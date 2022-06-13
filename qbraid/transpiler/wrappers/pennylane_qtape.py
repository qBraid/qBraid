"""
Module defining PennylaneQTapeWrapper Class

"""
from pennylane.tape import QuantumTape

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class PennylaneQTapeWrapper(QuantumProgramWrapper):
    """Wrapper class for Pennylane ``QuantumTape`` objects."""

    def __init__(self, tape: QuantumTape):
        """Create a PennylaneQTapeWrapper

        Args:
            tape: the quantum tape object to be wrapped

        """
        super().__init__(tape)

        self._qubits = tape.wires
        self._num_qubits = len(self.qubits)
        self._depth = tape.graph.get_depth()
        self._package = "pennylane"
        self._program_type = "QuantumTape"
