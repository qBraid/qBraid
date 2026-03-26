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
Module defining OriginQ device class.

"""
from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Optional

from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.profile import TargetProfile

from .job import OriginJob

if TYPE_CHECKING:
    from pyqpanda3.qcloud import QCloudBackend

logger = logging.getLogger(__name__)

SIMULATOR_BACKENDS: dict[str, int] = {
    "full_amplitude": 35,
    "partial_amplitude": 68,
    "single_amplitude": 200,
}


def _infer_num_qubits(backend: QCloudBackend, backend_name: str, *, simulator: bool) -> int | None:
    """Infer qubit count from chip info or simulator mapping."""
    if simulator:
        return SIMULATOR_BACKENDS.get(backend_name)
    try:
        chip_info = backend.chip_info()
        return chip_info.qubits_num()
    except Exception:
        logger.debug("Unable to determine qubit count from chip info", exc_info=True)
        return None


def _infer_basis_gates(backend: QCloudBackend, *, simulator: bool) -> list[str] | None:
    """Infer basis gates from chip info for hardware devices."""
    if simulator:
        return None
    try:
        chip_info = backend.chip_info()
        return chip_info.get_basic_gates()
    except Exception:
        logger.debug("Unable to determine basis gates from chip info", exc_info=True)
        return None


class OriginDevice(QuantumDevice):
    """OriginQ QCloud device interface."""

    def __init__(
        self,
        profile: TargetProfile,
        backend: QCloudBackend,
        backend_name: str,
        api_key: Optional[str] = None,
    ):
        super().__init__(profile=profile)
        self._backend = backend
        self._backend_name = backend_name
        self._api_key = api_key

    @staticmethod
    def build_profile(
        backend: QCloudBackend,
        device_id: str,
        backend_name: str,
    ) -> TargetProfile:
        """Build a TargetProfile from an OriginQ backend."""
        simulator = backend_name in SIMULATOR_BACKENDS
        return TargetProfile(
            device_id=device_id,
            simulator=simulator,
            experiment_type=ExperimentType.GATE_MODEL,
            num_qubits=_infer_num_qubits(backend, backend_name, simulator=simulator),
            program_spec=ProgramSpec(str, alias="qasm2"),
            basis_gates=_infer_basis_gates(backend, simulator=simulator),
            provider_name="origin",
        )

    @property
    def backend(self) -> Any:
        """Return the underlying QCloudBackend."""
        return self._backend

    @property
    def backend_name(self) -> str:
        """Return the OriginQ backend name."""
        return self._backend_name

    def status(self) -> DeviceStatus:
        """Return the current status of the OriginQ device."""
        # OriginQ does not expose health endpoints; assume online when instantiated.
        return DeviceStatus.ONLINE

    def _to_qprog(self, run_input):
        """Convert input to QProg format."""
        # Try Qiskit QuantumCircuit -> QASM string first
        try:
            # pylint: disable-next=import-outside-toplevel
            from qiskit import QuantumCircuit
            from qiskit.qasm2 import dumps as qasm2_dumps

            if isinstance(run_input, QuantumCircuit):
                run_input = qasm2_dumps(run_input)
        except ImportError:
            pass

        if isinstance(run_input, str):
            # pylint: disable-next=import-outside-toplevel
            from pyqpanda3.intermediate_compiler import convert_qasm_string_to_qprog

            return convert_qasm_string_to_qprog(run_input)

        raise TypeError(
            f"Unsupported input type {type(run_input)}; "
            "expected OpenQASM 2.0 string or qiskit.QuantumCircuit"
        )

    def transform(self, run_input):
        """Transform a single input to OriginQ's QProg format."""
        return self._to_qprog(run_input)

    def run(self, run_input, *args, **kwargs):
        """Run a quantum program or list of programs on this device."""
        is_single = not isinstance(run_input, Sequence) or isinstance(run_input, str)
        inputs = [run_input] if is_single else run_input
        jobs = [self.submit(self._to_qprog(item), *args, **kwargs) for item in inputs]
        return jobs[0] if is_single else jobs

    def submit(self, run_input, *, shots: int, **kwargs) -> OriginJob:
        """Submit a single quantum program to the OriginQ device."""
        qprog = self._to_qprog(run_input)
        nshots = int(shots)

        if self._backend_name in SIMULATOR_BACKENDS:
            backend_job = self._backend.run(qprog, nshots)
        else:
            # pylint: disable-next=import-outside-toplevel
            from pyqpanda3 import qcloud as qcloud_module

            options = qcloud_module.QCloudOptions()
            backend_job = self._backend.run(qprog, nshots, options)

        job_id = backend_job.job_id()
        return OriginJob(
            job_id=job_id,
            device=self,
            backend_job=backend_job,
            api_key=self._api_key,
        )
