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
Module defining abstract QuantumJobResult Class

"""
from abc import ABC, abstractmethod


class QuantumJobResult(ABC):
    """Abstract interface for result-like classes.

    Args:
        _result: A result-like object

    """

    def __init__(self, _result):
        self._result = _result

    @abstractmethod
    def measurements(self):
        """Return measurements as list"""

    @abstractmethod
    def raw_counts(self):
        """Returns raw histogram data of the run"""

    @staticmethod
    def format_counts(counts: dict, include_zero_values: bool = False) -> dict:
        """Formats, sorts, and adds missing bit indices to counts dictionary
        Can pass in a 'include_zero_values' parameter to decide whether to include the states
        with zero counts.

        For example:

        .. code-block:: python

            >>> counts
            {'1 1': 13, '0 0': 46, '1 0': 79}
            >>> QuantumJobResult.format_counts(counts)
            {'00': 46, '10': 79, '11': 13}
            >>> QuantumJobResult.format_counts(counts, include_zero_values=True)
            {'00': 46, '01': 0, '10': 79, '11': 13}

        """
        counts = {key.replace(" ", ""): value for key, value in counts.items()}

        num_bits = max(len(key) for key in counts)
        all_keys = [format(i, f"0{num_bits}b") for i in range(2**num_bits)]
        final_counts = {key: counts.get(key, 0) for key in sorted(all_keys)}

        if not include_zero_values:
            final_counts = {key: value for key, value in final_counts.items() if value != 0}

        return final_counts

    def measurement_counts(self, include_zero_values: bool = False) -> dict:
        """Returns the sorted histogram data of the run"""
        raw_counts = self.raw_counts()
        if isinstance(raw_counts, dict):
            return self.format_counts(raw_counts, include_zero_values=include_zero_values)
        return [
            self.format_counts(counts, include_zero_values=include_zero_values)
            for counts in raw_counts
        ]
