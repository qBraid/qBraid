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
from typing import Optional

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
        self._quilc_process: Optional[Popen] = None
        self._qvm_process: Optional[Popen] = None
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
            self._qcs_client = build_qcs_client(
                refresh_token=refresh_token,
                client_id=os.getenv("RIGETTI_CLIENT_ID"),
                issuer=os.getenv("RIGETTI_ISSUER"),
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
                logger.warning("Process %d did not exit in time, sending SIGKILL", proc.pid)
                proc.kill()
            setattr(self, attr, None)

    def _signal_handler(self, signum: int, frame) -> None:  # pylint: disable=unused-argument
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
        refresh_token: Optional[str] = None,
        client_id: Optional[str] = None,
        issuer: Optional[str] = None,
        quilc_endpoint: Optional[str] = None,
        qvm_endpoint: Optional[str] = None,
        grpc_endpoint: Optional[str] = None,
        start_quilc: bool = True,
        start_qvm: bool = False,
        interactive: bool = True,
    ) -> None:
        """Set up credentials and optionally start quilc/qvm processes.

        Args:
            refresh_token: Rigetti QCS refresh token. Falls back to
                ``RIGETTI_REFRESH_TOKEN`` env var, then interactive prompt.
            client_id: OAuth client ID. Falls back to ``RIGETTI_CLIENT_ID``.
            issuer: OAuth issuer URL. Falls back to ``RIGETTI_ISSUER``.
            quilc_endpoint: Quilc RPCQ endpoint (e.g. ``tcp://host:5555``).
                If provided, no local quilc process is started.
            qvm_endpoint: QVM endpoint (e.g. ``http://host:5000``).
                If provided, no local qvm process is started.
            grpc_endpoint: QCS gRPC endpoint override.
            start_quilc: Start a local quilc process if no endpoint is given
                and quilc is not already running.
            start_qvm: Start a local qvm process if no endpoint is given
                and qvm is not already running.
            interactive: If True, prompt for missing credentials via input().
        """
        # --- Gather credentials ---
        refresh_token = refresh_token or os.getenv("RIGETTI_REFRESH_TOKEN")
        if not refresh_token:
            if interactive:
                refresh_token = input("Enter your Rigetti QCS refresh token: ").strip()
            if not refresh_token:
                raise ValueError(
                    "A Rigetti refresh token is required. "
                    "Pass it via refresh_token=, set RIGETTI_REFRESH_TOKEN, "
                    "or run with interactive=True."
                )

        client_id = client_id or os.getenv("RIGETTI_CLIENT_ID")
        issuer = issuer or os.getenv("RIGETTI_ISSUER")
        if interactive and not client_id:
            client_id = input("Enter your Rigetti client ID (or press Enter to skip): ").strip()
            client_id = client_id or None
        if interactive and not issuer:
            issuer = input("Enter your Rigetti issuer URL (or press Enter to skip): ").strip()
            issuer = issuer or None

        # --- Resolve URLs ---
        quilc_url = quilc_endpoint or os.getenv("QCS_QUILC_ENDPOINT", DEFAULT_QUILC_URL)
        qvm_url = qvm_endpoint or os.getenv("QCS_QVM_ENDPOINT", DEFAULT_QVM_URL)
        grpc_api_url = grpc_endpoint or os.getenv("QCS_GRPC_ENDPOINT", DEFAULT_GRPC_API_URL)

        # --- Rebuild QCSClient ---
        self._qcs_client = build_qcs_client(
            refresh_token=refresh_token,
            client_id=client_id,
            issuer=issuer,
            grpc_api_url=grpc_api_url,
            quilc_url=quilc_url,
            qvm_url=qvm_url,
        )
        self._execution_options = self._build_execution_options()

        # --- Handle quilc ---
        if quilc_endpoint:
            logger.info("Using provided quilc endpoint: %s", quilc_endpoint)
        elif start_quilc:
            if is_port_in_use(DEFAULT_QUILC_PORT):
                logger.info("quilc already running on port %d, skipping.", DEFAULT_QUILC_PORT)
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
                logger.info("qvm already running on port %d, skipping.", DEFAULT_QVM_PORT)
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
            program_spec=ProgramSpec(pyquil.Program, serialize=lambda program: program.out()),
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
                    execution_options=self._execution_options,
                )
            )
        return devices

    def get_device(self, device_id: str) -> RigettiDevice:
        profile = self._build_profile(quantum_processor_id=device_id)
        return RigettiDevice(
            profile=profile,
            qcs_client=self._qcs_client,
            execution_options=self._execution_options,
        )
