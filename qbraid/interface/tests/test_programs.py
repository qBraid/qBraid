"""
Unit tests for equivalence of interfacing quantum programs
"""
import pytest

from qbraid.interface._programs import bell_circuits, random_circuit, shared15_circuits
from qbraid.interface.calculate_unitary import equal_unitaries


def test_bell():
    """Test the equality of bell circuits"""
    map, _ = bell_circuits()
    braket_bell = map["braket"]()
    cirq_bell = map["cirq"]()
    pyquil_bell = map["pyquil"]()
    pennylane_bell = map["pennylane"]()
    qiskit_bell = map["qiskit"]()

    eq1 = equal_unitaries(braket_bell, cirq_bell)
    eq2 = equal_unitaries(cirq_bell, pyquil_bell)
    eq3 = equal_unitaries(pyquil_bell, pennylane_bell)
    eq4 = equal_unitaries(pennylane_bell, qiskit_bell)

    assert eq1 and eq2 and eq3 and eq4


def test_shared15():
    """Test the equality of shared gates circuits"""
    map, _ = shared15_circuits()
    braket_shared15 = map["braket"]()
    cirq_shared15 = map["cirq"]()
    qiskit_shared15 = map["qiskit"]()

    eq1 = equal_unitaries(braket_shared15, cirq_shared15)
    eq2 = equal_unitaries(cirq_shared15, qiskit_shared15)

    assert eq1 and eq2


@pytest.mark.parametrize("package", ["braket", "cirq", "qiskit"])
def test_random(package):
    """Test generating random circuits"""
    try:
        random_circuit(package)
    except Exception:
        assert False
    assert True
