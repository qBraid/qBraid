"""QiskitResultWrapper Class"""

import numpy as np
from qiskit.result.result import Result

from qbraid.devices.result import ResultWrapper


class QiskitResultWrapper(ResultWrapper):
    """Qiskit ``Result`` wrapper class."""

    # pylint: disable=too-few-public-methods
    def __init__(self, result: Result):
        """Create a QiskitResultWrapper

        Args:
            result (Result): a Qiskit ``Result`` object

        """
        super().__init__(result)

    def measurements(self):
        qiskit_meas = self.vendor_rlo.get_memory()
        qbraid_meas = []
        for str_shot in qiskit_meas:
            lst_shot = [int(x) for x in list(str_shot)]
            qbraid_meas.append(lst_shot)
        return np.array(qbraid_meas)

    def measurement_counts(self):

        return self.vendor_rlo.get_counts()
