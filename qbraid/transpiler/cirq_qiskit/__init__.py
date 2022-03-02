"""
==================================================================
 Qiskit transpiler  (:mod:`qbraid.transpiler.cirq_qiskit`)
==================================================================

.. currentmodule:: qbraid.transpiler.cirq_qiskit

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

    from_qiskit
    to_qiskit

"""
from qbraid.transpiler.cirq_qiskit.conversions import from_qiskit, to_qiskit
