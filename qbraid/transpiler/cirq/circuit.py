"""CirqCircuitWrapper Class"""

from typing import Iterable, List

from cirq.circuits import Circuit
from cirq.ops.moment import Moment

from qbraid.transpiler.circuit import CircuitWrapper
from qbraid.transpiler.cirq.instruction import CirqInstructionWrapper
from qbraid.transpiler.cirq.moment import CirqMomentWrapper
from qbraid.transpiler.parameter import ParamID


class CirqCircuitWrapper(CircuitWrapper):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, circuit: Circuit, input_qubit_mapping=None):
        """Create a CirqCircuitWrapper

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped
            input_qubit_mapping (optinal, dict): input qubit mapping

        """
        super().__init__(circuit, input_qubit_mapping)

        self._qubits = circuit.all_qubits()
        self._num_qubits = len(self.qubits)
        self._package = "cirq"

        self._wrap_circuit(circuit)

    def _wrap_circuit(self, circuit: Iterable[Moment]):
        """Internal circuit wrapper initialization helper function."""
        params = set()
        moments = []

        for moment in circuit.moments:

            instructions = []

            for op in moment.operations:
                qbs = [self.input_qubit_mapping[qubit] for qubit in op.qubits]
                next_instruction = CirqInstructionWrapper(op, qbs)
                params.union(set(next_instruction.gate.get_abstract_params()))
                instructions.append(next_instruction)

            next_moment = CirqMomentWrapper(moment, instructions=instructions)
            moments.append(next_moment)

        self._params = params
        self._input_param_mapping = {
            param: ParamID(index, param.name) for index, param in enumerate(self.params)
        }

        for moment in moments:
            for instruction in moment.instructions:
                instruction.gate.parse_params(self.input_param_mapping)

        self._moments = moments

    @property
    def moments(self) -> List[CirqMomentWrapper]:
        """Return list of the circuit's moments."""
        return self._moments

    @property
    def instructions(self) -> List[CirqInstructionWrapper]:
        """Return list of the circuit's instructions."""
        instructions = []
        for m in self.moments:
            for i in m.instructions:
                instructions.append(i)

        return instructions
