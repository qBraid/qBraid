from ..gate import GateWrapper


class QbraidGateWrapper(GateWrapper):
    """
    qBraid Gate Wrapper class

    Args:
        gate: input object
        name (optional): name of the gate
        gate_type: a string demonstrating the gate type according to qBraid
            documentation. (eg. 'H', 'CX', 'MEASURE')

    Attributes:
        package: the name of the pacakge to which the original gate object
            belongs (eg. 'qiskit')
    """

    def __init__(self, gate_type: str):

        super().__init__()

        self._gate_type = gate_type
        self._package = "qbraid"
