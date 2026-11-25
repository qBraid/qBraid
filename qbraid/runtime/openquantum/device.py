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
Module defining OpenQuantum device class

"""
from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus
from qbraid.runtime.exceptions import QbraidRuntimeError

from .job import EXECUTION_PLAN_TYPES, QUEUE_PRIORITY_TYPES, OpenQuantumJob

if TYPE_CHECKING:
    import qbraid.runtime.openquantum

_DEFAULT_SHOTS = 100


def _device_status(row: Optional[dict[str, Any]]) -> DeviceStatus:
    """Map an Open Quantum catalog row to a qBraid device status.

    A missing row, or a row from before liveness was published, stays
    ``ONLINE`` so older payloads keep the previous behavior.
    """
    if not isinstance(row, dict):
        return DeviceStatus.ONLINE
    status = row.get("status")
    accepting = row.get("accepting_jobs")
    if status is None and accepting is None:
        return DeviceStatus.ONLINE
    normalized = status.lower() if isinstance(status, str) else ""
    if normalized == "offline":
        return DeviceStatus.OFFLINE
    if normalized in {"maintenance", "reserved"} or accepting is False:
        return DeviceStatus.UNAVAILABLE
    return DeviceStatus.ONLINE


def _resolve_shots(
    shots: Optional[int], configuration_data: Any
) -> tuple[Optional[int], dict[str, Any]]:
    """Copy shots into configuration_data, matching the Open Quantum API.

    Omitted shots default to 100 unless ``configuration_data["shots"]`` is
    set. Both values, when set, must agree.
    """
    if configuration_data is None:
        config: dict[str, Any] = {}
    elif isinstance(configuration_data, dict):
        config = dict(configuration_data)
    else:
        raise ValueError("configuration_data must be an object.")

    config_shots = config.get("shots")
    if config_shots is not None and (
        isinstance(config_shots, bool) or not isinstance(config_shots, int)
    ):
        raise ValueError("configuration_data.shots must be an integer.")
    if shots is not None and (isinstance(shots, bool) or not isinstance(shots, int)):
        raise ValueError("shots must be an integer.")
    if shots is not None and config_shots is not None and shots != config_shots:
        raise ValueError(
            f"shots mismatch: shots ({shots}) differs from "
            f"configuration_data.shots ({config_shots})"
        )
    if shots is None and config_shots is None:
        shots = _DEFAULT_SHOTS
    elif shots is None:
        shots = config_shots
    if shots is not None:
        config["shots"] = shots
    return shots, config


class OpenQuantumDevice(QuantumDevice):
    """OpenQuantum device interface."""

    def __init__(
        self,
        profile: qbraid.runtime.TargetProfile,
        session: qbraid.runtime.openquantum.OpenQuantumSession,
    ):
        super().__init__(profile=profile)
        self._session = session

    @property
    def session(self) -> qbraid.runtime.openquantum.OpenQuantumSession:
        """Return the OpenQuantum session."""
        return self._session

    def status(self) -> DeviceStatus:
        """Return the current status of the OpenQuantum device.

        Liveness comes from the management catalog (``status`` and
        ``accepting_jobs``). A failed lookup uses the snapshot stored on
        the device profile.
        """
        try:
            devices = self.session.get_devices()
        except Exception:  # pylint: disable=broad-exception-caught
            devices = None
        if isinstance(devices, list):
            for row in devices:
                if not isinstance(row, dict):
                    continue
                if row.get("short_code") == self.id or row.get("id") == self.id:
                    return _device_status(row)
        return _device_status(
            {
                "status": getattr(self.profile, "availability_status", None),
                "accepting_jobs": getattr(self.profile, "accepting_jobs", None),
            }
        )

    def _resolve_organization_id(self, organization_id: Optional[str]) -> str:
        """Pick the billing organization.

        An explicit id wins, then ``OPENQUANTUM_ORGANIZATION_ID``. With one
        organization, that organization is used. With several, the first
        owned organization is used and a warning names the choice.
        """
        if organization_id:
            return organization_id
        env_org = os.getenv("OPENQUANTUM_ORGANIZATION_ID")
        if env_org and env_org.strip():
            return env_org.strip()

        orgs = self.session.get_user_organizations()
        if not orgs:
            raise QbraidRuntimeError(
                "No organization found. Please accept the Open Quantum terms of use to continue."
            )
        chosen = orgs[0]
        if len(orgs) > 1:
            shown = orgs[:8]
            listing = ", ".join(f"{org.get('name', 'unnamed')} ({org.get('id')})" for org in shown)
            extra = len(orgs) - len(shown)
            if extra:
                listing = f"{listing}, and {extra} more"
            message = (
                "Multiple organizations found. Using "
                f"{chosen.get('name', 'unnamed')} ({chosen.get('id')}). "
                "Pass organization_id or set OPENQUANTUM_ORGANIZATION_ID "
                f"to choose one. Available: {listing}"
            )
            warnings.warn(message, UserWarning, stacklevel=2)
        org_id = chosen.get("id")
        if not org_id:
            raise QbraidRuntimeError("Organization is missing an id.")
        return org_id

    # pylint: disable-next=arguments-differ,too-many-arguments
    def submit(
        self,
        run_input: str | list[str],
        shots: Optional[int] = None,
        name: str = "qBraid Job",
        subcategory: Optional[str] = "oth:oth",
        dry_run: bool = False,
        organization_id: Optional[str] = None,
        execution_plan: Optional[str] = None,
        execution_plan_id: Optional[str] = None,
        queue_priority: Optional[str] = None,
        queue_priority_id: Optional[str] = None,
        input_format: Optional[str] = None,
        **kwargs,
    ) -> Union[OpenQuantumJob, list[OpenQuantumJob], list[dict[str, Any]]]:
        """Submit a job to the OpenQuantum device.

        Omitted shots default to 100, unless ``configuration_data["shots"]``
        is set. With one organization, that organization is billed. With
        several, pass ``organization_id`` or set
        ``OPENQUANTUM_ORGANIZATION_ID``. Plan and priority default to the
        cheapest quote. ``input_format`` defaults to OpenQASM on the server.
        Simulators that require fields such as ``engine`` take them in
        ``configuration_data``. The device profile's ``configuration_schema``
        lists those fields.
        """
        if isinstance(run_input, list):
            return [
                self.submit(
                    run_input=item,
                    shots=shots,
                    name=f"{name} {i}",
                    subcategory=subcategory,
                    dry_run=dry_run,
                    organization_id=organization_id,
                    execution_plan=execution_plan,
                    execution_plan_id=execution_plan_id,
                    queue_priority=queue_priority,
                    queue_priority_id=queue_priority_id,
                    input_format=input_format,
                    **kwargs,
                )
                for i, item in enumerate(run_input)
            ]

        organization_id = self._resolve_organization_id(organization_id)
        shots, configuration_data = _resolve_shots(shots, kwargs.get("configuration_data"))

        # Encode QASM
        if isinstance(run_input, str):
            run_input = run_input.encode("utf-8")

        upload_id = self.session.upload_input(run_input)

        prep_payload = {
            "organization_id": organization_id,
            "backend_class_id": self.id,
            "name": name,
            "upload_endpoint_id": upload_id,
            "shots": shots,
            "configuration_data": configuration_data,
            "submitted_with": "qbraid",
        }
        if subcategory is not None:
            prep_payload["job_subcategory_id"] = subcategory
        if input_format is not None:
            prep_payload["input_format"] = input_format

        prep_resp = self.session.prepare_job(prep_payload)
        prep_id = prep_resp["id"]

        quote = self.session.wait_for_preparation(prep_id)

        if dry_run:
            return quote

        # Convert readable names to UUIDs
        if execution_plan and not execution_plan_id:
            execution_plan_id = EXECUTION_PLAN_TYPES.get(execution_plan.upper())
            if not execution_plan_id:
                raise ValueError(f"Unknown execution plan: {execution_plan}")

        if queue_priority and not queue_priority_id:
            queue_priority_id = QUEUE_PRIORITY_TYPES.get(queue_priority.upper())
            if not queue_priority_id:
                raise ValueError(f"Unknown queue priority: {queue_priority}")

        # Plan & priority selection
        valid_options = []
        plan_found = False

        for p in quote:
            if execution_plan_id and p.get("execution_plan_id") != execution_plan_id:
                continue
            plan_found = True
            for q in p.get("queue_priorities", []):
                if queue_priority_id and q.get("queue_priority_id") != queue_priority_id:
                    continue
                valid_options.append((p, q))

        if not valid_options:
            if execution_plan_id and not plan_found:
                raise ValueError(f"Execution plan '{execution_plan_id}' not found in quote.")
            if execution_plan_id and queue_priority_id:
                raise ValueError(
                    f"Queue priority '{queue_priority_id}' not found in selected plan."
                )
            if queue_priority_id:
                raise ValueError(
                    f"Queue priority '{queue_priority_id}' not found in any execution plan."
                )
            raise ValueError("No valid execution plans or queue priorities found in quote.")

        plan, prio = min(
            valid_options,
            key=lambda opt: opt[0].get("price", float("inf"))
            + opt[1].get("price_increase", float("inf")),
        )

        job_payload = {
            "organization_id": organization_id,
            "job_preparation_id": prep_id,
            "execution_plan_id": plan["execution_plan_id"],
            "queue_priority_id": prio["queue_priority_id"],
        }

        job_resp = self.session.create_job(job_payload)
        return OpenQuantumJob(job_id=job_resp["id"], session=self.session, device=self)
