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
Module defining QuantumProgramWrapper Class

"""
from typing import TYPE_CHECKING, List, Optional

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.exceptions import PackageValueError
from qbraid.interface.circuit_drawer import circuit_drawer
from qbraid.transpiler.conversions import convert_from_cirq, convert_to_cirq
from qbraid.transpiler.exceptions import CircuitConversionError

if TYPE_CHECKING:
    import qbraid


class QuantumProgramWrapper:
    """Abstract class for qbraid program wrapper objects.

    Note: The program wrapper object keeps track of abstract parameters and qubits using an
    intermediate representation. Qubits are stored simplhy as integers. All other objects are
    transpiled directly when the :meth:`~qbraid.transpiler.QuantumProgramtWrapper.transpile`
    method is called.

    """

    def __init__(self, program: "qbraid.QPROGRAM"):
        self._program = program
        self._qubits = []
        self._num_qubits = 0
        self._num_clbits = 0
        self._depth = 0
        self._params = []
        self._input_param_mapping = {}
        self._package = None

    @property
    def program(self) -> "qbraid.QPROGRAM":
        """Return the underlying quantum program that has been wrapped."""
        return self._program

    @property
    def qubits(self) -> List[int]:
        """Return the qubits acted upon by the operations in this circuit"""
        return self._qubits

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits in the circuit."""
        return self._num_qubits

    @property
    def num_clbits(self) -> int:
        """Return the number of classical bits in the circuit."""
        return self._num_clbits

    @property
    def depth(self) -> int:
        """Return the circuit depth (i.e., length of critical path)."""
        return self._depth

    @property
    def params(self) -> Optional[list]:
        """Return the circuit parameters. Defaults to None."""
        return self._params

    @property
    def input_param_mapping(self) -> dict:
        """Return the input parameter mapping. Defaults to None."""
        return self._input_param_mapping

    @property
    def package(self) -> str:
        """Return the original package of the wrapped circuit."""
        return self._package

    def transpile(self, conversion_type: str) -> "qbraid.QPROGRAM":
        r"""Transpile a qbraid quantum program wrapper object to quantum
        program object of type specified by ``conversion_type``.

        Args:
            conversion_type: a supported quantum frontend package.
                Must be one of :data:`~qbraid.QPROGRAM_LIBS`.

        Raises:
            PackageValueError: If ``conversion_type`` is not one of
                :data:`~qbraid.QPROGRAM_LIBS`.
            CircuitConversionError: If the input quantum program could not be
                converted to a program of type ``conversion_type``.

        Returns:
            :data:`~qbraid.QPROGRAM`: supported quantum program object

        """
        if conversion_type == self.package:
            return self.program
        if conversion_type in QPROGRAM_LIBS:
            try:
                cirq_circuit, _ = convert_to_cirq(self.program)
            except Exception as err:
                raise CircuitConversionError(
                    "Quantum program could not be converted to Cirq. "
                    "This may be because the program contains gates or operations"
                    "not yet supported by the qBraid transpiler."
                ) from err
            try:
                converted_program = convert_from_cirq(cirq_circuit, conversion_type)
            except Exception as err:
                raise CircuitConversionError(
                    f"Circuit could not be converted from Cirq to "
                    f"program of type {conversion_type}."
                ) from err

            return converted_program

        raise PackageValueError(conversion_type)

    def draw(self, package: str = "cirq", output: Optional[str] = None, **kwrags):
        """draw circuit"""
        return circuit_drawer(self.transpile(package), output, **kwrags)
