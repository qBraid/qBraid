# Copyright (C) 2021 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tests to make sure qbraid.transpiler works without optional packages like Qiskit,
pyQuil, etc.

Ideally these tests should touch all of qbraid.transpiler except for
qbraid.transpiler.[package], where [package] is any supported package that
interfaces with the qbraid (see qbraid.transpiler.SUPPORTED_PROGRAM_TYPES).
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


# TODO: More tests wanted!
