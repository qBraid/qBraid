from ...gate import Gate


class Unitary(Gate):
    """Unitary gate.

    .. todo: Finish implementing unitary gate

    """

    def __init__(self, name, num_qubits, params=None, global_phase=0.0):
        super().__init__(name, num_qubits, params=params, global_phase=global_phase)

        pass
