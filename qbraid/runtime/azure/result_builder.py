# Copyright (C) 2024 qBraid
# Copyright (C) 2024 Microsoft Corporation
#
# This file is part of the qBraid-SDK.
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. This specific file, adapted from Microsoft, is dual-licensed under both
# the MIT License, and the GPL v3. You may not use this file except in compliance
# with the applicable license. You may obtain a copy of the MIT License at
#
# https://opensource.org/license/mit
#
# This file includes code adapted from Microsoft (https://github.com/microsoft/azure-quantum-python)
# with modifications by qBraid. The original copyright notice is included above.
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# qbraid: skip-header

"""
Module defining AzureResultBuilder class

"""
import ast
import datetime
import json
import os
import re
from typing import Any, Optional, Union

import numpy as np
from azure.quantum import Job

from qbraid.runtime.ionq.job import IonQJob
from qbraid.runtime.postprocess import counts_to_probabilities, normalize_counts

from .io_format import OutputDataFormat


class AzureGateModelResultBuilder:
    """Class to format Azure Quantum job results."""

    def __init__(self, azure_job: Job):
        self._azure_job = azure_job

    @property
    def job(self) -> Job:
        """Return the Azure Quantum job."""
        return self._azure_job

    @property
    def from_simulator(self) -> bool:
        """Return whether the job was executed on a simulator."""
        return self._azure_job.details.target.split(".", 1)[1] != "qpu"

    def _shots_count(self) -> Optional[int]:
        """Return the number of shots used in the job."""
        # Some providers use 'count', some other 'shots', give preference to 'count':
        input_params = self.job.details.input_params
        return input_params.get("count", input_params.get("shots"))

    def _format_results(
        self, sampler_seed: Optional[int] = None
    ) -> Union[list[dict[str, Any]], dict[str, Any]]:
        """
        Populates the results datastructures in a format that
        is compatible with qBraid runtime.

        """
        if self.job.details.output_data_format == OutputDataFormat.MICROSOFT_V2.value:
            return self._format_microsoft_v2_results()

        success = self.job.details.status == "Succeeded"

        job_result = {
            "data": {},
            "success": success,
            "header": {},
        }

        if success:
            if self.job.details.output_data_format == OutputDataFormat.MICROSOFT_V1.value:
                job_result["data"] = self._format_microsoft_results(sampler_seed=sampler_seed)
            elif self.job.details.output_data_format == OutputDataFormat.IONQ.value:
                job_result["data"] = self._format_ionq_results()
            elif self.job.details.output_data_format == OutputDataFormat.QUANTINUUM.value:
                job_result["data"] = self._format_quantinuum_results()
            elif self.job.details.output_data_format == OutputDataFormat.RIGETTI.value:
                job_result["data"] = self._format_rigetti_results()
            else:
                job_result["data"] = self._format_unknown_results()

        job_result["header"] = self.job.details.metadata or {}
        if "metadata" in job_result["header"]:
            job_result["header"]["metadata"] = json.loads(job_result["header"]["metadata"])

        job_result["shots"] = self._shots_count()
        return job_result

    @staticmethod
    def _draw_random_sample(
        probabilities: dict[str, int], shots: int, sampler_seed: Optional[int] = None
    ) -> dict:
        """Draw a random sample from the given probabilities."""
        norm = sum(probabilities.values())

        if norm != 1:
            if not np.isclose(norm, 1.0, rtol=1e-4):
                raise ValueError(f"Probabilities do not add up to 1: {probabilities}")
            probabilities = {k: v / norm for k, v in probabilities.items()}
        if not sampler_seed:
            current_microtime = int(datetime.datetime.now().timestamp() * 1_000_000)
            random_bytes = os.urandom(4) + current_microtime.to_bytes(8, "little")
            sampler_seed = int.from_bytes(random_bytes, "little") % (2**32 - 1)

        rng = np.random.default_rng(sampler_seed)
        rand_values = rng.choice(list(probabilities.keys()), shots, p=list(probabilities.values()))
        return dict(zip(*np.unique(rand_values, return_counts=True)))

    def _format_ionq_results(self) -> dict[str, Any]:
        """
        Translate IonQ's histogram data into a format that
        can be consumed by qBraid runtime.

        """
        shots = self._shots_count()
        az_result = self.job.get_results()

        if "histogram" not in az_result:
            raise ValueError("Histogram missing from IonQ Job results")

        data = {
            "shots": shots,
            "probabilities": az_result["histogram"],
        }

        raw_counts = IonQJob._get_counts(data)
        counts = normalize_counts(raw_counts)
        probabilities = counts_to_probabilities(counts)

        return {"counts": counts, "probabilities": probabilities}

    @staticmethod
    def _qir_to_qbraid_bitstring(obj) -> str:
        """Convert the data structure from Azure into the "schema" used by qBraid."""
        if isinstance(obj, str) and not re.match(r"[\d\s]+$", obj):
            obj = ast.literal_eval(obj)

        if isinstance(obj, tuple):
            # the outermost implied container is a tuple, and each item is
            # associated with a classical register. Azure and qBraid order the
            # registers in opposite directions, so reverse here to match.
            return " ".join(
                [
                    AzureGateModelResultBuilder._qir_to_qbraid_bitstring(term)
                    for term in reversed(obj)
                ]
            )
        if isinstance(obj, list):
            # a list is for an individual classical register
            return "".join([str(bit) for bit in obj])

        return str(obj)

    def _format_microsoft_results(self, sampler_seed: Optional[int] = None) -> dict[str, Any]:
        """
        Translate Microsoft's job results histogram into a format that
        can be consumed by qBraid runtime.

        """
        histogram = self.job.get_results()
        shots = self._shots_count()

        counts = {}
        probabilities = {}

        for key in histogram.keys():
            bitstring = self._qir_to_qbraid_bitstring(key)

            value = histogram[key]
            probabilities[bitstring] = value

        if self.from_simulator:
            counts = self._draw_random_sample(probabilities, shots, sampler_seed)
        else:
            counts = {
                bitstring: np.round(shots * value) for bitstring, value in probabilities.items()
            }

        return {"counts": counts, "probabilities": probabilities}

    def _format_quantinuum_results(self) -> dict[str, Any]:
        """
        Translate Quantinuum's histogram data into a format that
        can be consumed by qBraid runtime.

        """
        az_result = self.job.get_results()
        all_bitstrings = [
            bitstrings
            for classical_register, bitstrings in az_result.items()
            if classical_register != "access_token"
        ]
        counts = {}
        combined_bitstrings = ["".join(bitstrings) for bitstrings in zip(*all_bitstrings)]
        shots = len(combined_bitstrings)

        for bitstring in set(combined_bitstrings):
            counts[bitstring] = combined_bitstrings.count(bitstring)

        histogram = {bitstring: count / shots for bitstring, count in counts.items()}

        return {"counts": counts, "probabilities": histogram}

    def _format_rigetti_results(self) -> dict[str, Any]:
        """
        Translate Rigetti's readout data into a format that
        can be consumed by qBraid runtime.

        """
        az_result = self.job.get_results()
        readout = az_result["ro"]
        measurements = ["".join(map(str, row)) for row in readout]
        counts = {row: measurements.count(row) for row in set(measurements)}
        total_counts = sum(counts.values())
        probabilities = {outcome: count / total_counts for outcome, count in counts.items()}
        return {"counts": counts, "probabilities": probabilities}

    def _format_unknown_results(self):
        """Format Job results data when the job output is in an unknown format."""
        return self.job.get_results()

    def _translate_microsoft_v2_results(self) -> list[tuple[int, dict[str, Any]]]:
        """
        Translate Microsoft's batching job results histograms into a format that
        can be consumed by qBraid runtime.

        """
        az_result = self.job.get_results()

        if not "DataFormat" in az_result:
            raise ValueError("DataFormat missing from Job results")

        if not "Results" in az_result:
            raise ValueError("Results missing from Job results")

        histograms = []
        results = az_result["Results"]
        for circuit_results in results:
            counts = {}
            probabilities = {}

            if not "TotalCount" in circuit_results:
                raise ValueError("TotalCount missing from Job results")

            total_count: int = circuit_results["TotalCount"]

            if total_count <= 0:
                raise ValueError("TotalCount must be a positive non-zero integer")

            if not "Histogram" in circuit_results:
                raise ValueError("Histogram missing from Job results")

            histogram = circuit_results["Histogram"]
            for result in histogram:
                if not "Display" in result:
                    raise ValueError("Dispaly missing from histogram result")

                if not "Count" in result:
                    raise ValueError("Count missing from histogram result")

                bitstring = self._qir_to_qbraid_bitstring(result["Display"])
                count = result["Count"]
                probability = count / total_count
                counts[bitstring] = count
                probabilities[bitstring] = probability
            histograms.append((total_count, {"counts": counts, "probabilities": probabilities}))
        return histograms

    def _get_entry_point_names(self) -> list[str]:
        """Get QIR entry point names from the input parameters."""
        input_params = self.job.details.input_params
        # All V2 output is a list of entry points
        entry_points = input_params["items"]
        entry_point_names = []
        for entry_point in entry_points:
            if not "entryPoint" in entry_point:
                raise ValueError("Entry point input_param is missing an 'entryPoint' field")
            entry_point_names.append(entry_point["entryPoint"])
        return entry_point_names if len(entry_point_names) > 0 else ["main"]

    def _format_microsoft_v2_results(self) -> list[dict[str, Any]]:
        """
        Translate Microsoft's batching job results histograms into a format that
        can be consumed by qBraid runtime.

        """
        status = self.job.details.status
        success = status == "Succeeded"

        if not success:
            return [
                {
                    "data": {},
                    "success": False,
                    "header": {},
                    "shots": 0,
                }
            ]

        entry_point_names = self._get_entry_point_names()

        results = self._translate_microsoft_v2_results()

        if len(results) != len(entry_point_names):
            raise ValueError(
                "The number of experiment results does not match the number of experiment names"
            )

        return [
            {
                "data": result,
                "success": success,
                "shots": total_count,
                "name": name,
                "status": status,
                "header": {"name": name},
            }
            for name, (total_count, result) in zip(entry_point_names, results)
        ]

    def get_results(
        self, timeout: Optional[int] = None, sampler_seed: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Return the results of the job."""
        self.job.wait_until_completed(timeout_secs=timeout)

        results = self._format_results(sampler_seed=sampler_seed)
        results = results if isinstance(results, list) else [results]
        return results

    def get_counts(self) -> Union[dict[str, int], list[dict[str, int]]]:
        """Return the raw counts from the result data."""
        results = self.get_results()

        if len(results) == 1:
            return results[0]["data"]["counts"] if results[0]["success"] else {}

        return [result["data"]["counts"] if result["success"] else {} for result in results]
