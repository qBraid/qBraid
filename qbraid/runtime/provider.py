# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for configuring provider credentials and authentication.

"""
from abc import ABC, abstractmethod


class QuantumProvider(ABC):
    """
    This class is responsible for managing the interactions and
    authentications with various Quantum services.

    """

    def save_config(self, **kwargs):
        """Saves account data and/or credentials to the disk."""
        raise NotImplementedError

    @abstractmethod
    def get_devices(self, **kwargs):
        """Return a list of backends matching the specified filtering."""

    @abstractmethod
    def get_device(self, device_id: str):
        """Return quantum device corresponding to the specified device ID."""

    def __eq__(self, other):
        """Equality comparison.

        By default, it is assumed that two `QuantumProviders` from the same class are
        equal. Subclassed providers can override this behavior.
        """
        return type(self).__name__ == type(other).__name__
