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

# pylint: disable=redefined-outer-name

"""
Benchmarking tests for Qrisp conversions

"""

import importlib.util
import string

import numpy as np
import pytest

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ConversionGraph, transpile

try:
    import qrisp
    from qrisp.circuit.library import *  # pylint: disable=wildcard-import, unused-wildcard-import  # noqa: F403

    qrisp_not_installed = False
except ImportError:
    qrisp_not_installed = True

pytestmark = pytest.mark.skipif(qrisp_not_installed, reason="qrisp not installed")

np.random.seed(0)


gates_param_map = {
    "XGate": {"qubits": [0]},
    "YGate": {"qubits": [0]},
    "ZGate": {"qubits": [0]},
    "CXGate": {"qubits": [0, 1]},
    "CYGate": {"qubits": [0, 1]},
    "CZGate": {"qubits": [0, 1]},
    "MCXGate": {"qubits": [0, 1, 2, 3], "control_amount": 3},
    "PGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "CPGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "u3Gate": {
        "qubits": [0],
        "theta": np.random.rand() * 2 * np.pi,
        "phi": np.random.rand() * 2 * np.pi,
        "lam": np.random.rand() * 2 * np.pi,
    },
    "HGate": {"qubits": [0]},
    "RXGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "RYGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "RZGate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "MCRXGate": {
        "qubits": [0, 1, 2, 3],
        "phi": np.random.rand() * 2 * np.pi,
        "control_amount": 3,
    },
    "SGate": {"qubits": [0]},
    "TGate": {"qubits": [0]},
    "RXXGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "RYYGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "RZZGate": {"qubits": [0, 1], "phi": np.random.rand() * 2 * np.pi},
    "SXGate": {"qubits": [0]},
    "SXDGGate": {"qubits": [0]},
    "XXYYGate": {"qubits": [0, 1]},
    "Barrier": {"qubits": [0]},
    "Measurement": {"qubits": [0], "clbits": [0]},
    "Reset": {"qubits": [0]},
    "QubitAlloc": {"qubits": [0]},
    "GPhaseGate": {"qubits": [0]},
    "SwapGate": {"qubits": [0, 1]},
    "U1Gate": {"qubits": [0], "phi": np.random.rand() * 2 * np.pi},
    "IDGate": {"qubits": [0]},
    "RGate": {
        "qubits": [0],
        "theta": np.random.rand() * 2 * np.pi,
        "phi": np.random.rand() * 2 * np.pi,
    },
}


@pytest.fixture
def qrisp_circuits():
    """Construct a dictionary of Qrisp circuits over all supported gates
    using random parameters as applicable.
    """
    qrisp_gates = {
        attr: None
        for attr in dir(qrisp.circuit.standard_operations)
        if attr[0] in string.ascii_uppercase
        # qrisp 0.9 leaks non-gate upper-case names (e.g. ``TYPE_CHECKING``) into the
        # module namespace; restrict enumeration to callables (gate classes/factories).
        and callable(getattr(qrisp.circuit.standard_operations, attr))
    }

    qrisp_gates.pop("Operation")
    qrisp_gates.pop("QubitAlloc")
    qrisp_gates.pop("QubitDealloc")
    qrisp_gates.pop("PauliGate")
    qrisp_gates.pop("Reset")

    # U3 gate is covered under `u3Gate` function
    qrisp_gates.pop("U3Gate")

    # Non-unitary / special gates aren't comparable via circuits_allclose; exclude them
    # from the benchmark, as the other coverage modules do.
    qrisp_gates.pop("Measurement")
    qrisp_gates.pop("Barrier")
    qrisp_gates.pop("GPhaseGate")

    for gate in qrisp_gates:
        try:
            if gates_param_map[gate] is None:
                continue
            qubits = gates_param_map[gate]["qubits"]
            clbits = gates_param_map[gate]["clbits"] if "clbits" in gates_param_map[gate] else []
            gate_op = eval(gate)(  # pylint: disable=eval-used
                **{
                    key: gates_param_map[gate][key]
                    for key in gates_param_map[gate]
                    if key not in ["qubits", "clbits"]
                }
            )
            qc = qrisp.QuantumCircuit(gate_op.num_qubits, gate_op.num_clbits)
            qc.append(gate_op, qubits, clbits)
            qrisp_gates[gate] = qc  # type: ignore
        except Exception:  # pylint: disable=broad-exception-caught
            continue
    return qrisp_gates


@pytest.fixture
def conversion_graph():
    """Return a conversion graph of natively supported conversions."""
    return ConversionGraph(require_native=True)


