# Copyright 2023 qBraid
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
Unit tests for converting QASM code to Amazon Braket code

"""

import os
import sys

from qbraid.interface.qbraid_cirq.circuits import cirq_shared15
from qbraid.transpiler.code.qasm_to_braket import qasm_to_braket_code

test_code = """
import qbraid
from qbraid.interface import convert_to_contiguous, circuits_allclose
cirq_circuit = qbraid.circuit_wrapper(circuit).transpile("cirq")
cirq_flipped = convert_to_contiguous(cirq_circuit, rev_qubits=True)
all_close = circuits_allclose(circuit, cirq_circuit)
all_close_flipped = circuits_allclose(circuit, cirq_flipped)
passed = all_close or all_close_flipped
print(passed)
"""


def test_qasm_to_braket_code(capfd):
    cirq_circuit = cirq_shared15()
    qasm_str = cirq_circuit.to_qasm()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(current_dir, "_braket_out.py")
    if os.path.isfile(output_file):
        os.remove(output_file)
    qasm_to_braket_code(qasm_str=qasm_str, output_file=output_file)

    # write test code to output file
    braket_out = open(output_file, "a")
    braket_out.writelines(test_code)
    braket_out.close()

    os.system(f"{sys.executable} {output_file}")
    out, err = capfd.readouterr()
    assert out == "True\n"
    assert len(err) == 0
    os.remove(output_file)
