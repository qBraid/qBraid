# Copyright 2026 qBraid
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

# pylint: disable=no-name-in-module

# The above disable is necessary because the qcs_sdk.* modules load from Rust extension bindings
# (__file__ is None for submodules), so pylint/astroid can’t reliably introspect exported names
# and emits E0611 false positives.
"""
Module defining Rigetti device class
"""

from __future__ import annotations

import socket
from multiprocessing.pool import ThreadPool
from typing import Any
from urllib.parse import urlparse

import pyquil
from qcs_sdk.client import QCSClient
from qcs_sdk.compiler.quilc import (
    QuilcClient,
    TargetDevice,
    compile_program,
)
from qcs_sdk.qpu import ListQuantumProcessorsError, list_quantum_processors
from qcs_sdk.qpu.api import ExecutionOptions, SubmissionError
from qcs_sdk.qpu.api import submit as qpu_submit
from qcs_sdk.qpu.isa import GetISAError, get_instruction_set_architecture
from qcs_sdk.qpu.translation import TranslationOptions, translate

from qbraid.runtime import QuantumDevice, TargetProfile
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import RigettiJob, RigettiJobError

# Short timeout (seconds) for the quilc TCP reachability probe so that
# transform() fails fast instead of hanging when the quilc server is down.
_QUILC_PROBE_TIMEOUT_S = 2.0


class RigettiDeviceError(QbraidRuntimeError):
    """Class for errors raised while processing a Rigetti device."""


