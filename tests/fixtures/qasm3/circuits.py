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
