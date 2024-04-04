# Copyright (C) 2023 qBraid
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
   get_devices
   get_jobs


Classes
--------

.. autosummary::
   :toctree: ../stubs/

   LazyLoader


Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError

"""
import sys

from ._about import about
from ._import import LazyLoader
from ._version import __version__
from .exceptions import QbraidError
from .get_devices import get_devices
from .get_jobs import get_jobs

if "sphinx" in sys.modules:
    from . import compiler, interface, programs, providers, transpiler, visualization
else:
    compiler = LazyLoader("compiler", globals(), "qbraid.compiler")
    interface = LazyLoader("interface", globals(), "qbraid.interface")
    programs = LazyLoader("programs", globals(), "qbraid.programs")
    providers = LazyLoader("providers", globals(), "qbraid.providers")
    transpiler = LazyLoader("transpiler", globals(), "qbraid.transpiler")
    visualization = LazyLoader("visualization", globals(), "qbraid.visualization")


__all__ = [
    "about",
    "compiler",
    "get_devices",
    "get_jobs",
    "interface",
    "LazyLoader",
    "programs",
    "providers",
    "QbraidError",
    "transpiler",
    "visualization",
]
