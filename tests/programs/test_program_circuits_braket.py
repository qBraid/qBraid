# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for qbraid.programs.braket.BraketCircuit

"""
import re
from itertools import chain, combinations
from unittest.mock import Mock

import numpy as np
import pytest
from braket.circuits import Circuit, Instruction, gates
from braket.circuits.measure import Measure
from braket.circuits.serialization import IRType

from qbraid.programs import ProgramTypeError
from qbraid.programs.gate_model.braket import BraketCircuit
from qbraid.runtime.profile import TargetProfile


def get_subsets(nqubits):
    """Return list of all combinations up to number nqubits"""
    qubits = list(range(0, nqubits))

    def combos(x):
        return combinations(qubits, x)

    all_subsets = chain(*map(combos, range(0, len(qubits) + 1)))
    return list(all_subsets)[1:]


def calculate_expected(gates_set):
    """Calculated expected unitary"""
    if len(gates_set) == 1:
        return gates_set[0]
    if len(gates_set) == 2:
        return np.kron(gates_set[1], gates_set[0])
    return np.kron(calculate_expected(gates_set[2:]), np.kron(gates_set[1], gates_set[0]))


def generate_test_data(input_gate_set, contiguous=True):
    """Generate test data"""
    testdata = []
    gate_set = input_gate_set.copy()
    gate_set.append(gates.I)
    nqubits = len(input_gate_set)
    subsets = get_subsets(nqubits)
    for ss in subsets:
        bk_instrs = []
        np_gates = []
        for index in range(max(ss) + 1):
            idx = -1 if index not in ss else index
            BKGate = gate_set[idx]
            np_gate = BKGate().to_matrix()
            if idx != -1 or contiguous:
                bk_instrs.append((BKGate, index))
            np_gates.append(np_gate)
        u_expected = calculate_expected(np_gates)
        testdata.append((bk_instrs, u_expected))
    return testdata


def make_circuit(bk_instrs):
    """Constructs Braket circuit from list of instructions"""
    circuit = Circuit()
    for instr in bk_instrs:
        Gate, index = instr
        circuit.add_instruction(Instruction(Gate(), target=index))
    qprogram = BraketCircuit(circuit)
    qprogram.populate_idle_qubits()
    return qprogram.program


test_gate_set = [gates.X, gates.Y, gates.Z]
test_data_contiguous_qubits = generate_test_data(test_gate_set)
test_data_non_contiguous_qubits = generate_test_data(test_gate_set, contiguous=False)
test_data = test_data_contiguous_qubits + test_data_non_contiguous_qubits


@pytest.mark.parametrize("bk_instrs,u_expected", test_data)
def test_unitary_calc(bk_instrs, u_expected):
    """Test calculating unitary of circuits using both contiguous and
    non-contiguous qubit indexing."""
    circuit = make_circuit(bk_instrs)
    qbraid_circuit = BraketCircuit(circuit)
    u_test = qbraid_circuit.unitary_little_endian()
    assert np.allclose(u_expected, u_test)


@pytest.mark.parametrize("bk_instrs,u_expected", test_data)
def test_convert_be_to_le(bk_instrs, u_expected):
    """Test converting big-endian unitary to little-endian unitary."""
    circuit = make_circuit(bk_instrs)
    qbraid_circuit = BraketCircuit(circuit)
    u_test = qbraid_circuit.unitary_little_endian()
    assert np.allclose(u_expected, u_test)


def test_kronecker_product_factor_permutation():
    """Test calculating unitary permutation representing
    circuits with reversed qubits"""
    bk_circuit = Circuit().h(0).cnot(0, 1)
    circuit = BraketCircuit(bk_circuit)

    unitary = circuit.unitary()
    circuit.reverse_qubit_order()
    unitary_rev = circuit.unitary_rev_qubits()

    assert np.allclose(unitary, unitary_rev)


def test_unitary_little_endian_braket_bell():
    """Test convert_to_contigious on bell circuit"""
    circuit = Circuit().h(0).cnot(0, 1)  # pylint: disable=no-member
    h_gate = np.sqrt(1 / 2) * np.array([[1, 1], [1, -1]])
    h_gate_kron = np.kron(np.eye(2), h_gate)
    cnot_gate = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]])
    u_expected = np.einsum("ij,jk->ki", h_gate_kron, cnot_gate)
    qprogram = BraketCircuit(circuit)
    qprogram.remove_idle_qubits()
    u_little_endian = qprogram.unitary_little_endian()
    assert np.allclose(u_expected, u_little_endian)


def test_collapse_empty_braket_control_modifier():
    """Test that converting braket circuits to contiguous qubits works with control modifiers"""
    circuit = Circuit().y(target=0, control=1)
    qprogram = BraketCircuit(circuit)
    qprogram.remove_idle_qubits()
    contig_circuit = qprogram.program
    assert circuit.qubit_count == contig_circuit.qubit_count


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        BraketCircuit(Mock())


def test_properties():
    """Test properties of BraketCircuit"""
    circuit = Circuit().h(0).cnot(0, 1)
    qprogram = BraketCircuit(circuit)
    assert qprogram.qubits == circuit.qubits
    assert qprogram.num_clbits == 0
    assert qprogram.depth == circuit.depth


def test_pad_measurements_no_existing_measurements():
    """Test pad_measurements method when no measurements exist."""
    circuit = Circuit().h(0).cnot(0, 1)
    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    # Should have no measurement
    measurement_count = sum(
        1
        for instr in qprogram.program.instructions
        if hasattr(instr.operator, "__class__") and instr.operator.__class__.__name__ == "Measure"
    )
    assert measurement_count == 0


def test_pad_measurements_with_existing_measurements():
    """Test pad_measurements method when some measurements already exist."""
    circuit = Circuit().h(0).cnot(0, 1).measure(0)
    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    # Should have measurements on all qubits now
    measurement_count = sum(
        1
        for instr in qprogram.program.instructions
        if hasattr(instr.operator, "__class__") and instr.operator.__class__.__name__ == "Measure"
    )
    assert measurement_count == 2

    # Should track the originally measured qubit
    assert hasattr(qprogram.program, "partial_measurement_qubits")
    assert qprogram.program.partial_measurement_qubits == [0]


def test_pad_measurements_multiple_partial_measurements():
    """Test pad_measurements method with multiple partial measurements."""
    circuit = Circuit().h(0).cnot(0, 1).cnot(1, 2).measure(0).measure(2)
    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    # Should have measurements on all qubits now
    measurement_count = sum(
        1
        for instr in qprogram.program.instructions
        if hasattr(instr.operator, "__class__") and instr.operator.__class__.__name__ == "Measure"
    )
    assert measurement_count == 3

    # Should track the originally measured qubits
    assert hasattr(qprogram.program, "partial_measurement_qubits")
    assert set(qprogram.program.partial_measurement_qubits) == {0, 2}


def test_transform_with_ionq_device():
    """Test transform method with IonQ device calls pad_measurements."""
    circuit = Circuit().h(0).cnot(0, 1).measure(0)
    qprogram = BraketCircuit(circuit)

    # Mock device with IonQ provider
    mock_device = Mock()
    mock_device.simulator = False
    mock_device.profile = TargetProfile(
        device_id="test_device",
        simulator=False,
        provider_name="IonQ",
    )

    qprogram.transform(mock_device)

    # Should have padded measurements
    measurement_count = sum(
        1
        for instr in qprogram.program.instructions
        if hasattr(instr.operator, "__class__") and instr.operator.__class__.__name__ == "Measure"
    )
    assert measurement_count == 2
    assert hasattr(qprogram.program, "partial_measurement_qubits")
    assert qprogram.program.partial_measurement_qubits == [0]


def test_transform_with_amazon_braket_device():
    """Test transform method with Amazon Braket device calls pad_measurements."""
    circuit = Circuit().h(0).cnot(0, 1).measure(1)
    qprogram = BraketCircuit(circuit)

    # Mock device with Amazon Braket provider
    mock_device = Mock()
    mock_device.simulator = False
    mock_device.profile = TargetProfile(
        device_id="test_device",
        simulator=False,
        provider_name="Amazon Braket",
    )

    qprogram.transform(mock_device)

    # Should have padded measurements
    measurement_count = sum(
        1
        for instr in qprogram.program.instructions
        if hasattr(instr.operator, "__class__") and instr.operator.__class__.__name__ == "Measure"
    )
    assert measurement_count == 2
    assert hasattr(qprogram.program, "partial_measurement_qubits")
    assert qprogram.program.partial_measurement_qubits == [1]


def test_transform_with_other_provider():
    """Test transform method with other provider doesn't call pad_measurements."""
    circuit = Circuit().h(0).cnot(0, 1).measure(0)
    qprogram = BraketCircuit(circuit)

    # Mock device with other provider
    mock_device = Mock()
    mock_device.simulator = False
    mock_device.profile = TargetProfile(
        device_id="test_device",
        simulator=False,
        provider_name="Other Provider",
    )

    qprogram.transform(mock_device)

    # Should not have padded measurements
    measurement_count = sum(
        1
        for instr in qprogram.program.instructions
        if hasattr(instr.operator, "__class__") and instr.operator.__class__.__name__ == "Measure"
    )
    assert measurement_count == 1
    assert not hasattr(qprogram.program, "partial_measurement_qubits")


