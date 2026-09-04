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
Unit tests for loading jobs using entrypoints

"""

import ast
from pathlib import Path

import pytest

import qbraid.runtime
import qbraid.runtime.loader as runtime_loader
from qbraid._entrypoints import get_entrypoints
from qbraid.runtime import (
    PROVIDERS,
    JobLoaderError,
    OpenQuantumJob,
    OpenQuantumProvider,
    ProviderLoaderError,
    QbraidProvider,
    get_providers,
    load_job,
    load_provider,
)

from ._resources import JOB_DATA_QIR


@pytest.fixture
def job_id():
    """Mock job data for testing"""
    return JOB_DATA_QIR["jobQrn"]


def test_load_job(mock_client, job_id):
    """Test loading a job using entrypoints"""
    job = load_job(job_id, "qbraid", client=mock_client)
    assert job.id == job_id


def test_load_openquantum_job(job_id):
    """Test loading an Open Quantum job through its entry point."""
    job = load_job(job_id, "openquantum", session=object())
    assert isinstance(job, OpenQuantumJob)


def test_load_job_error(job_id):
    """Test that JobLoaderError is raised when loading a job fails."""
    provider = "fake_provider"

    with pytest.raises(
        JobLoaderError,
        match=f"Error loading QuantumJob sub-class for provider '{provider}'.",
    ):
        load_job(job_id, provider)


def test_get_providers():
    """Test getting all available providers."""
    providers = get_providers()
    assert (
        providers
        == PROVIDERS
        == [
            "aqt",
            "aws",
            "azure",
            "ibm",
            "ionq",
            "openquantum",
            "oqc",
            "origin",
            "pasqal",
            "qbraid",
            "qperfect",
            "quantinuum",
            "qudora",
            "rigetti",
        ]
    )


def test_runtime_modules_have_provider_and_job_entrypoints():
    """Test that every built-in runtime provider can be discovered."""
    runtime_path = Path(qbraid.runtime.__file__).parent
    runtime_modules = {
        path.name
        for path in runtime_path.iterdir()
        if path.is_dir() and (path / "__init__.py").is_file()
    }
    expected_entrypoints = {
        "qbraid" if module == "native" else module for module in runtime_modules
    }

    assert expected_entrypoints <= set(get_entrypoints("providers"))
    assert expected_entrypoints <= set(get_entrypoints("jobs"))


def _literal_overload_names(function_name: str, parameter_name: str) -> set[str]:
    """Return the string literals accepted by a loader's overloads."""
    loader_tree = ast.parse(Path(runtime_loader.__file__).read_text(encoding="utf-8"))
    names: set[str] = set()

    for node in loader_tree.body:
        if not isinstance(node, ast.FunctionDef) or node.name != function_name:
            continue
        if not any(
            isinstance(decorator, ast.Name) and decorator.id == "overload"
            for decorator in node.decorator_list
        ):
            continue

        parameters = dict(zip((arg.arg for arg in node.args.args), node.args.args))
        annotation = parameters[parameter_name].annotation
        if not (
            isinstance(annotation, ast.Subscript)
            and isinstance(annotation.value, ast.Name)
            and annotation.value.id == "Literal"
        ):
            continue

        values = (
            annotation.slice.elts if isinstance(annotation.slice, ast.Tuple) else [annotation.slice]
        )
        names.update(
            value.value
            for value in values
            if isinstance(value, ast.Constant) and isinstance(value.value, str)
        )

    return names


@pytest.mark.parametrize(
    ("function_name", "parameter_name", "entrypoint_group"),
    [
        ("load_provider", "provider_name", "providers"),
        ("load_job", "provider", "jobs"),
    ],
)
def test_loader_overloads_match_entrypoints(function_name, parameter_name, entrypoint_group):
    """Test that loader overloads cover every registered provider and legacy alias."""
    legacy_aliases = {"braket", "native", "qiskit"}
    expected_names = set(get_entrypoints(entrypoint_group)) | legacy_aliases

    assert _literal_overload_names(function_name, parameter_name) == expected_names


def test_load_provider(mock_client):
    """Test loading a provider using entrypoints"""
    provider = load_provider("qbraid", client=mock_client)
    assert isinstance(provider, QbraidProvider)


def test_load_openquantum_provider():
    """Test loading the Open Quantum provider through its entry point."""
    provider = load_provider("openquantum", client_id="client-id", client_secret="client-secret")
    assert isinstance(provider, OpenQuantumProvider)


def test_load_provider_error():
    """Test that ProviderLoaderError is raised when loading a provider fails."""
    provider_name = "fake_provider"

    with pytest.raises(
        ProviderLoaderError,
        match=f"Error loading QuantumProvider sub-class for provider '{provider_name}'.",
    ):
        load_provider(provider_name)
