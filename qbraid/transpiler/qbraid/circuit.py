"""QbraidCircuitWrapper Class"""

from qbraid.circuits.circuit import Circuit

from qbraid.transpiler.circuit import CircuitWrapper
from qbraid.transpiler.parameter import ParamID
from qbraid.transpiler.qbraid.moment import QbraidMomentWrapper


class QbraidCircuitWrapper(CircuitWrapper):
    """Wrapper class for qBraid ``Circuit`` objects."""

    def __init__(self, circuit: Circuit, input_qubit_mapping=None, input_param_mapping=None):
        """Create a QbraidCircuitWrapper

        Args:
            circuit: the qbraid ``Circuit`` object to be wrapped
            input_qubit_mapping (optional, dict): the input qubit mapping
            input_param_mapping (optional, dict): the input parameter mapping

        """

        super().__init__(circuit, input_qubit_mapping)

        self._package = "qbraid"

        self._qubits = list(range(circuit.num_qubits))
        self._params = circuit.params

        if not input_param_mapping:
            self._input_param_mapping = {
                p: ParamID(i, p.name) for i, p in enumerate(circuit.params)
            }

        self._params = self._input_param_mapping.values()

        self._wrap_circuit()

    def _wrap_circuit(self):
        """Internal circuit wrapper initialization helper function."""
        self._moments = []

        for moment in self._circuit.moments:

            next_moment = QbraidMomentWrapper(moment)
            self._moments.append(next_moment)

            for instruction in next_moment.instructions:
                instruction.gate.parse_params(self.input_param_mapping)

    @property
    def instructions(self):
        """Return list of the circuit's instructions."""
        instructions = []
        for m in self.moments:
            instructions += m.instructions
        return instructions

    @property
    def moments(self):
        """Return list of the circuit's moments."""
        return self._moments

    @property
    def num_qubits(self):
        """Return the number of qubits in the circuit."""
        return len(self.qubits)
