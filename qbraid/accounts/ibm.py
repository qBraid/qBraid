from qiskit import IBMQ

def get_ibm_provider():
    
    return IBMQ.enable_account(input("Insert IBM Token"))
