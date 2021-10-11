# -*- coding: utf-8 -*-
# All rights reserved-2021©.
import pytest

from qiskit import QuantumCircuit as QiskitCircuit
from braket.circuits import Circuit as BraketCircuit
from cirq import Circuit as CirqCircuit

from qbraid import circuits
from qbraid.circuits import ParameterTable, drawer, update_rule, random_circuit
from qbraid.circuits.circuit import Circuit
from qbraid.circuits.exceptions import CircuitError
from qbraid.circuits.instruction import Instruction
from qbraid.circuits.moment import Moment
from qbraid.circuits.update_rule import UpdateRule


def get_qubit_idx_dict(dict: dict = None) -> None:
    # get index of qubits
    check_qubit = []
    for qubit_obj in dict["_qubits"]:
        check_qubit.append(qubit_obj._index)
    dict["_qubits"] = check_qubit


def circuit():
    return Circuit(num_qubits=3, name="test_circuit")


"""
INSTRUCTIONS
"""


class TestInstructions:
    @pytest.fixture()
    def gate(self):
        return circuits.H()

    @pytest.fixture()
    def instruction(self, gate):
        return Instruction(gate=gate, qubits=[0])

    def test_instruction_creation(self, instruction):
        """Test Instruction Object Creation."""
        assert [type(instruction), type(instruction.gate), type(instruction.qubits)] == [
            Instruction,
            circuits.H,
            list,
        ]

    def test_too_many_qubits(self, gate):
        """Test gate with too many qubits."""
        with pytest.raises(AttributeError):
            Instruction(gate=gate, qubits=[1, 2, 3])

    def test_too_few_qubits(self):
        """Test gate with too few qubits."""
        with pytest.raises(AttributeError):
            Instruction(gate=circuit.CH(), qubits=[1])

    def test_no_qubits(self):
        """Test gate with no qubits."""
        with pytest.raises(AttributeError):
            Instruction(gate=circuit.CH())

    def test_invalid_gate(self):
        """Test invalid gate."""
        with pytest.raises(AttributeError):
            Instruction(gate="SWAP", qubits=[1, 2])

    def test_control_gate(self):
        """Test Instruction Parameters."""
        print(Instruction(gate=circuits.CH(), qubits=[1, 2]))


"""
MOMENTS
"""


class TestMoments:
    @pytest.fixture()
    def gate(self):
        return circuits.H()

    @pytest.fixture()
    def instruction(self, gate):
        return Instruction(gate=gate, qubits=[0])

    @pytest.fixture()
    def two_same_instructions(self):
        return [
            Instruction(gate=circuits.CH(), qubits=[1, 2]),
            Instruction(gate=circuits.CH(), qubits=[1, 2]),
        ]

    @pytest.fixture()
    def two_diff_instructions(self):
        return [
            Instruction(gate=circuits.I(), qubits=[1]),
            Instruction(gate=circuits.RZX(theta=0), qubits=[3, 2]),
        ]

    @pytest.fixture()
    def moment(self, instruction):
        return Moment(instructions=instruction)

    def test_moment_w_instruction(self, moment):
        # check class parameter
        """Test moment with an instruction always should be a list."""
        assert type(moment.instructions) == list

    def test_not_instruction(self, moment):
        """Test moment with not instruction type appended."""
        with pytest.raises(TypeError):
            moment.append(5)

    def test_append_set(self, moment, two_diff_instructions):
        """Test moment with nested list, works since recursively unpacks instructions."""
        moment.append([{*two_diff_instructions}])
        assert len(moment.instructions) == 3

    def test_nested_list(self, moment):
        """Test moment with nested list, works since recursively unpacks instructions."""
        instruction1 = Instruction(gate=circuits.DCX(), qubits=[1, 2])
        moment.append([[instruction1]])
        assert len(moment.instructions) == 2

    def test_add_operators_on_same_qubit(self, moment, two_same_instructions):
        """Test adding two instructions acting onsame qubits."""
        with pytest.raises(CircuitError):
            moment.append(two_same_instructions)

    def test_same_qubit_at_a_time(self, moment, two_same_instructions):
        """Test adding two instructions acting on the same qubits."""
        with pytest.raises(CircuitError):
            for instruction in two_same_instructions:
                moment.append(instruction)

    def test_add_operators_on_diff_qubit(self, moment):
        """Test adding two instructions acting on diff qubits."""
        CH1 = Instruction(gate=circuits.CH(), qubits=[1, 2])
        CH2 = Instruction(gate=circuits.CH(), qubits=[3, 4])
        moment.append([CH1, CH2])
        assert len(moment.instructions) == 3


