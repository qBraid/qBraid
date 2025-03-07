# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining IonQ device class

"""
from __future__ import annotations

import importlib.util
import json
import warnings
from typing import TYPE_CHECKING, Any, Literal, Optional, Union

import pyqasm
from qbraid_core._import import LazyLoader

from qbraid._logging import logger
from qbraid.passes import CompilationError
from qbraid.programs import QPROGRAM_REGISTRY, load_program
from qbraid.programs.gate_model.ionq import GateSet, InputFormat
from qbraid.programs.gate_model.qasm2 import OpenQasm2Program
from qbraid.programs.gate_model.qasm3 import OpenQasm3Program
from qbraid.programs.typer import IonQDict, IonQDictType, QasmStringType
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_ionq import (
    IONQ_ONE_QUBIT_GATE_MAP,
    IONQ_THREE_QUBIT_GATE_ALIASES,
    IONQ_TWO_QUBIT_GATE_MAP,
)

from .job import IonQJob

if TYPE_CHECKING:
    import qiskit as qiskit_typing

    import qbraid.runtime
    import qbraid.runtime.ionq.provider

qiskit = LazyLoader("qiskit", globals(), "qiskit")
qiskit_ionq = LazyLoader("qiskit_ionq", globals(), "qiskit_ionq")

IONQ_GATE_MAP = IONQ_ONE_QUBIT_GATE_MAP | IONQ_TWO_QUBIT_GATE_MAP | IONQ_THREE_QUBIT_GATE_ALIASES

DEFAULT_FORMAT = InputFormat.CIRCUIT.value
DEFAULT_GATESET = GateSet.QIS.value


class IonQDevice(QuantumDevice):
    """IonQ quantum device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.ionq.provider.IonQSession,
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.ionq.provider.IonQSession:
        """Return the IonQ session."""
        return self._session

    def __str__(self):
        """String representation of the IonQDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> qbraid.runtime.DeviceStatus:
        """Return the current status of the IonQ device."""
        device_data = self.session.get_device(self.id)
        status = device_data.get("status")

        if status in ["available", "running"]:
            return DeviceStatus.ONLINE

        if status in ["unavailable", "reserved", "calibrating"]:
            return DeviceStatus.UNAVAILABLE

        if status == "retired":
            return DeviceStatus.RETIRED

        if status == "offline":
            return DeviceStatus.OFFLINE

        raise ValueError(f"Unrecognized device status: {status}")

    def avg_queue_time(self) -> int:
        """Return the average queue time for the IonQ device."""
        device_data = self.session.get_device(self.id)
        return device_data["average_queue_time"]

    def transform(self, run_input: QasmStringType) -> QasmStringType:
        """Transform the input to the IonQ device."""
        program: OpenQasm2Program | OpenQasm3Program = load_program(run_input)

        try:
            program.transform(device=self, gate_mappings=IONQ_GATE_MAP)
        except CompilationError as err:
            logger.debug("Failed to transform OpenQASM program for IonQ: %s", err)
            logger.debug("Retrying using pyqasm.unroll()...")
            program._module.unroll()
            program._program = pyqasm.dumps(program._module)
            program.transform(device=self, gate_mappings=IONQ_GATE_MAP)

        return program.program

    @staticmethod
    def _squash_multicircuit_input(batch_input: list[IonQDictType]) -> dict[str, Any]:
        if not batch_input:
            raise ValueError("run_input list cannot be empty.")

        input_format = batch_input[0].get("format", DEFAULT_FORMAT)
        input_gateset = batch_input[0].get("gateset", DEFAULT_GATESET)
        max_qubits = 0
        circuits = []

        for i, run_input in enumerate(batch_input):
            if not isinstance(run_input, IonQDict):
                raise ValueError("All run_inputs must be an instance of ~IonQDict.")
            if run_input.get("format", DEFAULT_FORMAT) != input_format:
                raise ValueError("All run_inputs must have the same value for key 'format'.")
            if run_input.get("gateset", DEFAULT_FORMAT) != input_gateset:
                raise ValueError("All run_inputs must have the same value for key 'gateset'.")

            max_qubits = max(max_qubits, run_input["qubits"])
            circuits.append({"circuit": run_input["circuit"], "name": f"Circuit {i}"})

        return {
            "format": input_format,
            "gateset": input_gateset,
            "qubits": max_qubits,
            "circuits": circuits,
        }

    # pylint:disable-next=arguments-differ,too-many-arguments
    def submit(
        self,
        run_input: Union[IonQDictType, list[IonQDictType]],
        shots: int,
        preflight: bool = False,
        name: Optional[str] = None,
        noise: Optional[dict[str, Any]] = None,
        error_mitigation: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs,
    ) -> IonQJob:
        """Submit a job to the IonQ device."""
        ionq_input = (
            self._squash_multicircuit_input(run_input) if isinstance(run_input, list) else run_input
        )
        job_data = {
            "target": self.id,
            "shots": shots,
            "preflight": preflight,
            "input": ionq_input,
            **kwargs,
        }
        optional_fields = {
            "name": name,
            "noise": noise,
            "metadata": metadata,
            "error_mitigation": error_mitigation,
        }
        job_data.update({key: value for key, value in optional_fields.items() if value is not None})
        serialized_data = json.dumps(job_data)
        job_data = self.session.create_job(serialized_data)
        job_id = job_data.get("id")
        if not job_id:
            raise ValueError("Job ID not found in the response")
        return IonQJob(job_id=job_id, session=self.session, device=self, shots=shots)

    def _apply_qiskit_ionq_conversion(
        self,
        run_input: list[qiskit_typing.QuantumCircuit],
        gateset: Literal["qis", "native"] = "qis",
        ionq_compiler_synthesis: bool = False,
    ) -> list[IonQDictType]:
        # pylint: disable-next=import-outside-toplevel
        from qbraid.transpiler.conversions.qiskit import qiskit_to_ionq

        provider = qiskit_ionq.IonQProvider(token=self.session.api_key)
        backend = provider.get_backend(self.id, gateset=gateset)

        run_input_compat = []
        for program in run_input:
            transpiled_circuit = qiskit.transpile(program, backend=backend)
            ionq_dict = qiskit_to_ionq(
                transpiled_circuit, gateset=gateset, ionq_compiler_synthesis=ionq_compiler_synthesis
            )
            run_input_compat.append(ionq_dict)

        return run_input_compat

    def run(
        self,
        run_input: Union[qbraid.programs.QPROGRAM, list[qbraid.programs.QPROGRAM]],
        *args,
        gateset: Optional[GateSet] = None,
        ionq_compiler_synthesis: Optional[bool] = None,
        **kwargs,
    ) -> Union[qbraid.runtime.IonQJob, list[qbraid.runtime.IonQJob]]:
        """
        Run a quantum job or a list of quantum jobs on this IonQ device.

        Args:
            run_input: A single quantum program or a list of quantum programs to run on the device.
            gateset (GateSet, optional): The gate set to use for the qiskit-ionq transpile step.
                Only applicable if qiskit-ionq is installed and all run_inputs are of type
                qiskit.QuantumCircuit. Defaults to GateSet.QIS.
            ionq_compiler_synthesis (bool, optional): Whether to opt-in to IonQ compiler's
                intelligent trotterization. Only applicable if qiskit-ionq is installed and all
                run_inputs are of type qiskit.QuantumCircuit. Defaults to False.

        Returns:
            An IonQJob object or a list of IonQJob objects corresponding to the input.
        """
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input

        if (
            "qiskit" in QPROGRAM_REGISTRY
            and all(isinstance(program, QPROGRAM_REGISTRY["qiskit"]) for program in run_input)
            and importlib.util.find_spec("qiskit_ionq") is not None
        ):
            gateset = gateset or GateSet.QIS
            ionq_compiler_synthesis = ionq_compiler_synthesis or False
            run_input_compat = self._apply_qiskit_ionq_conversion(
                run_input, gateset=gateset.value, ionq_compiler_synthesis=ionq_compiler_synthesis
            )
        else:
            if gateset is not None:
                warnings.warn(
                    UserWarning(
                        "GateSet argument is only applicable when qiskit-ionq "
                        "is installed, and when all run_inputs are of type "
                        "qiskit.QuantumCircuit. Ignoring..."
                    )
                )
            if ionq_compiler_synthesis is not None:
                warnings.warn(
                    UserWarning(
                        "IonQ compiler synthesis option is only applicable when "
                        "qiskit-ionq is installed, and when all run_inputs are of "
                        "type qiskit.QuantumCircuit. Ignoring..."
                    )
                )
            run_input_compat = [self.apply_runtime_profile(program) for program in run_input]

        run_input_compat = run_input_compat[0] if is_single_input else run_input_compat
        return self.submit(run_input_compat, *args, **kwargs)
