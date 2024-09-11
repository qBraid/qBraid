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
import logging
import os
import re
from typing import Any, Optional, Union

import numpy as np
from azure.quantum import Job
from azure.quantum.target.microsoft import MicrosoftEstimatorResult

from qbraid.runtime.result import ResultFormatter

logger = logging.getLogger(__name__)

# Constants for output data format:
MICROSOFT_OUTPUT_DATA_FORMAT = "microsoft.quantum-results.v1"
MICROSOFT_OUTPUT_DATA_FORMAT_V2 = "microsoft.quantum-results.v2"
IONQ_OUTPUT_DATA_FORMAT = "ionq.quantum-results.v1"
QUANTINUUM_OUTPUT_DATA_FORMAT = "honeywell.quantum-results.v1"
RESOURCE_ESTIMATOR_OUTPUT_DATA_FORMAT = "microsoft.resource-estimates.v1"
RIGETTI_OUTPUT_DATA_FORMAT = "rigetti.quil-results.v1"


class AzureResultBuilder:
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

    @staticmethod
    def make_estimator_result(data: dict[str, Any]) -> MicrosoftEstimatorResult:
        """Create a MicrosoftEstimatorResult object from the given data."""
        if not data["success"]:
            error_data = data["error_data"]
            message = (
                "Cannot retrieve results as job execution failed "
                f"({error_data['code']}: {error_data['message']})"
            )
            raise RuntimeError(message)

        results = data["results"]
        if len(results) == 1:
            data = results[0]["data"]
            return MicrosoftEstimatorResult(data)
        raise ValueError("Expected resource estimator results to be of length 1")

    def result(
        self, timeout: Optional[int] = None, sampler_seed: Optional[int] = None
    ) -> Union[dict, MicrosoftEstimatorResult]:
        """Return the results of the job."""
        self.job.wait_until_completed(timeout_secs=timeout)

        success = self.job.details.status == "Succeeded"
        results = self._format_results(sampler_seed=sampler_seed)
        results = results if isinstance(results, list) else [results]
        error_data = (
            None if self.job.details.error_data is None else self.job.details.error_data.as_dict()
        )

        result_dict = {
            "results": results,
            "job_id": self.job.id,
            "target": self.job.details.target,
            "job_name": self.job.details.name,
            "success": success,
            "error_data": error_data,
        }

        if self.job.details.output_data_format == RESOURCE_ESTIMATOR_OUTPUT_DATA_FORMAT:
            return self.make_estimator_result(result_dict)
        return result_dict

    def _format_results(
        self, sampler_seed: Optional[int] = None
    ) -> Union[list[dict[str, Any]], dict[str, Any]]:
        """
        Populates the results datastructures in a format that
        is compatible with qBraid runtime.

        """
        if self.job.details.output_data_format == MICROSOFT_OUTPUT_DATA_FORMAT_V2:
            return self._format_microsoft_v2_results()

        success = self.job.details.status == "Succeeded"

        job_result = {
            "data": {},
            "success": success,
            "header": {},
        }

        if success:
            if self.job.details.output_data_format == MICROSOFT_OUTPUT_DATA_FORMAT:
                job_result["data"] = self._format_microsoft_results(sampler_seed=sampler_seed)
            elif self.job.details.output_data_format == IONQ_OUTPUT_DATA_FORMAT:
                job_result["data"] = self._format_ionq_results()
            elif self.job.details.output_data_format == QUANTINUUM_OUTPUT_DATA_FORMAT:
                job_result["data"] = self._format_quantinuum_results()
            elif self.job.details.output_data_format == RIGETTI_OUTPUT_DATA_FORMAT:
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
        az_result = self.job.get_results()
        shots = self._shots_count()

        counts = None
        probabilities = None

        if not "histogram" in az_result:
            raise ValueError("Histogram missing from IonQ Job results")

        data = {
            "shots": shots,
            "probabilities": az_result["histogram"],
        }
        probs_binary = {
            bin(int(key))[2:].zfill(2): value for key, value in data["probabilities"].items()
        }
        probs_normal = ResultFormatter.normalize_bit_lengths(probs_binary)
        counts = {state: int(prob * shots) for state, prob in probs_normal.items()}

        total_count = sum(counts.values())
        probabilities = {key: value / total_count for key, value in counts.items()}

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
                [AzureResultBuilder._qir_to_qbraid_bitstring(term) for term in reversed(obj)]
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
            bitstring = AzureResultBuilder._qir_to_qbraid_bitstring(key)

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

                bitstring = AzureResultBuilder._qir_to_qbraid_bitstring(result["Display"])
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