"""
CIRCUITS
"""


class TestCircuit:
    @pytest.fixture()
    def gate(self):
        return circuits.H()

    @pytest.fixture()
    def instruction(self, gate):
        return Instruction(gate=gate, qubits=[0])

    @pytest.fixture()
    def two_same_instructions(self):
        return [
            Instruction(gate=circuits.CH(), qubits=[1, 2]),
            Instruction(gate=circuits.CH(), qubits=[1, 2]),
        ]

    @pytest.fixture()
    def two_diff_instructions(self):
        return [
            Instruction(gate=circuits.I(), qubits=[1]),
            Instruction(gate=circuits.RZX(theta=0), qubits=[3, 2]),
        ]

    @pytest.fixture()
    def moment(self, instruction):
        return Moment(instructions=instruction)

    def test_circuit_str(self):
        """Test str result"""
        circuit = Circuit(num_qubits=3, name="test_circuit")
        assert circuit.__str__() == "Circuit(test_circuit, 3 qubits, 0 gates)"

    def test_add_circuit(self, gate):
        """Test adding circuit to another circuit."""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        circuit.append([h1, h2, h3])
        circuit2 = Circuit(num_qubits=3, name="circuit_2")
        circuit2.append([h1, h2, h3])
        circuit.append(circuit2)
        assert len(circuit.moments) == 2

    def test_add_empty_circuit_first(self, gate):
        """Test adding circuit to another circuit."""
        circuit = Circuit(num_qubits=3, name="test_circuit")
        circuit2 = Circuit(num_qubits=3, name="circuit_2")
        circuit.append(circuit2)
        # Nothing should be added to the circuit
        assert len(circuit.moments) == 0

    def test_add_filled_circuit_first(self, gate):
        """Test adding circuit to another circuit."""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        circuit2 = Circuit(num_qubits=3, name="circuit_2")
        circuit2.append([h1, h2, h3])
        circuit.append(circuit2)
        assert len(circuit.moments) == 1

    def test_add_small_circuit(self, gate):
        """Test adding a small circuit to another larger circuit."""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        circuit.append([h1, h3])
        circuit2 = Circuit(num_qubits=2, name="circuit_2")
        circuit2.append([h1, h2])
        circuit.append(circuit2)
        assert len(circuit.moments) == 2

    def test_add_larger_circuit(self, gate):
        """Test adding a larger circuit to another smaller circuit."""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        circuit.append([h1, h3])
        circuit2 = Circuit(num_qubits=2, name="circuit_2")
        circuit2.append([h1, h2])
        with pytest.raises(CircuitError):
            circuit2.append(circuit)

    def test_unrecognized_update_rule(self, gate):
        """Test fake update rule."""
        h1 = Instruction(gate, 0)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule="Not Updating")
        with pytest.raises(CircuitError):
            circuit.append(h1)

    def test_negative_circuit_qubit(self, gate):
        """Test circuit specified to negative number of qubits.
        Takes absolute value and returns circuit.
        """
        h3 = Instruction(gate, 1)
        circuit = Circuit(num_qubits=-3, name="test_circuit")
        circuit.append(h3)
        assert circuit.num_qubits == 3

    def test_negative_qubit(self, gate):
        """Test qubit specified to negative qubit."""
        h3 = Instruction(gate, -10)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        with pytest.raises(CircuitError):
            circuit.append(h3)

    def test_qubit_not_in_channel(self, gate):
        """Test qubit specified to too high of a qubit."""
        h3 = Instruction(gate, 4)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        with pytest.raises(CircuitError):
            circuit.append(h3)

    def test_far_qubit_not_in_channel(self, gate):
        """Test qubit specified to too high of a qubit."""
        h3 = Instruction(gate, 10)
        circuit = Circuit(num_qubits=3, name="test_circuit")
        with pytest.raises(CircuitError):
            circuit.append(h3)

    def test_inline_update_rule(self, gate):
        """Test inline update rule indivdually"""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.INLINE)
        circuit.append(h1)
        circuit.append(h2)
        circuit.append(h3)
        assert len(circuit.instructions) == 3

    def test_inline_update_rule_together(self, gate):
        """Test inline update rule as list"""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.INLINE)
        circuit.append([h1, h2, h3])
        assert len(circuit.instructions) == 3

    def test_new_update_rule(self, gate):
        """Test new update rule as list"""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.NEW)
        circuit.append(h1)
        circuit.append(h2)
        circuit.append(h3)
        assert len(circuit.moments) == 3

    def test_new_update_rule_together(self, gate):
        """Test new update rule as list"""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.NEW)
        circuit.append([h1, h2, h3])
        assert len(circuit.moments) == 3

    def test_earliest_update_rule(self, gate):
        """Test earliest update rule as list"""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.EARLIEST)
        circuit.append(h1)
        circuit.append(h2)
        circuit.append(h3)
        assert len(circuit.moments) == 1

    def test_earliest_update_rule_together(self, gate):
        """Test earliest update rule as list"""
        h1 = Instruction(gate, 0)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 1)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.EARLIEST)
        circuit.append([h1, h2, h3])
        assert len(circuit.moments) == 2

    def test_new_then_inline_rule(self, gate):
        """Test new then inline update rule.
        There is a distinction here between the below test_new_then_inline_rule_together()
        because this will create a new moment every time append is called.
        """
        h1 = Instruction(gate, 1)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        h4 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.NEW_THEN_INLINE)
        circuit.append(h1)
        circuit.append(h2)
        circuit.append(h3)
        circuit.append(h4)
        assert len(circuit.moments) == 4

    def test_new_then_inline_rule_together(self, gate):
        """Test new then inline update rule"""
        h1 = Instruction(gate, 1)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        h4 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.NEW_THEN_INLINE)
        circuit.append([h1, h2, h3, h4])
        assert len(circuit.moments) == 3

    @pytest.mark.parametrize(
        "circuit_param, expected",
        [
            (
                circuit(),
                {
                    "_qubits": [0, 1, 2],
                    "_moments": [],
                    "name": "test_circuit",
                    "_parameter_table": ParameterTable({}),
                    "update_rule": update_rule.UpdateRule.EARLIEST,
                },
            ),
        ],
    )
    def test_creating_circuit(self, circuit_param, expected):
        """Test creating a circuit."""
        # check class parameters
        dict = circuit_param.__dict__.copy()
        get_qubit_idx_dict(dict)
        assert dict == expected

    @pytest.mark.parametrize(
        "circuit_param, expected",
        [
            (
                circuit(),
                {
                    "_qubits": [0, 1, 2],
                    "_moments": [Moment("[]")],
                    "name": "test_circuit",
                    "_parameter_table": ParameterTable({}),
                    "update_rule": update_rule.UpdateRule.EARLIEST,
                },
            )
        ],
    )
    def test_add_moment(self, circuit_param, expected):
        """Test adding a moment."""
        moment = Moment()
        circuit_param.append(moment)
        dict = circuit_param.__dict__.copy()
        assert len(dict["_moments"]) == len(expected["_moments"])

        """
        DRAWER TESTS
        """


