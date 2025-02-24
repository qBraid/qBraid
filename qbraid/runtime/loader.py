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
    from qbraid.runtime import QuantumJob, QuantumProvider
    from qbraid.runtime.aws import BraketProvider, BraketQuantumTask
    from qbraid.runtime.azure import AzureQuantumJob, AzureQuantumProvider
    from qbraid.runtime.ibm import QiskitJob, QiskitRuntimeProvider
    from qbraid.runtime.ionq import IonQJob, IonQProvider
    from qbraid.runtime.native import QbraidJob, QbraidProvider
    from qbraid.runtime.oqc import OQCJob, OQCProvider


class JobLoaderError(QbraidError):
    """Raised when an error occurs while loading a quantum job."""


class ProviderLoaderError(QbraidError):
    """Raised when an error occurs while loading a quantum provider."""


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
    entry_points = get_entrypoints("providers")
    return sorted(entry_points.keys())


@overload
def load_provider(provider_name: Literal["native", "qbraid"], **kwargs) -> QbraidProvider: ...


@overload
def load_provider(provider_name: Literal["aws", "braket"], **kwargs) -> BraketProvider: ...


@overload
def load_provider(provider_name: Literal["ibm", "qiskit"], **kwargs) -> QiskitRuntimeProvider: ...


@overload
def load_provider(provider_name: Literal["azure"], **kwargs) -> AzureQuantumProvider: ...


@overload
def load_provider(provider_name: Literal["ionq"], **kwargs) -> IonQProvider: ...


@overload
def load_provider(provider_name: Literal["oqc"], **kwargs) -> OQCProvider: ...


@overload
def load_provider(provider_name: str, **kwargs) -> QuantumProvider: ...


def load_provider(provider_name: str = "qbraid", **kwargs) -> QuantumProvider:
    """Load a quantum provider object from a supported qBraid runtime module.

    Args:
        provider_name: The name of the provider module within in the
            ``qbraid.runtime`` package. Defaults to "qbraid".

    Returns:
        QuantumProvider: A quantum provider object of the inferred subclass.

    Raises:
        ProviderLoaderError: If the provider subclass cannot be loaded.
    """
    provider_aliases = {"native": "qbraid", "qiskit": "ibm", "braket": "aws"}

    provider_module = provider_aliases.get(provider_name, provider_name).lower()

    try:
        provider_class = load_entrypoint("providers", provider_module)
    except Exception as err:
        raise ProviderLoaderError(
            f"Error loading QuantumProvider sub-class for provider '{provider_name}'."
        ) from err

    provider_instance = provider_class(**kwargs)

    return provider_instance
