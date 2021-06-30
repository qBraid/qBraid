class Circuit:

    """
    Circuit class for qBraid quantum circuit objects.
    Args:
        num_qubits: The total number of qubits
        name: The name of the circuit
        update_rule: How to pick/create the moment to put operations into.
    """

    def __init__(
        self,
        num_qubits,
        name: str = None,
        
    ):
        self._qubits = [i for i in range(num_qubits)]
        self._moments = []  # list of moments
        self.name = name

x = Circuit(3)

print(x.__dict__)