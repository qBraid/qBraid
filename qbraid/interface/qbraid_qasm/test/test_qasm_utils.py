
from qbraid.interface.qbraid_qasm.tools import qasm_qubits, qasm_num_qubits, qasm_depth
from qbraid.interface.qbraid_qasm.circuits import qasm_bell, qasm_shared15

def test_qasm_qubits():
    """test calculate qasm qubit"""
    
    assert qasm_qubits(qasm_bell()) == ['qreg q[2];']
    assert qasm_qubits(qasm_shared15()) == ['qreg q[4];']
def test_qasm_num_qubits():
    assert qasm_num_qubits(qasm_bell()) == 2
    assert qasm_num_qubits(qasm_shared15()) == 4

def test_qasm_depth():
    """test calcualte qasm depth"""
    assert qasm_depth(qasm_bell()) == 2
    assert qasm_depth(qasm_shared15()) == 22