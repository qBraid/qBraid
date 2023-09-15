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
Module for calculating unitary of quantum circuit/program

"""
from copy import deepcopy
from typing import TYPE_CHECKING, Union

import numpy as np
from cirq import Circuit, GridQubit, LineQubit, MeasurementGate, NamedQubit, Qid
from cirq.testing import assert_allclose_up_to_global_phase

from qbraid.exceptions import QbraidError

QUBIT = Union[LineQubit, GridQubit, NamedQubit, Qid]

if TYPE_CHECKING:
    import qbraid


class UnitaryCalculationError(QbraidError):
    """Class for exceptions raised during unitary calculation"""


def circuits_allclose(  # pylint: disable=too-many-arguments
    circuit0: "qbraid.QPROGRAM",
    circuit1: "qbraid.QPROGRAM",
    index_contig: bool = False,
    allow_rev_qubits: bool = False,
    strict_gphase: bool = False,
    atol: float = 1e-7,
) -> bool:
    """Check if quantum program unitaries are equivalent.

    Args:
        circuit0 (:data:`~qbraid.QPROGRAM`): First quantum program to compare
        circuit1 (:data:`~qbraid.QPROGRAM`): Second quantum program to compare
        index_contig: If True, calculates circuit unitaries using contiguous qubit indexing.
        allow_rev_qubits: Whether to count identical circuits with reversed qubit ordering
            as equivalent.
        strict_gphase: If False, disregards global phase when verifying
            equivalence of the input circuit's unitaries.
        atol: Absolute tolerance parameter for np.allclose function.

    Returns:
        True if the input circuits pass unitary equality check

    """
    from qbraid import circuit_wrapper  # pylint: disable=import-outside-toplevel

    def unitary_equivalence_check(unitary0, unitary1, unitary_rev=None):
        if strict_gphase:
            return np.allclose(unitary0, unitary1) or (
                allow_rev_qubits and np.allclose(unitary0, unitary_rev)
            )
        try:
            assert_allclose_up_to_global_phase(unitary0, unitary1, atol=atol)
        except AssertionError:
            if allow_rev_qubits:
                try:
                    assert_allclose_up_to_global_phase(unitary0, unitary_rev, atol=atol)
                except AssertionError:
                    return False
            else:
                return False
        return True

    program0 = circuit_wrapper(circuit0)
    program1 = circuit_wrapper(circuit1)

    if index_contig:
        program0.convert_to_contiguous()
        program1.convert_to_contiguous()

    unitary0 = program0.unitary()
    unitary1 = program1.unitary()
    unitary_rev = program1.unitary_rev_qubits()

    return unitary_equivalence_check(unitary0, unitary1, unitary_rev)


def _equal(
    circuit_one: Circuit,
    circuit_two: Circuit,
    require_qubit_equality: bool = False,
    require_measurement_equality: bool = False,
) -> bool:
    """Returns True if the circuits are equal, else False.

    Args:
        circuit_one: Input circuit to compare to circuit_two.
        circuit_two: Input circuit to compare to circuit_one.
        require_qubit_equality: Requires that the qubits be equal
            in the two circuits.
        require_measurement_equality: Requires that measurements are equal on
            the two circuits, meaning that measurement keys are equal.

    Note:
        If set(circuit_one.all_qubits()) = {LineQubit(0)},
        then set(circuit_two_all_qubits()) must be {LineQubit(0)},
        else the two are not equal.
        If True, the qubits of both circuits must have a well-defined ordering.
    """
    # Make a deepcopy only if it's necessary
    if not (require_qubit_equality and require_measurement_equality):
        circuit_one = deepcopy(circuit_one)
        circuit_two = deepcopy(circuit_two)

    if not require_qubit_equality:
        # Transform the qubits of circuit one to those of circuit two
        qubit_map = dict(
            zip(
                sorted(circuit_one.all_qubits()),
                sorted(circuit_two.all_qubits()),
            )
        )
        circuit_one = circuit_one.transform_qubits(lambda q: qubit_map[q])

    if not require_measurement_equality:
        for circ in (circuit_one, circuit_two):
            measurements = [
                (moment, op)
                for moment, op, _ in circ.findall_operations_with_gate_type(MeasurementGate)
            ]
            circ.batch_remove(measurements)
    return circuit_one == circuit_two
