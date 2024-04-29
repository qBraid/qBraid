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
Module defining the Configuration class for quantum devices, providing necessary
parameters for integration with the qBraid runtime.

"""

from collections.abc import Mapping
from typing import Any, Iterator, Optional

from qbraid.programs import ProgramSpec
from qbraid.transpiler import ConversionGraph

from .enums import DeviceType


class RuntimeProfile(Mapping):
    """
    Encapsulates configuration settings for a quantum device, presenting them as a read-only dictionary.
    This class primarily stores and manages settings that are crucial for the proper functioning and integration
    of quantum devices within a specified environment.

    Attributes:
        _data (dict): Internal storage for the configuration properties.
    """

    def __init__(
        self,
        device_type: DeviceType,
        device_num_qubits: int,
        program_spec: ProgramSpec,
        conversion_graph: Optional[ConversionGraph] = None,
        **kwargs,
    ) -> None:
        """
        Initializes a new instance of the RuntimeProfile, setting up configuration according to the provided parameters.

        Args:
            device_type (DeviceType): Type of the quantum device, should be an instance of DeviceType.
            device_num_qubits (int): Number of qubits supported by the device.
            program_spec (ProgramSpec): Specification for the program, encapsulating program type and other metadata.
            conversion_graph (Optional[ConversionGraph]): Graph coordinating conversions between different quantum software program
                                                          types. If None, the default qBraid graph is used. Defaults to None.

        Raises:
            TypeError: If any of the inputs are not of the expected type.
        """
        if not isinstance(device_type, DeviceType):
            raise TypeError("device_type must be an instance of DeviceType")
        if not isinstance(device_num_qubits, int):
            raise TypeError("device_num_qubits must be an integer")
        if not isinstance(program_spec, ProgramSpec):
            raise TypeError("program_spec must be an instance of ProgramSpec")
        if conversion_graph is None:
            conversion_graph = ConversionGraph()
        elif not isinstance(conversion_graph, ConversionGraph):
            raise TypeError("conversion_graph must be an instance of ConversionGraph")

        self._data = {
            "device_type": device_type,
            "device_num_qubits": device_num_qubits,
            "program_spec": program_spec,
            "conversion_graph": conversion_graph,
            **kwargs,
        }

    def __getitem__(self, key: str) -> Any:
        """Return the value associated with the key."""
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        """Iterate over the keys of the configuration."""
        return iter(self._data)

    def __len__(self) -> int:
        """Return the number of items in the configuration."""
        return len(self._data)
