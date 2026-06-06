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
Module containing myQLM extras-based conversion functions.

These conversions use the myQLM interoperability layer (``myqlm-interop``).
The qiskit and cirq binders additionally require those frameworks to be installed.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import requires_extras

qat_openqasm = LazyLoader("qat_openqasm", globals(), "qat.interop.openqasm")
qat_qiskit = LazyLoader("qat_qiskit", globals(), "qat.interop.qiskit")
qat_cirq = LazyLoader("qat_cirq", globals(), "qat.interop.cirq")

if TYPE_CHECKING:
    import cirq
    import qiskit.circuit
    from qat.core.wrappers.circuit import Circuit as MyQLMCircuit

    from qbraid.programs.typer import Qasm2StringType


@requires_extras("myqlm-interop")
def qasm2_to_myqlm(qasm: Qasm2StringType) -> MyQLMCircuit:
    """Returns a myQLM Circuit equivalent to the input OpenQASM 2 circuit.

    Args:
        qasm: OpenQASM 2 string to convert.

    Returns:
        qat.core.wrappers.circuit.Circuit equivalent to the input OpenQASM 2 string.
    """
    parser = qat_openqasm.OqasmParser()
    return parser.compile(qasm)


@requires_extras("myqlm-interop")
def qiskit_to_myqlm(circuit: qiskit.circuit.QuantumCircuit) -> MyQLMCircuit:
    """Returns a myQLM Circuit equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit QuantumCircuit to convert.

    Returns:
        qat.core.wrappers.circuit.Circuit equivalent to the input Qiskit circuit.
    """
    return qat_qiskit.qiskit_to_qlm(circuit)


@requires_extras("myqlm-interop")
def myqlm_to_qiskit(circuit: MyQLMCircuit) -> qiskit.circuit.QuantumCircuit:
    """Returns a Qiskit QuantumCircuit equivalent to the input myQLM circuit.

    Args:
        circuit: myQLM Circuit to convert.

    Returns:
        qiskit.circuit.QuantumCircuit equivalent to the input myQLM circuit.
    """
    return qat_qiskit.qlm_to_qiskit(circuit)


@requires_extras("myqlm-interop")
def cirq_to_myqlm(circuit: cirq.Circuit) -> MyQLMCircuit:
    """Returns a myQLM Circuit equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq Circuit to convert.

    Returns:
        qat.core.wrappers.circuit.Circuit equivalent to the input Cirq circuit.
    """
    return qat_cirq.cirq_to_qlm(circuit)
