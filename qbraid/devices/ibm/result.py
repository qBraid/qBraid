# This code is part of Qiskit.
#
# (C) Copyright IBM 2017.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of the source tree https://github.com/Qiskit/qiskit-terra/blob/main/LICENSE.txt
# or at http://www.apache.org/licenses/LICENSE-2.0.
#
# NOTICE: This file has been modified from the original:
# https://github.com/Qiskit/qiskit-terra/blob/main/qiskit/result/result.py

"""QiskitResultWrapper Class"""

from typing import Dict

from qiskit.result.result import Result

from qbraid.devices.result import ResultWrapper


class QiskitResultWrapper(ResultWrapper):
    """Qiskit ``Result`` wrapper class."""

    # pylint: disable=too-few-public-methods
    def __init__(self, vendor_rlo: Result):
        """Create a QiskitResultWrapper

        Args:
            vendor_rlo (Result): a Qiskit ``Result`` object

        """
        super().__init__(vendor_rlo)
        self.vendor_rlo = vendor_rlo

    def data(self, **kwargs) -> Dict:
        """Get the raw data for an experiment.

        Returns:
            dict: A dictionary of results data for an experiment.

        Raises:
            QiskitError: if data for the experiment could not be retrieved.

        """
        return self.vendor_rlo.data(**kwargs)
