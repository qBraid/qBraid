# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=invalid-name

"""
Module defining IonQ device class

"""
import json
import re
from typing import TYPE_CHECKING

import openqasm3

from qbraid.passes.qasm3.compat import convert_qasm_pi_to_decimal
from qbraid.programs import load_program
from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import IonQJob

if TYPE_CHECKING:
    import qbraid.runtime
    import qbraid.runtime.ionq.provider


class IonQDevice(QuantumDevice):
    """IonQ quantum device interface."""

    def __init__(
        self,
        profile: "qbraid.runtime.TargetProfile",
        session: "qbraid.runtime.ionq.provider.IonQSession",
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> "qbraid.runtime.ionq.provider.IonQSession":
        """Return the IonQ session."""
        return self._session

    def status(self) -> "qbraid.runtime.DeviceStatus":
        """Return the current status of the IonQ device."""
        device_data = self.session.get_device(self.id)
        status = device_data.get("status")

        if status in ["available", "running"]:
            return DeviceStatus.ONLINE

        if status in ["unavailable", "reserved", "calibrating"]:
            return DeviceStatus.UNAVAILABLE

        if status == "offline":
            return DeviceStatus.OFFLINE

        raise ValueError(f"Unrecognized device status: {status}")

    @staticmethod
    def extract_gate_data(program: "openqasm3.ast.Program") -> list[dict]:
        """Extract gate data from the input program."""
        gates = []

        for statement in program.statements:
            if isinstance(statement, openqasm3.ast.QuantumGate):
                name = statement.name.name
                qubits = statement.qubits
                qubit_values = []

                for qubit in qubits:
                    _ = qubit.name.name
                    indices = qubit.indices
                    for index in indices:
                        qubit_values.extend(literal.value for literal in index)

                # support gates defined in `stdgates.inc` from OpenQASM 3
                if len(qubit_values) == 1:
                    # IonQ supported gates:
                    if name in ["x", "not", "y", "z", "h", "s", "si", "t", "ti", "v", "vi"]:
                        gate_data = {"gate": name, "target": qubit_values[0]}
                    elif name in ["rx", "ry", "rz"]:
                        # convert "rz(3 * pi / 4) q[0];" to "3 * pi / 4"
                        angle_str = re.findall(r"\((.+)\)", openqasm3.dumps(statement))[0]
                        gate_data = {
                            "gate": name,
                            "target": qubit_values[0],
                            "rotation": float(convert_qasm_pi_to_decimal(angle_str)),
                        }
                    # OpenQASM 3 aliases:
                    elif name == "sdg":
                        gate_data = {"gate": "si", "target": qubit_values[0]}
                    elif name == "tdg":
                        gate_data = {"gate": "ti", "target": qubit_values[0]}
                    elif name == "sx":
                        gate_data = {"gate": "v", "target": qubit_values[0]}
                    elif name == "sxdg":
                        gate_data = {"gate": "vi", "target": qubit_values[0]}
                    else:
                        raise NotImplementedError(f"'{name}' gate not yet supported")
                elif len(qubit_values) == 2:
                    if name in ["cnot", "cx", "CX"]:
                        gate_data = {
                            "gate": "cnot",
                            "control": qubit_values[0],
                            "target": qubit_values[1],
                        }
                    elif name == "swap":
                        gate_data = {
                            "gate": "swap",
                            "targets": qubit_values,
                        }
                    else:
                        raise NotImplementedError(f"'{name}' gate not yet supported")
                elif len(qubit_values) == 3:
                    if name in ["ccx", "toffoli"]:
                        gate_data = {
                            "gate": "cnot",
                            "controls": qubit_values[:2],
                            "target": qubit_values[2],
                        }
                else:
                    raise NotImplementedError(f"'{name}' gate not yet supported")

                gates.append(gate_data)

        return gates

    def transform(self, run_input: "openqasm3.ast.Program") -> dict:
        """Transform the input to the IonQ device."""
        program = load_program(run_input)
        program.transform(device=self)
        num_qubits = program.num_qubits
        gate_data = self.extract_gate_data(program.parsed())
        return {"qubits": num_qubits, "circuit": gate_data}

    def submit(self, run_input: list[dict], *args, shots: int = 100, **kwargs) -> IonQJob:
        """Submit a job to the IonQ device."""
        is_single_input = not isinstance(run_input, list)
        run_input = [run_input] if is_single_input else run_input
        jobs = []
        for input_data in run_input:
            data = {
                "target": self.id,
                "shots": shots,
                "input": input_data,
                **kwargs,
            }
            serialized_data = json.dumps(data)
            job_data = self.session.create_job(serialized_data)
            job_id = job_data.get("id")
            if not job_id:
                raise ValueError("Job ID not found in the response")
            qbraid_job = IonQJob(job_id=job_id, session=self.session, device=self, shots=shots)
            jobs.append(qbraid_job)
        return jobs[0] if is_single_input else jobs
