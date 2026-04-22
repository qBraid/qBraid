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

"""
Module defining Quantinuum provider class.

"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from qbraid._caching import cached_method
from qbraid.programs import ExperimentType, ProgramSpec
from qbraid.runtime.exceptions import ResourceNotFoundError
from qbraid.runtime.profile import TargetProfile
from qbraid.runtime.provider import QuantumProvider

from .device import QuantinuumDevice

if TYPE_CHECKING:
    from pytket.backends.backendinfo import BackendInfo

logger = logging.getLogger(__name__)


def _fetch_quantinuum_devices_df():
    """Return the NEXUS Quantinuum devices dataframe."""
    # pylint: disable-next=import-outside-toplevel
    import qnexus as qnx

    return qnx.devices.get_all(issuers=[qnx.devices.IssuerEnum.QUANTINUUM]).df()


def _get_backend_info(device_name: str) -> BackendInfo:
    """Fetch the pytket BackendInfo for a specific Quantinuum device."""
    df = _fetch_quantinuum_devices_df()
    matching_rows = df.loc[df["device_name"] == device_name]

    if matching_rows.empty:
        available_devices = df["device_name"].tolist()
        raise ResourceNotFoundError(
            f"Device '{device_name}' not found in Quantinuum device list. "
            f"Available devices: {available_devices}"
        )

    return matching_rows.iloc[0]["backend_info"]


def _build_profile(device_id: str, backend_info: BackendInfo) -> TargetProfile:
    """Build a TargetProfile from a Quantinuum device name and backend info."""
    # pylint: disable-next=import-outside-toplevel
    from pytket import Circuit

    return TargetProfile(
        device_id=device_id,
        # Quantinuum emulator/simulator device names contain "E" (e.g. "H1-1E").
        simulator="E" in device_id.upper(),
        experiment_type=ExperimentType.GATE_MODEL,
        num_qubits=len(backend_info.architecture.nodes),
        program_spec=ProgramSpec(Circuit, alias="pytket"),
        provider_name="quantinuum",
        # Extras: accessible via ``device.profile.backend_info``.
        backend_info=backend_info,
    )


class QuantinuumProvider(QuantumProvider):
    """Quantinuum NEXUS provider class."""

    def __hash__(self) -> int:
        # Authentication is handled implicitly by qnexus (via ``qnx login``),
        # so a single process-wide provider instance is effectively stateless
        # from qBraid's perspective.
        return hash(("quantinuum", id(self)))

    @cached_method
    def get_device(self, device_id: str) -> QuantinuumDevice:
        """Get a specific Quantinuum device."""
        device_id = device_id.strip()
        backend_info = _get_backend_info(device_id)
        return QuantinuumDevice(profile=_build_profile(device_id, backend_info))

    @cached_method
    def get_devices(self) -> list[QuantinuumDevice]:  # pylint: disable=arguments-differ
        """Get a list of available Quantinuum devices.

        Issues a single call to ``qnx.devices.get_all`` and builds each
        :class:`QuantinuumDevice` from the returned dataframe rows, avoiding
        the N+1 pattern that would otherwise re-fetch the device list inside
        :meth:`get_device` for each entry.
        """
        df = _fetch_quantinuum_devices_df()
        return [
            QuantinuumDevice(
                profile=_build_profile(row["device_name"], row["backend_info"]),
            )
            for _, row in df.iterrows()
        ]
