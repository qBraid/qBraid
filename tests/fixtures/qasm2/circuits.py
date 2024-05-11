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

QASMType = str
current_dir = os.path.dirname(os.path.abspath(__file__))


def _read_qasm_file(filename: str) -> QASMType:
    """Reads a qasm file from the qasm_lib directory"""
    return open(os.path.join(current_dir, filename), mode="r", encoding="utf-8").read()


def qasm2_bell() -> QASMType:
    """Returns OpenQASM2 bell circuit"""
    return _read_qasm_file("bell.qasm")


def qasm2_shared15() -> QASMType:
    """Returns OpenQASM2 15 gate test circuit."""
    return _read_qasm_file("shared15.qasm")


def qasm2_cirq_shared15() -> QASMType:
    """Returns OpenQASM 2 15 gate test circuit with no gate defs."""
    return _read_qasm_file("shared15_cirq.qasm")
