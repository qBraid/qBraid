"""
==================================================================
 Qiskit Transpiler2  (:mod:`qbraid.transpiler2.interface.qiskit`)
==================================================================

.. currentmodule:: qbraid.transpiler2.interface.qiskit

Wrapping Strategy
------------------

Qiskit's circuit layer stores abstract parameters globally, making them easily retreivable.
The qBraid transpiler does the same.

The notion of an instruction object (a gate applied to specific qubits) does not exist in qiskit.
Rather, this concept is stored in `QuantumCircuit.data` as a tuple (gate,qubits,clbits). To add
some confusion, and `Instruction` object refers not to the above concept but rather to an abstract
class which is extended by ``QuantumGate``.

Output Strategy
---------------

Because qubits and parameters are stored as global attributes of the CircuitWrapper class, these
output mappings must be passed as arguments of the transpile functions for lower-level objects:
moments,circuits, and gates.

.. autosummary::
   :toctree: ../stubs/

    QiskitCircuitWrapper
    from_qasm
    from_qiskit
    to_qasm
    to_qiskit

"""
from qbraid.transpiler2.interface.qiskit.conversions import (
    from_qasm,
    from_qiskit,
    to_qasm,
    to_qiskit,
)

from .circuit_wrapper import QiskitCircuitWrapper
