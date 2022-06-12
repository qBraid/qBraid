"""
Tests to make sure qbraid.transpiler works without optional packages
like Qiskit,pyQuil, etc.

Ideally these tests should touch all of qbraid.transpiler except for
qbraid.transpiler.[package], where [package] is any supported package that
interfaces with the qbraid (see qbraid.transpiler.SUPPORTED_PROGRAM_TYPES).

TODO: Maybe remove this module since in the current state of the SDK,
these tests don't really apply.

"""
from abc import ABCMeta


def test_import():
    """Simple test that the qbraid.transpiler can be imported without any
    (or all) supported program types."""
    import qbraid

    if isinstance(qbraid.QPROGRAM, ABCMeta):
        pass  # If only Cirq is installed, QPROGRAM is not a typing.Union.
    else:
        assert (
            1  # cirq.Circuit is always supported.
            <= len(qbraid.QPROGRAM.__args__)  # All installed types.
            <= len(qbraid.SUPPORTED_PROGRAM_TYPES.keys())  # All types.
        )
