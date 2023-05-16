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
Module containing qasm programs used for testing

"""
import os

QASMType = str
current_dir = os.path.dirname(os.path.abspath(__file__))


def qasm_bell() -> QASMType:
    """Returns QASM2 bell circuit"""
    return open(os.path.join(current_dir, "bell.qasm"), mode="r", encoding="utf-8").read()


def qasm_shared15():
    """Returns QASM2 for qBraid `TestSharedGates`."""
    return open(os.path.join(current_dir, "shared_15.qasm"), mode="r", encoding="utf-8").read()
