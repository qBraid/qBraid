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
Module containing PyQIR quantum programs used for testing

"""

from pyqir import BasicQisBuilder, SimpleModule

def qir_bell() -> BasicQisBuilder:
    """Returns QIR bell circuit"""
    bell = SimpleModule("bell", num_qubits=2, num_results=0)
    qis = BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.cx(bell.qubits[0], bell.qubits[1])

    return qis