class RigettiDevice(QuantumDevice):
    """Wraps a single Rigetti QCS quantum processor or simulator."""

    def __init__(
        self,
        profile: TargetProfile,
        qcs_client: QCSClient,
    ):
        """Initialize a RigettiDevice.

        Args:
            profile: A TargetProfile object (constructed by RigettiProvider).
            qcs_client: An authenticated QCSClient used for QCS API calls.

        ``ExecutionOptions`` are not stored on the device. Instead, callers
        pass an ``execution_options=`` kwarg to ``run()`` / ``submit()`` so
        each job can use a different connection strategy without forcing
        re-instantiation of the device.
        """
        super().__init__(profile=profile)
        self._qcs_client = qcs_client
        self._compiler_options = None

    @property
    def client(self) -> QCSClient:
        """Return the QCSClient associated with this device."""
        return self._qcs_client

    def __str__(self) -> str:
        """String representation of the RigettiDevice object."""
        return f"{self.__class__.__name__}('{self.id}')"

    def status(self) -> DeviceStatus:
        """
        Return the current status of the device.
        """
        try:
            # Otherwise, check if the quantum processor ID is in the list of available processors
            quantum_processor_ids = set(list_quantum_processors(client=self._qcs_client))
            if self.id not in quantum_processor_ids:
                return DeviceStatus.OFFLINE
        except ListQuantumProcessorsError as e:
            raise RigettiDeviceError(  # pylint: disable=bad-exception-cause
                "Failed to retrieve quantum processor list from Rigetti QCS."
            ) from e
        return DeviceStatus.ONLINE

    def _probe_quilc_reachable(self) -> None:
        """Verify that the configured quilc endpoint accepts TCP connections.

        ``compile_program`` will hang indefinitely if quilc is not running,
        which makes ``run()`` look frozen. We perform a short TCP connect
        probe (default 2s) against the host:port from
        ``self._qcs_client.quilc_url`` and raise ``RigettiDeviceError`` on
        failure so users get an immediate, actionable error.
        """
        quilc_url = self._qcs_client.quilc_url
        parsed = urlparse(quilc_url)
        host = parsed.hostname
        port = parsed.port
        if not host or not port:
            # Can't introspect a non-standard URL; skip the probe
            return

        try:
            with socket.create_connection((host, port), timeout=_QUILC_PROBE_TIMEOUT_S):
                pass
        except OSError as exc:
            raise RigettiDeviceError(
                f"quilc not reachable at {quilc_url}. "
                "Start a local quilc server or set QCS_QUILC_ENDPOINT to "
                "an available endpoint before calling run()."
            ) from exc

    @staticmethod
    def _parse_runtime_options(
        runtime_options: dict[str, Any] | None,
    ) -> TranslationOptions | None:
        """Extract known translation keys from a runtime_options dict.

        Recognized translation keys are mapped to ``TranslationOptions.v2()``.
        Unrecognized keys are silently ignored.

        Returns:
            A ``TranslationOptions`` instance, or ``None`` when no recognised
            translation keys are present.
        """
        if not runtime_options:
            return None

        translation_keys = {
            "prepend_default_calibrations",
            "passive_reset_delay_seconds",
            "allow_unchecked_pointer_arithmetic",
            "allow_frame_redefinition",
        }
        translation_kwargs = {
            k: runtime_options[k] for k in translation_keys if k in runtime_options
        }
        return TranslationOptions.v2(**translation_kwargs) if translation_kwargs else None

    def transform(self, run_input: pyquil.Program) -> pyquil.Program:
        """Compile a Quil program into the QPU's native gate set via quilc.

        Per the ``QuantumDevice.transform`` contract, the input/output type
        must match: ``Program`` in, ``Program`` out. Quil-string lowering
        is handled by ``ProgramSpec.serialize`` (configured by the provider
        as ``lambda program: program.out()``).

        ``self._compiler_options`` may be set to a
        ``qcs_sdk.compiler.quilc.CompilerOpts`` instance before calling
        this method to customise quilc behaviour. When ``None`` (the
        default), the qcs_sdk defaults are used.

        Raises:
            RigettiDeviceError: If quilc is unreachable or compilation fails.
        """
        # Fail fast if quilc isn't running, instead of hanging in compile_program.
        self._probe_quilc_reachable()

        compiler_options = getattr(self, "_compiler_options", None)

        try:
            compilation_result = compile_program(
                quil=run_input.out(),
                target=TargetDevice.from_isa(
                    get_instruction_set_architecture(
                        quantum_processor_id=self.id, client=self._qcs_client
                    )
                ),
                client=QuilcClient.new_rpcq(self._qcs_client.quilc_url),
                options=compiler_options,
            )
            compiled_quil = compilation_result.program.to_quil()
        except Exception as e:
            raise RigettiDeviceError(
                f"Compilation failed for quantum processor '{self.id}'. "
                "Ensure the program is valid Quil and that the quilc "
                "compiler is running and accessible"
            ) from e

        return pyquil.Program(compiled_quil)

    def _submit(
        self,
        run_input: str,
        shots: int,
        execution_options: ExecutionOptions | None = None,
        translation_options: TranslationOptions | None = None,
    ) -> RigettiJob:
        """
        Submit a Quil program to the Rigetti QPU.

        Args:
            run_input: A serialized Quil program string (produced by prepare()).
            shots: Number of shots for the job (must be > 0).
            execution_options: Optional ``ExecutionOptions``. ``None`` falls back to
                the qcs_sdk default (Gateway connection strategy).
            translation_options: Optional ``TranslationOptions`` forwarded to
                ``translate()``. ``None`` uses the qcs_sdk default backend.
        """
        if shots is None or shots <= 0:
            raise RigettiJobError(
                f"Shots > 0 must be specified for Rigetti QPU jobs, current value: {shots}."
            )

        try:
            translation_result = translate(
                native_quil=run_input,
                num_shots=shots,
                quantum_processor_id=self.id,
                client=self._qcs_client,
                translation_options=translation_options,
            )
        except Exception as e:
            raise RigettiJobError(
                f"Translation failed for quantum processor '{self.id}'. "
                "Ensure the program uses only native gates for the target QPU."
            ) from e

        try:
            job_id = qpu_submit(
                program=translation_result.program,
                patch_values={},
                quantum_processor_id=self.id,
                client=self._qcs_client,
                execution_options=execution_options,
            )
        except SubmissionError as e:
            raise RigettiJobError("Failed to submit job to Rigetti QCS.") from e

        return RigettiJob(
            job_id=job_id,
            num_shots=shots,
            device=self,
            qcs_client=self._qcs_client,
            ro_sources=translation_result.ro_sources,
            execution_options=execution_options,
        )

    # pylint: disable-next=arguments-differ
    def submit(
        self,
        run_input: str | list[str],
        shots: int,
        execution_options: ExecutionOptions | None = None,
        runtime_options: dict[str, Any] | None = None,
    ) -> RigettiJob | list[RigettiJob]:
        """
        Submit one or more jobs to the Rigetti device.

        Args:
            run_input: A serialized Quil program string (or a list of them).
            shots: Number of shots per job (must be > 0).
            execution_options: Optional ``ExecutionOptions`` applied to every
                job in this submission. ``None`` falls back to the qcs_sdk
                default (Gateway connection strategy).
            runtime_options: Optional dict of translation options forwarded
                to ``translate()``. Recognised keys are
                ``prepend_default_calibrations``,
                ``passive_reset_delay_seconds``,
                ``allow_unchecked_pointer_arithmetic``, and
                ``allow_frame_redefinition``. Unrecognised keys are
                silently ignored.
        """
        translation_options = self._parse_runtime_options(runtime_options)

        if isinstance(run_input, list):
            with ThreadPool(5) as pool:
                quantum_jobs = pool.map(
                    lambda job: self._submit(
                        job,
                        shots,
                        execution_options=execution_options,
                        translation_options=translation_options,
                    ),
                    run_input,
                )
                return quantum_jobs

        return self._submit(
            run_input,
            shots,
            execution_options=execution_options,
            translation_options=translation_options,
        )

    def live_qubits(self) -> list[int]:
        """
        Returns a list of live qubit IDs for the device.
        """
        try:
            isa = get_instruction_set_architecture(
                quantum_processor_id=self.id,
                client=self._qcs_client,
            )
            return [node.node_id for node in isa.architecture.nodes]
        except GetISAError as e:
            raise RigettiDeviceError(
                f"Failed to retrieve ISA for quantum processor '{self.id}'."
            ) from e
