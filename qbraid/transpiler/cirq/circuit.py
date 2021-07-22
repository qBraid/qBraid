from cirq.circuits import Circuit

from qbraid.transpiler.parameter import ParamID
from qbraid.transpiler.circuit import CircuitWrapper
from .gate import CirqGateWrapper


class CirqCircuitWrapper(CircuitWrapper):
    def __init__(self, circuit: Circuit, input_qubit_mapping=None):

        super().__init__()

        self.circuit = circuit
        self.qubits = circuit.all_qubits()
        self.input_qubit_mapping = (
            {qubit: index for index, qubit in enumerate(self.qubits)}
            if input_qubit_mapping is None
            else input_qubit_mapping
        )

        self.params = set()

        for instruction in circuit.all_operations():
            qubits = [self.input_qubit_mapping[qubit] for qubit in instruction.qubits]
            gate = CirqGateWrapper(instruction.gate)
            params = [p for p in gate.params if isinstance(p, ParamID)]

            next_instruction = {
                "instruction": instruction,
                "qubits": qubits,
                "params": params,
                "gate": gate,
            }

            self.params.union(set(gate.get_abstract_params()))
            self.instructions.append(next_instruction)

        self.input_param_mapping = {param: index for index, param in enumerate(self.params)}

        for next_instruction in self.instructions:
            next_instruction["gate"].parse_params(self.input_param_mapping)

        self._package = "cirq"

    @property
    def num_qubits(self):
        return len(self.qubits)
