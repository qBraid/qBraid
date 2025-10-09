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
Unit tests for submissions to AWS SV1, DM1, TN1 via qBraid native runtime.

"""

from qbraid.runtime.native.provider import _serialize_program


def test_braket_circuit_to_json(braket_circuit, qasm3_circuit):
    """Test conversion of Braket circuit to JSON."""
    qasm_json = _serialize_program(braket_circuit)
    assert len(qasm_json) == 1
    assert qasm_json.keys() == {"openQasm"}
    assert qasm_json["openQasm"].strip() == qasm3_circuit.strip()
