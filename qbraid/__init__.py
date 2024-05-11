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
This top level module contains the main qBraid public functionality.

.. currentmodule:: qbraid

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    about
    configure_logging
    filterwarnings
    check_warn_version_update

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError

"""
import sys

from ._about import about
from ._compat import check_warn_version_update, configure_logging, filterwarnings
from ._import import LazyLoader
from ._version import __version__
from .exceptions import QbraidError

if "sphinx" in sys.modules:
    from . import interface, programs, runtime, transforms, transpiler, visualization
else:
    transforms = LazyLoader("transforms", globals(), "qbraid.transforms")
    interface = LazyLoader("interface", globals(), "qbraid.interface")
    programs = LazyLoader("programs", globals(), "qbraid.programs")
    runtime = LazyLoader("runtime", globals(), "qbraid.runtime")
    transpiler = LazyLoader("transpiler", globals(), "qbraid.transpiler")
    visualization = LazyLoader("visualization", globals(), "qbraid.visualization")


__all__ = [
    "about",
    "configure_logging",
    "check_warn_version_update",
    "filterwarnings",
    "interface",
    "programs",
    "runtime",
    "QbraidError",
    "transforms",
    "transpiler",
    "visualization",
]
