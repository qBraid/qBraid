# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for converting generic quantum circuits to basis gate set compatible with IonQ devices.

"""
from typing import Union

import pytket
import pytket.extensions.braket
from braket.circuits import Circuit

try:
    from pytket.circuit_library import _TK1_to_RzRx  # type: ignore
except (ModuleNotFoundError, ImportError):
    # pytket <= 1.18
    from pytket._tket.circuit._library import _TK1_to_RzRx  # type: ignore

from pytket.passes import RebaseCustom
from pytket.predicates import (
    CompilationUnit,
    GateSetPredicate,
    MaxNQubitsPredicate,
    NoClassicalControlPredicate,
    NoFastFeedforwardPredicate,
    NoMidMeasurePredicate,
    NoSymbolsPredicate,
)

from qbraid.compiler.exceptions import CompilerError

HARMONY_MAX_QUBITS = 11

ionq_gates = {
    pytket.circuit.OpType.X,
    pytket.circuit.OpType.Y,
    pytket.circuit.OpType.Z,
    pytket.circuit.OpType.Rx,
    pytket.circuit.OpType.Ry,
    pytket.circuit.OpType.Rz,
    pytket.circuit.OpType.H,
    pytket.circuit.OpType.S,
    pytket.circuit.OpType.Sdg,
    pytket.circuit.OpType.T,
    pytket.circuit.OpType.Tdg,
    pytket.circuit.OpType.V,
    pytket.circuit.OpType.Vdg,
    pytket.circuit.OpType.Measure,
    pytket.circuit.OpType.noop,
    pytket.circuit.OpType.SWAP,
    pytket.circuit.OpType.CX,
    pytket.circuit.OpType.ZZPhase,
    pytket.circuit.OpType.XXPhase,
    pytket.circuit.OpType.YYPhase,
    pytket.circuit.OpType.ZZMax,
    pytket.circuit.OpType.Barrier,
}

preds = [
    NoClassicalControlPredicate(),
    NoFastFeedforwardPredicate(),
    NoMidMeasurePredicate(),
    NoSymbolsPredicate(),
    GateSetPredicate(ionq_gates),
    MaxNQubitsPredicate(HARMONY_MAX_QUBITS),
]

ionq_rebase_pass = RebaseCustom(
    ionq_gates,
    pytket.Circuit(),  # cx_replacement (irrelevant)
    _TK1_to_RzRx,
)  # tk1_replacement


def braket_ionq_compile(circuit: Union[Circuit, pytket.circuit.Circuit]) -> Circuit:
    """
    Compiles a Braket circuit to a Braket circuit that can run on IonQ Harmony.

    Args:
        circuit (Union[braket.circuits.Circuit, pytket.circuit.Circuit]):
            The input Braket or PyTKET circuit to be compiled.

    Returns:
        braket.circuits.Circuit: The compiled Braket circuit that can run on IonQ Harmony.

    Notes:
        - If the input circuit is a braket Circuit, the function
          transpiles it to a ``pytket.circuit.Circuit`` before compilation.
        - The circuit is transpiled using qBraid's transpiler, if it contains
          any of the following gates::

                CPhaseShift00
                CPhaseShift01
                CPhaseShift10
                CV
                ECR
                GPi
                GPi2
                MS
                PSwap
                Unitary

        - Otherwise, the circuit is transpiled using ``pytket-braket``'s ``braket_to_tk``.

    """
    if isinstance(circuit, Circuit):
        try:
            tk_circuit = pytket.extensions.braket.braket_convert.braket_to_tk(circuit)
        except NotImplementedError:
            from qbraid import circuit_wrapper  # pylint: disable=import-outside-toplevel

            tk_circuit = circuit_wrapper(circuit).transpile("pytket")
    else:
        tk_circuit = circuit

    cu = CompilationUnit(tk_circuit, preds)
    ionq_rebase_pass.apply(cu)
    if not cu.check_all_predicates():
        raise CompilerError("Circuit cannot be compiled to IonQ Harmony.")
    compiled, _, _ = pytket.extensions.braket.braket_convert.tk_to_braket(cu.circuit)
    return compiled