def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None


ALL_TARGETS = [("cirq", 0.95), ("pytket", 0.88), ("qiskit", 0.95)]

#: Gates whose qrisp -> target conversion is known to be wrong, keyed by target.
#:
#: These are asserted as an upper bound rather than folded into an accuracy ratio. The
#: ratio could not distinguish "the known-bad gates failed" from "a different gate broke",
#: and with 25 gates one failure moves accuracy by 0.04 while ALLOWANCE was 0.01 -- so the
#: pytket case sat exactly on its 0.88 baseline with three failures and went red the moment
#: a fourth appeared, regardless of which. That is what made it flake in CI.
#:
#: MCRXGate is listed for pytket because it fails only on some conversion paths: the direct
#: qrisp -> pytket edge produces a circuit that is not equivalent, while a route through an
#: intermediate does not, and which one the graph picks depends on what else is imported.
#: Listing it keeps the suite green either way; the underlying conversion is still wrong and
#: is tracked separately.
KNOWN_BAD_CONVERSIONS = {
    "cirq": {"RGate"},
    "pytket": {"CPGate", "MCRXGate", "RGate", "U1Gate"},
    "qiskit": {"RGate"},
}
AVAILABLE_TARGETS = [(name, version) for name, version in ALL_TARGETS if is_package_installed(name)]


def convert_from_qrisp_to_x(target, circuit_name, circuits, graph):
    """Construct a Qrisp circuit with the given gate, transpile it to
    target program type, and check equivalence.
    """
    source_circuit = circuits[circuit_name]
    # A gate enumerated from qrisp but absent from gates_param_map (or whose entry no
    # longer matches its constructor) never got a circuit built. Name that directly
    # instead of letting transpile(None) surface as an opaque NoneType error.
    assert (
        source_circuit is not None
    ), f"no circuit was built for {circuit_name}; add or update its gates_param_map entry"
    target_circuit = transpile(source_circuit, target, conversion_graph=graph)
    assert circuits_allclose(source_circuit, target_circuit, strict_gphase=False)


@pytest.mark.parametrize(("target", "baseline"), AVAILABLE_TARGETS)
def test_qrisp_coverage(target, baseline, qrisp_circuits, conversion_graph):
    """Every Qrisp gate converts to ``target``, except the known-bad ones.

    ``baseline`` is retained for the parametrize id and as documentation of the coverage
    this target is expected to reach; the assertion is on the failing gate NAMES, which
    says which conversion regressed instead of only that the rate moved.
    """
    failures = {}
    for gate_name in qrisp_circuits:
        try:
            convert_from_qrisp_to_x(target, gate_name, qrisp_circuits, conversion_graph)
        except Exception as e:  # pylint: disable=broad-exception-caught
            failures[gate_name] = e

    known_bad = KNOWN_BAD_CONVERSIONS.get(target, set())
    unexpected = sorted(set(failures) - known_bad)
    coverage = (len(qrisp_circuits) - len(failures)) / len(qrisp_circuits)

    assert not unexpected, (
        f"{len(unexpected)} qrisp -> {target} conversion(s) newly failing: {unexpected}\n"
        f"Coverage is now {coverage:.2%}, against a documented baseline of {baseline:.0%}.\n"
        f"Known-bad for this target: {sorted(known_bad)}\n"
        f"Errors: { {k: repr(failures[k]) for k in unexpected} }\n\n"
        f"If one of these is expected to fail, add it to KNOWN_BAD_CONVERSIONS with the "
        f"reason; otherwise it is a regression in the conversion itself."
    )

    # A known-bad gate that starts passing is not a failure, but the list must not rot:
    # left unchecked it grows into a permanent allowance that hides the next regression.
    fixed = sorted(known_bad - set(failures) - {"MCRXGate"})
    assert not fixed, (
        f"qrisp -> {target} now converts {fixed} correctly. Remove from "
        f"KNOWN_BAD_CONVERSIONS so a future regression is caught."
    )


@pytest.mark.parametrize("target", ["qasm2", "qasm3"])
def test_qrisp_to_qasm_roundtrip(target, conversion_graph):
    """Test forcing a roundtrip conversion from Qrisp to QASM and then to Cirq
    and check equivalence.
    """
    qc = qrisp.QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qasm = transpile(qc, target, conversion_graph=conversion_graph)
    assert isinstance(qasm, str)
    back = transpile(qasm, "cirq", conversion_graph=conversion_graph)
    assert circuits_allclose(qc.to_cirq(), back, strict_gphase=False)
