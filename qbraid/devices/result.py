# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module defining abstract ResultWrapper Class

"""
from abc import ABC, abstractmethod

from qiskit.visualization import plot_histogram


class ResultWrapper(ABC):
    """Abstract interface for result-like classes.

    Args:
        vendor_rlo: A result-like object

    """

    def __init__(self, vendor_rlo):
        self.vendor_rlo = vendor_rlo

    @abstractmethod
    def measurements(self):
        """Return measurements as list"""

    @abstractmethod
    def measurement_counts(self):
        """Returns the histogram data of the run"""

    def plot_counts(self):
        """Plot histogram of measurement counts"""
        counts = self.measurement_counts()
        return plot_histogram(counts)
