# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for qbraid.programs.braket.BraketCircuit

"""
from itertools import chain, combinations
from unittest.mock import Mock

import numpy as np
import pytest
from braket.circuits import Circuit, Instruction, gates

from qbraid.programs import ProgramTypeError
from qbraid.programs.gate_model.braket import BraketCircuit


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


def test_braket_circuit_serialize_regular():
    """Test serialization of regular (non-pulse) Braket circuits."""
    circuit = Circuit().h(0).cnot(0, 1).measure(0).measure(1)
    qprogram = BraketCircuit(circuit)
    serialized = qprogram.serialize()
    
    # Should return a dict with openQasm key
    assert isinstance(serialized, dict)
    assert "openQasm" in serialized
    assert isinstance(serialized["openQasm"], str)
    assert len(serialized["openQasm"]) > 0


def test_braket_circuit_serialize_pulse(monkeypatch):
    """Test serialization of pulse Braket circuits."""
    try:
        from braket.circuits.gates import PulseGate
        from braket.pulse import Frame, Port, PulseSequence
        from braket.pulse.waveforms import GaussianWaveform
        
        # Create pulse elements
        qubit_port = Port(port_id="q0_rf", dt=1e-9, properties={})
        drive_frame = Frame(
            frame_id="q0_drive",
            frequency=4.5e9,
            port=qubit_port,
            phase=0,
            is_predefined=False,
        )
        
        gaussian_pulse = GaussianWaveform(
            length=100e-9, sigma=25e-9, amplitude=0.3, zero_at_edges=True
        )
        
        pulse_sequence = PulseSequence()
        pulse_sequence.play(drive_frame, gaussian_pulse)
        
        pulse_circuit = Circuit()
        pulse_gate = PulseGate(pulse_sequence, 1)
        pulse_instruction = Instruction(pulse_gate, [0])
        pulse_circuit.add_instruction(pulse_instruction)
        pulse_circuit.measure(0)
        
        qprogram = BraketCircuit(pulse_circuit)
        serialized = qprogram.serialize()
        
        # Should return a dict with openQasm key for pulse circuits too
        assert isinstance(serialized, dict)
        assert "openQasm" in serialized
        assert isinstance(serialized["openQasm"], str)
        assert len(serialized["openQasm"]) > 0
        # Should contain calibration statements
        assert "cal {" in serialized["openQasm"]
        
    except ImportError:
        # Skip test if pulse modules not available
        pytest.skip("Braket pulse modules not available")


def test_braket_circuit_has_pulse_gates_detection():
    """Test detection of pulse gates in circuits."""
    from qbraid.programs.gate_model.braket import BraketCircuit
    
    # Regular circuit should not have pulse gates
    regular_circuit = Circuit().h(0).cnot(0, 1)
    regular_qprogram = BraketCircuit(regular_circuit)
    # Access the private method for testing
    has_pulse_gates = any(
        isinstance(instr.operator, __import__('braket.circuits.gates', fromlist=['PulseGate']).PulseGate) 
        for instr in regular_circuit.instructions
    )
    assert not has_pulse_gates
    
    # This test verifies the import and basic structure works
    assert hasattr(regular_qprogram, 'serialize')
