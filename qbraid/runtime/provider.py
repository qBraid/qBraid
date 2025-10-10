# Copyright 2025 qBraid
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
Module for configuring provider credentials and authentication.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from qbraid.runtime.device import QuantumDevice


class QuantumProvider(ABC):
    """
    Abstract base class for managing interactions and authentication with various quantum
    service providers.

    This class defines the core interface that any quantum provider must implement to facilitate
    access to their quantum devices via qBraid Runtime. Subclasses should build upon this structure
    to incorporate any additional steps specific to their quantum platform, such as managing
    authentication, retrieving available devices, or handling other provider-specific functionality.

    Subclass implementations of the :py:meth:`QuantumProvider.get_device` and
    :py:meth:`QuantumProvider.get_devices` methods should dynamically construct a detailed
    :py:class:`TargetProfile` for each device. This profile is necessary to instantiate a
    :py:class:`QuantumDevice` and plays a central role in defining the runtime behavior and request
    structure necessary for submitting and executing quantum programs on that device through your
    service. To learn more, check out our documentation on
    `setting up a new provider <https://docs.qbraid.com/sdk/user-guide/runtime/new-provider>`_ and
    the `components of qBraid Runtime <https://docs.qbraid.com/sdk/user-guide/runtime/components>`_.

    """

    @overload
    def get_devices(self) -> list[QuantumDevice]: ...

    @overload
    def get_devices(self, **kwargs) -> list[QuantumDevice]: ...

    @abstractmethod
    def get_devices(self, **kwargs) -> list[QuantumDevice]:
        """
        Retrieves a list of available quantum devices, applying any specified filtering criteria.

        Args:
            **kwargs: Optional keyword arguments for filtering devices, if applicable.

        Returns:
            list[QuantumDevice]: A list of quantum devices that meet the filtering criteria,
                or all devices if no filters are applied.
        """

    @abstractmethod
    def get_device(self, device_id: str) -> QuantumDevice:
        """
        Retrieves the quantum device corresponding to the specified device ID.

        Args:
            device_id (str): The unique identifier of the quantum device.

        Returns:
            QuantumDevice: The quantum device matching the specified device ID.
        """

    def __eq__(self, other: Any) -> bool:
        """
        Compares two `QuantumProvider` instances for equality.

        By default, two `QuantumProvider` objects are considered equal if they are instances of the
        same class or subclass. Subclasses can override this behavior to include additional
        equality checks (e.g., comparing configuration or state).

        Args:
            other (Any): The object to compare with the current instance.

        Returns:
            bool: True if both objects are instances of the same class or subclass; False otherwise.
        """
        if not isinstance(other, type(self)):
            return False
        return True
