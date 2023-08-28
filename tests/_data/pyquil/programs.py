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
Module containing pyQuil programs used for testing

"""
from pyquil import Program
from pyquil.gates import CNOT, H


def pyquil_bell() -> Program:
    """Returns pyQuil bell circuit"""
    program = Program()
    program += H(0)
    program += CNOT(0, 1)
    return program
