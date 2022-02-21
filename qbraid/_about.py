# Copyright (C) 2020 Unitary Fund
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

"""Information about the qbraid and dependencies."""
import platform

from cirq import __version__ as cirq_version
from numpy import __version__ as numpy_version
from scipy import __version__ as scipy_version

import qbraid


def about() -> None:
    """Displays information about the qbraid.transpiler2, core/optional
    packages, and Python version/platform information.
    """
    try:
        from pyquil import __version__ as pyquil_version
    except ImportError:
        pyquil_version = "Not installed"
    try:
        from qiskit import __qiskit_version__  # pragma: no cover

        qiskit_version = __qiskit_version__["qiskit"]  # pragma: no cover
    except ImportError:
        qiskit_version = "Not installed"
    try:
        from braket._sdk import __version__ as braket_version
    except ImportError:
        braket_version = "Not installed"

    about_str = f"""
A Python toolkit for building and executing quantum programs
=============================================================

Version:\t{qbraid.__version__}

Core Dependencies
-----------------
Cirq Version:\t{cirq_version}
NumPy Version:\t{numpy_version}
SciPy Version:\t{scipy_version}

Optional Dependencies
---------------------
PyQuil Version:\t{pyquil_version}
Qiskit Version:\t{qiskit_version}
Braket Version:\t{braket_version}

Python Version:\t{platform.python_version()}
Platform Info:\t{platform.system()} ({platform.machine()})"""
    print(about_str)


if __name__ == "__main__":
    about()
