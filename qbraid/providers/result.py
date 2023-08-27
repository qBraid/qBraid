# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module defining abstract ResultWrapper Class

"""
from abc import ABC, abstractmethod

from qiskit.visualization import plot_histogram


def _format_counts(raw_counts: dict, remove_zeros=True) -> dict:
    """Formats, sorts, and adds missing bit indicies to counts dictionary
    Can pass in a 'removeZeros' parameter to decide whether to plot the non-zero counts
    For example:

    .. code-block:: python

        >>> counts
        {'1 1': 13, '0 0': 46, '1 0': 79}
        >>> _format_counts(counts)
        {'00': 46, '01': 0, '10': 79, '11': 13}

    """

    # method to remove all zero count results
    def remove_zero_values(dictionary):
        keys_to_remove = [key for key, value in dictionary.items() if value == 0]

        for key in keys_to_remove:
            del dictionary[key]

        return dictionary

    # Remove spaces from keys
    counts = {key.replace(" ", ""): value for key, value in raw_counts.items()}

    # Create the sorted dictionary, filling in missing keys with 0
    num_bits = max(len(key) for key in counts)
    all_keys = [format(i, "0" + str(num_bits) + "b") for i in range(2**num_bits)]

    # removing zero value counts
    final_counts = {key: counts.get(key, 0) for key in sorted(all_keys)}
    if remove_zeros:
        final_counts = remove_zero_values(final_counts)
    return final_counts


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
    def raw_counts(self):
        """Returns raw histogram data of the run"""

    def measurement_counts(self, remove_zeros=True):
        """Returns the sorted histogram data of the run"""
        raw_counts = self.raw_counts()
        if isinstance(raw_counts, dict):
            return _format_counts(raw_counts, remove_zeros)
        return [_format_counts(counts) for counts in raw_counts]

    def plot_counts(self, remove_zeros=True):
        """Plot histogram of measurement counts"""
        counts = self.measurement_counts(remove_zeros)
        if isinstance(counts, dict):
            return plot_histogram(counts)
        return [plot_histogram(count) for count in counts]
