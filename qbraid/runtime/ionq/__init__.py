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
Mdule submiting and managing jobs through the IonQ API.

.. currentmodule:: qbraid.runtime.ionq

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    IonQSession
    IonQProvider
    IonQDevice
    IonQJob

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

    IonQJobError

"""
from .device import IonQDevice
from .job import IonQJob, IonQJobError
from .provider import IonQProvider, IonQSession

__all__ = [
    "IonQDevice",
    "IonQProvider",
    "IonQSession",
    "IonQJob",
    "IonQJobError",
]
