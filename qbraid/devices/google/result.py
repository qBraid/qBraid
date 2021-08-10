# Copyright 2019 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# NOTICE: This file has been modified from the original:
# https://github.com/quantumlib/Cirq/blob/504bdbb9bb30249d85ecf7ba199b047150ee33f3/cirq-core/cirq
# /study/result.py

"""CirqResultWrapper Class"""

import pandas as pd
from cirq.study.result import Result

from qbraid.devices import ResultWrapper


class CirqResultWrapper(ResultWrapper):
    """Cirq ``Result`` wrapper class."""

    # pylint: disable=too-few-public-methods
    def __init__(self, cirq_result: Result):
        """Create a CirqResultWrapper

        Args:
            cirq_result (Result): a Cirq ``Result`` object

        """

        super().__init__(cirq_result)
        self.vendor_rlo = cirq_result

    def data(self, **kwargs) -> pd.DataFrame:
        """Return a DataFrame with columns as measurement keys, rows as repetitions, and a big
        endian integer for individual measurements. Note that when a numpy array is produced from
        this data frame, Pandas will try to use np.int64 as dtype, but will upgrade to object if
        any value is too large to fit.
        """
        return self.vendor_rlo.data
