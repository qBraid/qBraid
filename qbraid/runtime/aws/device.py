# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module defining BraketDeviceWrapper Class

"""

from __future__ import annotations

import datetime
import warnings
from typing import TYPE_CHECKING

import pyqasm
from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
from braket.aws import AwsDevice
from braket.circuits import Circuit
from braket.circuits.measure import Measure
from braket.experimental_capabilities.experimental_capability_context import (
    EXPERIMENTAL_CAPABILITIES_ALL,
)
from braket.ir.openqasm import Program as OpenQasmProgram

from qbraid._logging import logger
from qbraid.passes.qasm import branches_on_measurement, contains_feedforward
from qbraid.programs import (
    NATIVE_REGISTRY,
    QPROGRAM_REGISTRY,
    ExperimentType,
    get_program_type_alias,
    load_program,
)
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import DeviceProgramTypeMismatchError, ProgramValidationError
from qbraid.runtime.options import RuntimeOptions
from qbraid.transpiler import transpile
from qbraid.transpiler.conversions.qasm3.qasm3_to_braket import transform_notation

from .availability import next_available_time
from .job import BraketQuantumTask

if TYPE_CHECKING:
    import braket.aws

    import qbraid.runtime


def _enable_experimental_capabilities(kwargs: dict) -> bool:
    """Normalize ``experimental_capabilities`` in ``kwargs``; return whether it is enabled.

    The Braket SDK accepts only ``"ALL"`` and raises on ``"NONE"``, the API's other value,
    so ``"NONE"`` and falsy values are dropped. Anything else raises before submission.
    """
    value = kwargs.pop("experimental_capabilities", None)
    if value == EXPERIMENTAL_CAPABILITIES_ALL:
        kwargs["experimental_capabilities"] = value
        return True
    if value and value != "NONE":
        raise ValueError(
            f"Invalid experimental_capabilities {value!r}: use 'ALL' to enable "
            "experimental capabilities, or 'NONE' to disable them."
        )
    return False


def _as_braket_openqasm(program: str) -> str:
    """Return ``program`` in Braket's gate names if it includes ``stdgates.inc``.

    Braket rejects ``include`` and names some standard gates differently (``cnot`` for
    ``cx``). Programs without the include are returned unchanged, because the rewrite
    reformats the source (``#pragma`` becomes ``pragma``).
    """
    if 'include "stdgates.inc";' not in program:
        return program
    return transform_notation(program)


class BraketDevice(QuantumDevice):
    """Wrapper class for Amazon Braket ``Device`` objects.

    Configure default quantum task tags with ``device.set_options(tags={"project": "example"})``.
    Tags passed to ``run`` or ``submit`` override matching default keys. Clear the defaults
    with ``device.set_options(tags=None)``.
    """

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: braket.aws.AwsSession | None = None,
    ):
        """Create a BraketDevice."""
        options = RuntimeOptions(tags=None)
        options.set_validator(
            "tags",
            lambda tags: tags is None
            or (
                isinstance(tags, dict)
                and all(
                    isinstance(key, str) and isinstance(value, str) for key, value in tags.items()
                )
            ),
        )
        super().__init__(profile=profile, options=options)
        self._device = AwsDevice(arn=self.id, aws_session=session)
        self._provider_name = self.profile.get("provider_name")

    def set_options(self, **fields):
        """Update runtime options, storing ``tags`` as a copy of the caller's dict."""
        if isinstance(fields.get("tags"), dict):
            fields["tags"] = dict(fields["tags"])
        super().set_options(**fields)

    @property
    def name(self) -> str:
        """Return the name of this Device."""
        return self._device.name

    def __str__(self):
        """String representation of the BraketDevice object."""
        return f"{self.__class__.__name__}('{self._provider_name} {self.name}')"

    def status(self) -> qbraid.runtime.DeviceStatus:
        """Return the status of this Device."""
        if self._device.status == "ONLINE":
            # Braket reports a device ONLINE even when its capabilities fail schema
            # validation, and then ``is_available`` raises on the unset properties.
            if self._device.properties is None:
                warnings.warn(
                    f"Device '{self.id}' is ONLINE but its capabilities could not be parsed, "
                    "so its availability is unknown. Reporting it as unavailable; upgrading "
                    "amazon-braket-schemas may resolve this.",
                    UserWarning,
                )
                return DeviceStatus.UNAVAILABLE
            if self._device.is_available:
                return DeviceStatus.ONLINE
            return DeviceStatus.UNAVAILABLE

        if self._device.status == "RETIRED":
            return DeviceStatus.RETIRED

        return DeviceStatus.OFFLINE

    def availability_window(self) -> tuple[bool, str, datetime.datetime | None]:
        """Provides device availability status. Indicates current availability,
        time remaining (hours, minutes, seconds) until next availability or
        unavailability, and future UTC datetime of next change in availability status.

        Returns:
            tuple[bool, str, Optional[str]]: Current device availability, hr/min/sec until
                availability switch, future UTC datetime of availability switch
        """
        return next_available_time(self._device)

    def queue_depth(self) -> int:
        """Return the number of jobs in the queue for the device."""
        queue_depth_info = self._device.queue_depth()
        total_queued = 0
        for queue_type in ["Normal", "Priority"]:
            num_queued = queue_depth_info.quantum_tasks[queue_type]
            if isinstance(num_queued, str) and num_queued.startswith(">"):
                num_queued = num_queued[1:]
            total_queued += int(num_queued)
        return total_queued

    def transpile(
        self,
        run_input: qbraid.programs.QPROGRAM,
        run_input_spec: qbraid.programs.ProgramSpec,
    ) -> qbraid.programs.QPROGRAM:
        """Reject OpenQASM feed-forward the device doesn't list, then transpile.

        Only checked when the profile carries ``supported_operations``; without them the
        device's support for ``if`` is unknown and the program is passed through.

        Raises:
            ProgramValidationError: If the program branches on a measurement result and
                ``if`` is not among the device's supported operations.
        """
        supported_operations = self.profile.get("supported_operations")
        if (
            run_input_spec.alias in {"qasm2", "qasm3"}
            and supported_operations is not None
            and "if" not in {operation.lower() for operation in supported_operations}
        ):
            try:
                module = pyqasm.loads(run_input)
            except Exception:  # pylint: disable=broad-exception-caught
                module = None  # leave parse errors to the conversion step
            # Unrolling is slow on large programs, so only unroll one that has a branch.
            if module is not None and contains_feedforward(module.original_program):
                try:
                    module.unroll()
                    # unrolling keeps any ``if`` on a bit, so check what it reads
                    feedforward = branches_on_measurement(module.unrolled_ast)
                except Exception:  # pylint: disable=broad-exception-caught
                    feedforward = branches_on_measurement(module.original_program)
            else:
                feedforward = False
            if feedforward:
                raise ProgramValidationError(
                    f"Device '{self.id}' does not support classical feed-forward ('if' on "
                    "measurement results). Remove the conditional, or submit it as "
                    "OpenQASM 3 to a device that runs it, such as IQM Emerald or Garnet, "
                    'with experimental_capabilities="ALL".'
                )
        return super().transpile(run_input, run_input_spec)

    def transform(
        self, run_input: Circuit | AnalogHamiltonianSimulation
    ) -> Circuit | AnalogHamiltonianSimulation:
        """Transpile a circuit for the device."""
        program = run_input

        provider = (self.profile.provider_name or "").upper()
        experiment_type = self.profile.experiment_type

        if experiment_type == ExperimentType.GATE_MODEL and not isinstance(program, Circuit):
            raise DeviceProgramTypeMismatchError(program, str(Circuit), experiment_type)

        if experiment_type == ExperimentType.ANALOG and not isinstance(
            program, AnalogHamiltonianSimulation
        ):
            raise DeviceProgramTypeMismatchError(
                program, str(AnalogHamiltonianSimulation), experiment_type
            )

        # Use Tket to transform circuits for IonQ to support a bigger gateset. The transformation
        # only applies when no measurement is presented and the circuit only use contiguous qubits.
        has_contiguous_qubits = False
        includes_measurement = False
        if isinstance(run_input, Circuit):
            includes_measurement = any(
                isinstance(instruction.operator, Measure) for instruction in run_input.instructions
            )
            has_contiguous_qubits = max(run_input.qubits) + 1 == run_input.qubit_count
        if (
            provider == "IONQ"
            and isinstance(run_input, Circuit)
            and not includes_measurement
            and has_contiguous_qubits
        ):
            graph = self.scheme.conversion_graph
            if (
                graph is not None
                and graph.has_edge("pytket", "braket")
                and QPROGRAM_REGISTRY["pytket"] == NATIVE_REGISTRY["pytket"]
                and QPROGRAM_REGISTRY["braket"] == NATIVE_REGISTRY["braket"]
                and self._target_spec.alias == "braket"
            ):
                tk_circuit = transpile(program, "pytket", max_path_depth=1, conversion_graph=graph)
                tk_program = load_program(tk_circuit)
                tk_program.transform(self)
                tk_transformed = tk_program.program
                braket_transformed = transpile(
                    tk_transformed, "braket", max_path_depth=1, conversion_graph=graph
                )
                program = braket_transformed
            else:
                logger.info(
                    "Skipping the IonQ gateset transform: the pytket <-> braket conversion "
                    "edges are unavailable. Install 'pytket-braket' to enable rebasing of "
                    "gates IonQ devices on Braket do not accept natively."
                )

        qprogram = load_program(program)
        qprogram.transform(self)
        program = qprogram.program

        return program

    def run(
        self,
        run_input: qbraid.programs.QPROGRAM | list[qbraid.programs.QPROGRAM],
        *args,
        **kwargs,
    ) -> BraketQuantumTask | list[BraketQuantumTask]:
        """Run a quantum job or a list of quantum jobs on this quantum device.

        With ``experimental_capabilities="ALL"``, OpenQASM 3 programs are submitted as written,
        without conversion or validation, except that a program including ``stdgates.inc``
        (as Qiskit's exporter writes) has the include removed and its gates renamed to
        Braket's. Experimental instructions such as IQM's ``measure_ff`` and ``cc_prx`` can
        only be converted inside Braket's process-wide ``EnableExperimentalCapability``
        context, which concurrent submissions would share.
        """
        programs = run_input if isinstance(run_input, list) else [run_input]
        if _enable_experimental_capabilities(kwargs) and all(
            get_program_type_alias(program, safe=True) == "qasm3" for program in programs
        ):
            openqasm = [OpenQasmProgram(source=_as_braket_openqasm(p)) for p in programs]
            return self.submit(
                openqasm if isinstance(run_input, list) else openqasm[0], *args, **kwargs
            )
        return super().run(run_input, *args, **kwargs)

    def submit(
        self,
        run_input: (
            Circuit
            | AnalogHamiltonianSimulation
            | OpenQasmProgram
            | list[Circuit]
            | list[AnalogHamiltonianSimulation]
            | list[OpenQasmProgram]
        ),
        *args,
        tags: dict[str, str] | None = None,
        **kwargs,
    ) -> BraketQuantumTask | list[BraketQuantumTask]:
        """Run a quantum task specification on this quantum device. Task must represent a
        quantum circuit, annealing problems not supported.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            tags (dict[str, str]): Tags to associate with the job, merged with defaults
                configured via ``set_options(tags=...)``. Per-submission values take
                precedence. Passing ``None`` or an empty dictionary uses the defaults.
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        _enable_experimental_capabilities(kwargs)
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input

        default_tags = self._options["tags"]
        if default_tags is not None:
            tags = {**default_tags, **(tags or {})}

        if any(hasattr(circuit, "partial_measurement_qubits") for circuit in run_input):
            # Extract partial measurement qubit information and add as tags for job tracking
            tasks = []
            tags = tags or {}
            for circuit in run_input:
                current_tags = tags.copy()
                if hasattr(circuit, "partial_measurement_qubits"):
                    partial_measurement_qubits: list[int] = circuit.partial_measurement_qubits
                    # Convert qubit indices to a string format for tagging (e.g., "0/2/3")
                    tag_value = "/".join([str(x) for x in partial_measurement_qubits])
                    current_tags["partial_measurement_qubits"] = tag_value
                task = self._device.run(circuit, *args, tags=current_tags, **kwargs)
                tasks.append(BraketQuantumTask(task.id, task=task, device=self._device))
        else:
            aws_quantum_task_batch = self._device.run_batch(run_input, *args, tags=tags, **kwargs)
            tasks = [
                BraketQuantumTask(task.id, task=task, device=self._device)
                for task in aws_quantum_task_batch.tasks
            ]

        if is_single_input:
            return tasks[0]
        return tasks
