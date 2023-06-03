import pytket
from pytket.predicates import CompilationUnit, NoClassicalControlPredicate, NoFastFeedforwardPredicate, NoMidMeasurePredicate, NoSymbolsPredicate, GateSetPredicate, MaxNQubitsPredicate
from pytket.passes import RebaseCustom 
from pytket._tket.circuit._library import _TK1_to_RzRx  # type: ignore

import pytket.extensions.braket


HARMONY_MAX_QUBITS = 11

ionq_multiqs = {
    pytket.circuit.OpType.SWAP,
    pytket.circuit.OpType.CX,
    pytket.circuit.OpType.ZZPhase,
    pytket.circuit.OpType.XXPhase,
    pytket.circuit.OpType.YYPhase,
    pytket.circuit.OpType.ZZMax,
    pytket.circuit.OpType.Barrier,
}
ionq_singleqs = {
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
}

ionq_gates = ionq_multiqs.union(ionq_singleqs)

preds = [
            NoClassicalControlPredicate(),
            NoFastFeedforwardPredicate(),
            NoMidMeasurePredicate(),
            NoSymbolsPredicate(),
            GateSetPredicate(ionq_gates),
            MaxNQubitsPredicate(HARMONY_MAX_QUBITS),
        ]

ionq_rebase_pass = RebaseCustom(
    ionq_multiqs | ionq_singleqs,
    pytket.Circuit(),  # cx_replacement (irrelevant)
    _TK1_to_RzRx,
)  # tk1_replacement

def braket_ionq_compilation(circuit):
    tk_circuit: pytket.Circuit = pytket.extensions.braket.braket_convert.braket_to_tk(circuit)
    cu = CompilationUnit(tk_circuit, preds)
    ionq_rebase_pass.apply(cu)
    assert cu.check_all_predicates()
    return pytket.extensions.braket.braket_convert.tk_to_braket(cu.circuit)