def _measure_target_indices(circuit: Circuit) -> list[int]:
    return [
        instr.operator._target_index
        for instr in circuit.instructions
        if isinstance(instr.operator, Measure)
    ]


def _assert_serialized_qasm_has_unique_bits(
    qprogram: BraketCircuit, expected_measures: int
) -> None:
    """Emit OpenQASM from the Braket Circuit and verify the measurement declarations
    map to unique classical bit indices, one per measure, all within ``qubit_count``."""
    source = qprogram.program.to_ir(IRType.OPENQASM).source
    bit_indices = [int(m) for m in re.findall(r"b\[(\d+)\]\s*=\s*measure\b", source)]
    assert len(bit_indices) == expected_measures
    assert len(set(bit_indices)) == expected_measures
    assert all(idx < qprogram.program.qubit_count for idx in bit_indices)


def _force_measure_target_index(circuit: Circuit, qubit: int, target_index: int) -> None:
    # Simulate what ``Circuit.from_ir`` does when the source QASM uses a literal bit index
    # that does not match Braket's own counter-based convention for ``Measure._target_index``.
    for instr in circuit.instructions:
        if isinstance(instr.operator, Measure) and int(instr.target[0]) == qubit:
            instr.operator._target_index = target_index
            return
    raise AssertionError(f"no measure instruction targeting qubit {qubit}")