class TestDrawer:
    @pytest.fixture()
    def gate(self):
        return circuits.H()

    def test_circuit_drawer(self, gate):
        h1 = Instruction(gate, 1)
        h2 = Instruction(gate, 1)
        h3 = Instruction(gate, 2)
        h4 = Instruction(gate, 2)
        circuit = Circuit(num_qubits=3, name="test_circuit", update_rule=UpdateRule.NEW_THEN_INLINE)
        circuit.append([h1, h2, h3, h4])
        drawer(circuit)
        assert True

    def test_moment_drawer(self, gate):
        h1 = Instruction(gate, 1)
        moment = Moment()
        moment.append(h1)
        with pytest.raises(TypeError):
            drawer(moment)

    def test_instruction_drawer(self, gate):
        h1 = Instruction(gate, 1)
        with pytest.raises(TypeError):
            drawer(h1)


class TestRandomCircuit:

    @pytest.mark.parametrize("package", ["qiskit", "braket", "cirq"])
    def test_random_circuit(self, package):
        rand_circuit = random_circuit(package)
        if package == "qiskit":
            assert isinstance(rand_circuit, QiskitCircuit)
        elif package == "braket":
            assert isinstance(rand_circuit, BraketCircuit)
        elif package == "cirq":
            assert isinstance(rand_circuit, CirqCircuit)
        else:
            raise ValueError



