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
# (__file__ is None for submodules), so pylint/astroid can't reliably introspect exported names
# and emits E0611 false positives.

"""
Module defining Rigetti provider class

"""

from __future__ import annotations

import atexit
import logging
import os
import signal
from subprocess import DEVNULL, Popen, TimeoutExpired

import pyquil
from qcs_sdk.client import QCSClient
from qcs_sdk.qpu import list_quantum_processors
from qcs_sdk.qpu.api import ConnectionStrategy, ExecutionOptionsBuilder
from qcs_sdk.qpu.isa import get_instruction_set_architecture

from qbraid.programs.experiment import ExperimentType
from qbraid.programs.spec import ProgramSpec
from qbraid.runtime import QuantumProvider, TargetProfile

from .device import RigettiDevice
from .setup import (
    DEFAULT_GRPC_API_URL,
    DEFAULT_QUILC_PORT,
    DEFAULT_QUILC_URL,
    DEFAULT_QVM_PORT,
    DEFAULT_QVM_URL,
    build_oauth_session,
    build_qcs_client,
    download_forest_sdk,
    find_binary,
    is_port_in_use,
    wait_for_port,
)

logger = logging.getLogger(__name__)


class RigettiProvider(QuantumProvider):
    """
    Implements qBraid's QuantumProvider interface for Rigetti QCS.
    """

    def __init__(
        self,
        qcs_client: QCSClient | None = None,
    ):
        self._qcs_client = qcs_client
        self._quilc_process: Popen | None = None
        self._qvm_process: Popen | None = None
        self._cleanup_registered = False
        self._previous_sigint = None
        self._previous_sigterm = None

        if self._qcs_client is None:
            refresh_token = os.getenv("RIGETTI_REFRESH_TOKEN")
            if not refresh_token:
                raise ValueError(
                    "A Rigetti refresh token is required."
                    " Set it via RIGETTI_REFRESH_TOKEN or pass a QCSClient directly."
                )
            oauth_session = build_oauth_session(
                refresh_token=refresh_token,
                client_id=os.getenv("RIGETTI_CLIENT_ID"),
                issuer=os.getenv("RIGETTI_ISSUER"),
            )
            self._qcs_client = build_qcs_client(
                oauth_session,
                grpc_api_url=os.getenv("QCS_GRPC_ENDPOINT", DEFAULT_GRPC_API_URL),
                quilc_url=os.getenv("QCS_QUILC_ENDPOINT", DEFAULT_QUILC_URL),
                qvm_url=os.getenv("QCS_QVM_ENDPOINT", DEFAULT_QVM_URL),
            )

        self._execution_options = self._build_execution_options()

    def _start_quilc(self, binary_path) -> None:
        """Start quilc as a background RPCQ server on port 5555."""
        logger.info("Starting quilc from %s", binary_path)
        self._quilc_process = Popen(  # pylint: disable=consider-using-with
            [str(binary_path), "-P", "-S", "-p", str(DEFAULT_QUILC_PORT)],
            stdout=DEVNULL,
            stderr=DEVNULL,
        )
        wait_for_port(DEFAULT_QUILC_PORT)
        logger.info("quilc is running (pid=%d)", self._quilc_process.pid)

    def _start_qvm(self, binary_path) -> None:
        """Start qvm as a background server on port 5000."""
        logger.info("Starting qvm from %s", binary_path)
        self._qvm_process = Popen(  # pylint: disable=consider-using-with
            [str(binary_path), "-S"],
            stdout=DEVNULL,
            stderr=DEVNULL,
        )
        wait_for_port(DEFAULT_QVM_PORT)
        logger.info("qvm is running (pid=%d)", self._qvm_process.pid)

    def _cleanup(self) -> None:
        """Terminate processes that *we* started. Never touch external processes."""
        for attr in ("_quilc_process", "_qvm_process"):
            proc = getattr(self, attr, None)
            if proc is None:
                continue
            logger.info("Stopping %s (pid=%d)", attr, proc.pid)
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except TimeoutExpired:
                logger.warning(
                    "Process %d did not exit in time, sending SIGKILL", proc.pid
                )
                proc.kill()
            setattr(self, attr, None)

    def _signal_handler(self, signum: int, _frame) -> None:
        """Handle SIGINT/SIGTERM by cleaning up, then re-raising."""
        self._cleanup()
        if signum == signal.SIGINT:
            raise KeyboardInterrupt
        raise SystemExit(1)

    def _register_cleanup(self) -> None:
        """Register atexit and signal handlers (once)."""
        if self._cleanup_registered:
            return
        atexit.register(self._cleanup)
        self._previous_sigint = signal.getsignal(signal.SIGINT)
        self._previous_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        self._cleanup_registered = True

    def setup(  # pylint: disable=too-many-arguments
        self,
        *,
        quilc_endpoint: str | None = None,
        qvm_endpoint: str | None = None,
        grpc_endpoint: str | None = None,
        start_quilc: bool = True,
        start_qvm: bool = False,
    ) -> None:
        """Manage local quilc / qvm helper processes and register cleanup.

        Credentials are bootstrapped in ``__init__`` and never re-collected
        here. If any of ``quilc_endpoint``, ``qvm_endpoint``, or
        ``grpc_endpoint`` is provided, the underlying ``QCSClient`` is
        rebuilt with those URL overrides while reusing the existing OAuth
        session (so callers do not re-authenticate). URLs not provided
        retain their current values on the client.

        Args:
            quilc_endpoint: A pre-existing quilc endpoint to use (e.g.
                ``tcp://host:5555``). When provided, the QCSClient's
                ``quilc_url`` is updated and no local quilc process is
                started.
            qvm_endpoint: A pre-existing QVM endpoint (e.g.
                ``http://host:5000``). When provided, the QCSClient's
                ``qvm_url`` is updated and no local qvm process is
                started.
            grpc_endpoint: An override for the QCS gRPC endpoint used by
                ``submit`` / ``retrieve_results`` / ``cancel_job``. When
                provided, the QCSClient is rebuilt and the cached
                ``ExecutionOptions`` are refreshed.
            start_quilc: Start a local quilc process if no endpoint is
                given and quilc is not already running on the default port.
            start_qvm: Start a local qvm process if no endpoint is given
                and qvm is not already running on the default port.
        """
        # --- Apply URL overrides by rebuilding the QCSClient (preserving auth) ---
        # The QCS SDK's ``QCSClient`` URLs are immutable on a constructed
        # instance; downstream calls (translate, submit, retrieve_results,
        # the quilc compiler client) all read URLs off the client. To
        # honour URL overrides we rebuild the client via the shared
        # ``build_qcs_client`` helper, reusing the existing OAuth session
        # (``QCSClient.oauth_session`` returns a copy per the qcs_sdk
        # stubs, which is safe to pass back into a new client). URLs not
        # overridden retain their existing values so the rebuild never
        # silently clears them. Execution options derive from the gRPC
        # URL, so refresh them whenever the client is rebuilt.
        if (
            quilc_endpoint is not None
            or qvm_endpoint is not None
            or grpc_endpoint is not None
        ):
            current = self._qcs_client
            # current is bound be non-null as we instantiate it in the
            # constructor when no client is provided, so we can safely read
            # its properties
            self._qcs_client = build_qcs_client(
                current.oauth_session,
                grpc_api_url=grpc_endpoint
                if grpc_endpoint is not None
                else current.grpc_api_url,
                quilc_url=quilc_endpoint
                if quilc_endpoint is not None
                else current.quilc_url,
                qvm_url=qvm_endpoint if qvm_endpoint is not None else current.qvm_url,
                api_url=current.api_url,
            )
            self._execution_options = self._build_execution_options()

        # --- Handle quilc ---
        if quilc_endpoint:
            logger.info("Using provided quilc endpoint: %s", quilc_endpoint)
        elif start_quilc:
            if is_port_in_use(DEFAULT_QUILC_PORT):
                logger.info(
                    "quilc already running on port %d, skipping.", DEFAULT_QUILC_PORT
                )
            else:
                binary = find_binary("quilc")
                if binary is None:
                    download_forest_sdk()
                self._start_quilc(binary)

        # --- Handle qvm ---
        if qvm_endpoint:
            logger.info("Using provided qvm endpoint: %s", qvm_endpoint)
        elif start_qvm:
            if is_port_in_use(DEFAULT_QVM_PORT):
                logger.info(
                    "qvm already running on port %d, skipping.", DEFAULT_QVM_PORT
                )
            else:
                binary = find_binary("qvm")
                if binary is None:
                    download_forest_sdk()
                self._start_qvm(binary)

        # --- Register cleanup ---
        self._register_cleanup()

    def _build_execution_options(self):
        """Build ExecutionOptions from the client's gRPC endpoint.

        The QCS QPU API calls (submit, retrieve_results, cancel_job) require
        ``ConnectionStrategy.EndpointAddress`` to connect directly to the
        gRPC endpoint. The default ``Gateway`` strategy does not work for
        direct API access.
        """
        builder = ExecutionOptionsBuilder()
        builder.connection_strategy = ConnectionStrategy.EndpointAddress(
            self._qcs_client.grpc_api_url
        )
        return builder.build()

    def _build_profile(self, quantum_processor_id: str) -> TargetProfile:
        instruction_set_architecture = get_instruction_set_architecture(
            quantum_processor_id=quantum_processor_id,
            client=self._qcs_client,
        )
        num_qubits = len(instruction_set_architecture.architecture.nodes)
        return TargetProfile(
            device_id=quantum_processor_id,
            simulator=False,
            experiment_type=ExperimentType.GATE_MODEL,
            program_spec=ProgramSpec(
                pyquil.Program, serialize=lambda program: program.out()
            ),
            num_qubits=num_qubits,
            provider_name="rigetti",
        )

    def get_devices(self) -> list[RigettiDevice]:
        devices: list[RigettiDevice] = []
        quantum_processor_ids = list_quantum_processors(client=self._qcs_client)
        for qpu_id in quantum_processor_ids:
            profile = self._build_profile(quantum_processor_id=qpu_id)
            devices.append(
                RigettiDevice(
                    profile=profile,
                    qcs_client=self._qcs_client,
                )
            )
        return devices

    def get_device(self, device_id: str) -> RigettiDevice:
        profile = self._build_profile(quantum_processor_id=device_id)
        return RigettiDevice(
            profile=profile,
            qcs_client=self._qcs_client,
        )
