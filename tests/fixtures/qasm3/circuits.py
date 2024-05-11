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
Module containing qasm programs used for testing

"""
import os

import openqasm3

QASMType = str
current_dir = os.path.dirname(os.path.abspath(__file__))


def _read_qasm_file(filename: str) -> QASMType:
    """Reads a qasm file from the qasm_lib directory"""
    return open(os.path.join(current_dir, filename), mode="r", encoding="utf-8").read()


def qasm3_bell() -> QASMType:
    """Returns OpenQASM3 bell circuit"""
    return _read_qasm_file("bell.qasm")


def qasm3_shared15() -> QASMType:
    """Returns OpenQASM3 15 gate test circuit."""
    return _read_qasm_file("shared15.qasm")


def openqasm3_bell():
    """Returns OpenQASM3 AST representing bell program"""
    qasm_str = qasm3_bell()
    return openqasm3.parse(qasm_str)


def openqasm3_shared15():
    """Returns OpenQASM3 AST representing 15 gate test program"""
    qasm_str = qasm3_shared15()
    return openqasm3.parse(qasm_str)
