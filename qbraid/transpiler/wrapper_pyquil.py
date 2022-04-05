"""PyQuilProgramWrapper Class"""

from pyquil import Program

from qbraid.transpiler.wrapper_abc import QuantumProgramWrapper


class PyQuilProgramWrapper(QuantumProgramWrapper):
    """Wrapper class for pyQuil ``Program`` objects."""

    def __init__(self, program: Program):
        """Create a PyQuilProgramWrapper

        Args:
            program: the program object to be wrapped

        """
        super().__init__(program)

        self._qubits = program.get_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(program)
        self._package = "pyquil"
        self._program_type = "Program"
