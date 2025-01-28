# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing top-level qbraid job loader functionality
utilizing entrypoints via ``importlib``

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

from qbraid._entrypoints import get_entrypoints, load_entrypoint
from qbraid.exceptions import QbraidError

if TYPE_CHECKING:
    from qbraid.runtime import QuantumJob
    from qbraid.runtime.aws import BraketQuantumTask
    from qbraid.runtime.azure import AzureQuantumJob
    from qbraid.runtime.ibm import QiskitJob
    from qbraid.runtime.ionq import IonQJob
    from qbraid.runtime.native import QbraidJob
    from qbraid.runtime.oqc import OQCJob


class JobLoaderError(QbraidError):
    """Raised when an error occurs while loading a quantum job."""


@overload
def load_job(job_id: str, provider: Literal["native", "qbraid"], **kwargs) -> QbraidJob: ...


@overload
def load_job(job_id: str, provider: Literal["aws", "braket"], **kwargs) -> BraketQuantumTask: ...


@overload
def load_job(job_id: str, provider: Literal["ibm", "qiskit"], **kwargs) -> QiskitJob: ...


@overload
def load_job(job_id: str, provider: Literal["azure"], **kwargs) -> AzureQuantumJob: ...


@overload
def load_job(job_id: str, provider: Literal["ionq"], **kwargs) -> IonQJob: ...


@overload
def load_job(job_id: str, provider: Literal["oqc"], **kwargs) -> OQCJob: ...


@overload
def load_job(job_id: str, provider: str, **kwargs) -> QuantumJob: ...


def load_job(job_id: str, provider: str = "qbraid", **kwargs) -> QuantumJob:
    """Load a quantum job object from a supported provider.

    Args:
        job_id: The provider-specific job identifier.
        provider: The name of the provider module within in the ``qbraid.runtime`` package.

    Returns:
        QuantumJob: A quantum job object of the inferred subclass.

    Raises:
        JobLoaderError: If the job cannot be loaded.
    """
    provider_aliases = {"native": "qbraid", "qiskit": "ibm", "braket": "aws"}

    provider_module = provider_aliases.get(provider.lower(), provider).lower()

    try:
        job_class = load_entrypoint("jobs", provider_module)
    except Exception as err:
        raise JobLoaderError(
            f"Error loading QuantumJob sub-class for provider '{provider}'."
        ) from err

    job_instance = job_class(job_id, **kwargs)

    return job_instance


def get_providers() -> list[str]:
    """Return a list of supported quantum job providers.

    Returns:
        list[str]: A list of supported quantum job providers.
    """
    entry_points = get_entrypoints("jobs")
    return sorted(entry_points.keys())
