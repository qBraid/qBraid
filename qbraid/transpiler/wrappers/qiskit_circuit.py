"""QiskitCircuitWrapper Class"""

from cirq import Circuit

# Currently not used because support parameterized circuits
from qbraid.transpiler.parameter import ParamID
from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class QiskitCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Qiskit ``Circuit`` objects"""

    def __init__(self, circuit: Circuit):
        """Create a QiskitCircuitWrapper

        Args
            circuit: the qiskit ``Circuit`` object to be wrapped
        """
        super().__init__(circuit)

        self._qubits = circuit.qubits
        self._params = circuit.parameters
        self._num_qubits = circuit.num_qubits
        self._num_clbits = circuit.num_clbits
        self._depth = circuit.depth()
        self._input_param_mapping = {p: ParamID(i, p.name) for i, p in enumerate(self.params)}
        self._package = "qiskit"
        self._program_type = "QuantumCircuit"
