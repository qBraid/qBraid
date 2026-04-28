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

from typing import TYPE_CHECKING, Any, Optional, Union

from qbraid.runtime.device import QuantumDevice
from qbraid.runtime.enums import DeviceStatus

from .job import OpenQuantumJob

# Execution plan and queue priority mappings
EXECUTION_PLAN_TYPES = {
    "PUBLIC": "072f7eb6-574b-4bae-aafa-d3399c4abe7a",
    "PRIVATE": "f83fd52f-c691-470f-9521-26b81c4e53bd",
}

QUEUE_PRIORITY_TYPES = {
    "STANDARD": "0f7b91a3-d1bf-46fb-af9c-55b77fa72bed",
    "PRIORITY": "4ea2b9de-2d20-46d4-b1b5-0b71537a584f",
    "INSTANT": "74cebc3d-14d8-455d-900e-daedc1566384",
}

if TYPE_CHECKING:
    import qbraid.runtime.openquantum


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
        """Return the current status of the OpenQuantum device."""
        # OpenQuantum does not explicitly expose individual device status endpoints
        # without listing all devices. Assuming ONLINE if instance exists.
        return DeviceStatus.ONLINE

    def submit(
        self,
        run_input: str | list[str],
        shots: int = 100,
        name: str = "qBraid Job",
        subcategory: Optional[str] = "oth:oth",
        dry_run: bool = False,
        organization_id: Optional[str] = None,
        execution_plan: Optional[str] = None,
        execution_plan_id: Optional[str] = None,
        queue_priority: Optional[str] = None,
        queue_priority_id: Optional[str] = None,
        **kwargs,
    ) -> Union[OpenQuantumJob, list[OpenQuantumJob], list[dict[str, Any]]]:
        """Submit a job to the OpenQuantum device.

        Users can omit organization/plan/priority for sensible defaults
        (first org + cheapest plan + lowest priority).
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
                    **kwargs,
                )
                for i, item in enumerate(run_input)
            ]

        # Auto-select organization (your logic — perfect)
        if organization_id is None:
            orgs = self.session.get_user_organizations()
            if not orgs:
                raise ValueError("No organization found for user.")
            organization_id = orgs[0]["id"]

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
            "configuration_data": kwargs.get("configuration_data", {}),
        }
        if subcategory is not None:
            prep_payload["job_subcategory_id"] = subcategory

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

        # Plan & priority selection (your logic, slightly cleaner)
        if execution_plan_id:
            plan = next((p for p in quote if p["execution_plan_id"] == execution_plan_id), None)
            if not plan:
                raise ValueError(f"Execution plan '{execution_plan_id}' not found in quote.")
        else:
            plan = min(quote, key=lambda p: p.get("price", float("inf")))

        if queue_priority_id:
            prio = next(
                (q for q in plan["queue_priorities"] if q["queue_priority_id"] == queue_priority_id),
                None,
            )
            if not prio:
                raise ValueError(f"Queue priority '{queue_priority_id}' not found in selected plan.")
        else:
            prio = min(plan["queue_priorities"], key=lambda q: q.get("price_increase", float("inf")))

        job_payload = {
            "organization_id": organization_id,
            "job_preparation_id": prep_id,
            "execution_plan_id": plan["execution_plan_id"],
            "queue_priority_id": prio["queue_priority_id"],
        }

        job_resp = self.session.create_job(job_payload)
        return OpenQuantumJob(job_id=job_resp["id"], session=self.session, device=self)