def test_pad_measurements_rebases_multi_register_collision():
    """Multiple classical registers in the source QASM collapse into colliding
    ``_target_index`` values after ``Circuit.from_ir``. ``pad_measurements`` must detect
    the internal collision and rebase every existing measure so the final QASM emits a
    unique classical bit per measurement."""
    circuit = Circuit().h(0).h(1).h(2).h(3).measure(0).measure(1).measure(2).measure(3)
    # Emulate: a[0]=q[0], a[1]=q[1], b[0]=q[2], b[1]=q[3] — indices collide across registers
    _force_measure_target_index(circuit, 0, 0)
    _force_measure_target_index(circuit, 1, 1)
    _force_measure_target_index(circuit, 2, 0)
    _force_measure_target_index(circuit, 3, 1)

    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    assert _measure_target_indices(qprogram.program) == [0, 1, 2, 3]
    assert qprogram.program.partial_measurement_qubits == [0, 1, 2, 3]
    _assert_serialized_qasm_has_unique_bits(qprogram, expected_measures=4)


def test_pad_measurements_rebases_when_padding_would_collide():
    """When an existing measure's ``_target_index`` lies within the range that Braket's
    counter-based ``.measure()`` will assign to padded measures, those indices collide.
    ``pad_measurements`` must rebase the existing measure before padding."""
    circuit = Circuit().h(0).h(5).measure(0)
    # User wrote ``c[5] = measure q[0]`` — target_index 5 will clash with the padded
    # measure for qubit 5, which Braket's counter assigns to index 5 as well.
    _force_measure_target_index(circuit, 0, 5)

    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    target_indices = _measure_target_indices(qprogram.program)
    assert len(target_indices) == len(set(target_indices))
    assert max(target_indices) < qprogram.program.qubit_count
    assert qprogram.program.partial_measurement_qubits == [0]
    _assert_serialized_qasm_has_unique_bits(
        qprogram, expected_measures=qprogram.program.qubit_count
    )


def test_pad_measurements_rebases_out_of_range_target_index():
    """A user-written ``_target_index`` greater than or equal to ``qubit_count`` produces
    invalid QASM, because Braket emits ``bit[qubit_count] b``. ``pad_measurements`` must
    rebase such measures even when there is no direct collision."""
    circuit = Circuit().h(0).h(1).h(2).h(3).measure(0)
    # User wrote ``c[10] = measure q[0]`` on a 4-qubit circuit — out of Braket's emission range.
    _force_measure_target_index(circuit, 0, 10)

    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    target_indices = _measure_target_indices(qprogram.program)
    assert all(idx < qprogram.program.qubit_count for idx in target_indices)
    assert len(target_indices) == len(set(target_indices))
    _assert_serialized_qasm_has_unique_bits(
        qprogram, expected_measures=qprogram.program.qubit_count
    )


def test_pad_measurements_preserves_safe_user_labels():
    """When the existing measures' ``_target_index`` values are unique, in range, and
    do not overlap with the slots Braket's counter will assign to padded measures,
    ``pad_measurements`` must leave them untouched so user-chosen bit labels round-trip
    through serialization unchanged."""
    circuit = Circuit().h(0).h(1).h(2).h(3).measure(0).measure(1)
    # Sequential, in-range, no overlap with padded range [2, 3] — safe to preserve.
    _force_measure_target_index(circuit, 0, 0)
    _force_measure_target_index(circuit, 1, 1)

    qprogram = BraketCircuit(circuit)
    qprogram.pad_measurements()

    target_indices = _measure_target_indices(qprogram.program)
    assert target_indices[:2] == [0, 1]  # preserved, not rebased
    assert len(target_indices) == 4
    assert len(set(target_indices)) == 4
    _assert_serialized_qasm_has_unique_bits(qprogram, expected_measures=4)


def test_replace_i_with_rz_zero():
    """Test replace_i_with_rz_zero method replaces identity gates with rz(0) gates."""
    circuit = Circuit().i(0).h(1).i(2).cnot(0, 1)
    qprogram = BraketCircuit(circuit)
    qprogram.replace_i_with_rz_zero()

    i_gate_count = sum(
        1 for instr in qprogram.program.instructions if instr.operator.name.lower() == "i"
    )
    rz_gate_count = sum(
        1 for instr in qprogram.program.instructions if instr.operator.name.lower() == "rz"
    )

    assert i_gate_count == 0  # No identity gates should remain
    assert rz_gate_count == 2  # Should have 2 rz gates (from the 2 identity gates)
    for instr in qprogram.program.instructions:
        if instr.operator.name.lower() == "rz":
            assert instr.operator.angle == 0
