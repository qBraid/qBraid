# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Types of changes:
- `Added`: for new features.
- `Improved`: for improvements to existing functionality.
- `Deprecated`: for soon-to-be removed features.
- `Removed`: for now removed features.
- `Fixed`: for any bug fixes.
- `Dependencies`: for updates to external libraries or packages.

## [Unreleased]

### Added

### Improved / Modified
- `OQCDevice.transform()` method now removes "include" statements from qasm strings, as they are not supported by the OQC cloud. ([#831](https://github.com/qBraid/qBraid/pull/831))
- Extended `OQCDevice.get_next_window()` to fallback and attempt to extract next (or current) start window from `OQCClient.get_qpu_execution_estimates()` if `OQCClient.get_next_window()` raises an exception (e.g. for non-AWS windows). Now can return next widow `datetime` for Toshiko QPU. ([#831](https://github.com/qBraid/qBraid/pull/831))
- Updated `OQCDevice.submit()` to so that we no longer explicitly set the `CompilerConfig` defaults and rather leave optional arguments as `None` if not provided. ([#831](https://github.com/qBraid/qBraid/pull/831))
- Updated `QuEraQasmSimulatorResultData` for `flair-visual` version 0.5.3 and for correspondiong qBraid Quantum Jobs API QuEra endpoint updates, which consolidate returned data into single `quera_simulation_result` dictionary field ([#832](https://github.com/qBraid/qBraid/pull/832))

### Deprecated

### Removed
- Removed `qbraid.passes.compat.rename_qasm_registers()`. Function did not work properly, and is no longer even needed for OQC runtime as submission format is now `qasm3`, not `qasm2`. ([#831](https://github.com/qBraid/qBraid/pull/831))

### Fixed

### Dependencies

## [0.8.6] - 2024-11-11

### Added
- Registered "qubo" coefficients program type under `qbraid.programs.typer.QuboCoefficientsDict` ([#820](https://github.com/qBraid/qBraid/pull/820))
- Added option to create a `ConversionGraph` using only specific nodes ([#822](https://github.com/qBraid/qBraid/pull/822))
- Added option to include all registered program types in `ConversionGraph`, even if they don't have any supported conversions ([#822](https://github.com/qBraid/qBraid/pull/822))
- Added method that maps all nodes in a `ConversionGraph` to their corresponding `ExperimentType` ([#822](https://github.com/qBraid/qBraid/pull/822))
- Added option to `ConversionGraph` while only showing nodes matching given `ExperimentType` value(s) ([#822](https://github.com/qBraid/qBraid/pull/822))

```python
from qbraid import ConversionGraph, ExperimentType

graph = ConversionGraph(nodes=["qasm2", "qasm3", "qubo"], include_isolated=True)

for alias, exp_type in graph.get_node_experiment_types().items():
    print(alias, exp_type.value)

graph.plot(experiment_type=ExperimentType.GATE_MODEL)
```

- Added conditional for OQC device `OFFLINE` status when unavailable + outside live window ([#826](https://github.com/qBraid/qBraid/pull/826))
- Added units for OQC device pricing (USD) ([#826](https://github.com/qBraid/qBraid/pull/826))

### Improved / Modified
- Separated runtime device `transform` and `to_ir` logic into separate steps ([#819](https://github.com/qBraid/qBraid/pull/819))
- Updated runtime validation step to handle program batches and not re-warn for device-related checks ([#819](https://github.com/qBraid/qBraid/pull/819))
- Updated runtime device transpile method and target profile to allow for lists of `ProgramSpec` ([#819](https://github.com/qBraid/qBraid/pull/819))
- Updated native runtime logic for NEC vector annealer to support "qubo" program spec type. Offset argument / attribute removed from `qbraid.programs.annealing.Problem`. `QbraidDevice.run` flow now derives "offset" paramater from `params` argument (of type `QuboSolveParams`, now required). This allows a more straightfoward procedure (with more visiblity) when submitting programs from  `pyqubo.Module`. See code example below. ([#820](https://github.com/qBraid/qBraid/pull/820))

```python
from qbraid import QbraidProvider
from qbraid.runtime.schemas import QuboSolveParams

s1, s2, s3, s4 = [pyqubo.Spin(f"s{i}") for i in range(1, 5)]
H = (4 * s1 + 2 * s2 + 7 * s3 + s4) ** 2
model = H.compile()
qubo, offset = model.to_qubo()

params = QuboSolveParams(offset=offset)

provider = QbraidProvider()

device = provider.get_device("nec_vector_annealer")

job = device.run(qubo, params=params)
```

- IonQ multicircuit jobs and input data format field added explicitly ([#825](https://github.com/qBraid/qBraid/pull/825))
- OQC provider url + timeout params added to `__init__`, and target profile updates to include new device metadata fields returned by `OQCClient`, particularly in relation to Toshiko QPU  ([#825](https://github.com/qBraid/qBraid/pull/825))
- Updated `random_circuit` function to use transpiler to consider all possible random circuit generators package funcs starting from the one with the closest conversion path to the specified target package. Reverses the logic of `ConversionGraph.get_sorted_closest_targets` with new function `ConversionGraph.get_sorted_closest_sources()` ([#829](https://github.com/qBraid/qBraid/pull/829))

### Fixed
- Fixed `qasm2_to_qasm3()` conversion error cause by `qbraid/transpiler/conversions/qasm2/qelib_qasm3.qasm` not being included in `MANIFEST.in`  ([#825](https://github.com/qBraid/qBraid/pull/825))
- Fixed docs CSS so stable/latest words show up (previously white and blended into the background so weren't visible) ([#826](https://github.com/qBraid/qBraid/pull/826))

### Dependencies
- Updated `pyqasm` optional dependency to `0.0.3` ([#824](https://github.com/qBraid/qBraid/pull/824))
- Updated `oqc-qcass-client` optional dependnecy to `3.11.0` ([#826](https://github.com/qBraid/qBraid/pull/826))

## [0.8.5] - 2024-10-31

### Added
- Updates for interfacing with IonQ devices from `QbraidProvider` including error mitigation field (to support `debias` parameter) for run method and basis gates set included in target profile ([#817](https://github.com/qBraid/qBraid/pull/817))

### Improved / Modified
- Updated examples submodule and added note to contributing doc about how to do so ([#817](https://github.com/qBraid/qBraid/pull/817))

## [0.8.4] - 2024-10-29

### Added
- Added support for [IonQ native gates](https://docs.ionq.com/guides/getting-started-with-native-gates) (gpi/gpi2/ms/zz) for `qasmX_to_ionq()` conversions ([#807](https://github.com/qBraid/qBraid/pull/807))
- Expanded `QuantumDevice.metadata()` to include average queue time field if provided, instead of (or in addition to) pending jobs ([#807](https://github.com/qBraid/qBraid/pull/807))
- Added device characterization data to `IonQDevice.profie` ([#807](https://github.com/qBraid/qBraid/pull/807))

### Improved / Modified
- Added pydantic schema to define the possible Qubo solve params available for submissions to the NEC vector annealer device ([#788](https://github.com/qBraid/qBraid/pull/788))
- Improved clarity of GitHub issue template bug report prompts ([#791](https://github.com/qBraid/qBraid/pull/791))
- Combined `qasm2` and `qasm3` modules in `qbraid.passes` to allow splitting `qbraid.programs.gate_model.qasm` into `qasm2` and `qasm3` sub-modules to maintain program type alias consistency ([#805](https://github.com/qBraid/qBraid/pull/805))
- Improved `IonQDevice.submit` method by explicitly list all available runtime parameters as optional args, included `preflight` bool to get cost in USD without actually submitting job ([#807](https://github.com/qBraid/qBraid/pull/807))
- `qbraid.runtime.native` schema + provider + profile updates for IonQ including basis gates (include native), program validation (no meas), and optional pricing (for when variable) ([#809](https://github.com/qBraid/qBraid/pull/809))
- Improved openqasm3 to ionq conversion error handling, error messages, and logging ([#814](https://github.com/qBraid/qBraid/pull/814))

### Fixed
- Fixed native runtime bug: failure to raise exception if `qbraid-qir` not installed for "qbraid_qir_simulator" device. Now warns at provider level and raises in run method if transform fails ([#801](https://github.com/qBraid/qBraid/pull/801))
- Fixed bug in `qbraid.passes.qasm.convert_qasm_pi_to_decimal()` where `gpi` and `gpi2` gate defs were being subbed with pi decimal value. Fix is not perfect but will work for most cases. ([#812](https://github.com/qBraid/qBraid/pull/812))

### Dependencies
- Added `pyqasm` as optional dependency extra for IonQ ([#807](https://github.com/qBraid/qBraid/pull/807))

## [0.8.3] - 2024-10-09

### Added
- Added `AnnealingResultData` class to `qbraid.runtime` module to represent annealing results. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Added `NECVectorAnnealerResultData` class to `qbraid.runtime.native` module to represent NEC vector annealer results. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Added `AnnealingExperimentMetadata` class to `qbraid.runtime.schemas` module to represent annealing experiment metadata. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Added `NECVectorAnnealerExperimentMetadata` class to `qbraid.runtime.schemas` module to represent NEC vector annealer experiment metadata. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Added mock data and methods to `test.resources` module to support testing of annealing and NEC vector annealing results. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Link to `examples` repo ([#778](https://github.com/qBraid/qBraid/pull/778))

### Improved / Modified
- Updated the ExperimentType enum to change the value of ANNEALING from "quantum_annealing" to "annealing" to better reflect the general nature of experiments. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Updated `QbraidJob.result`  method to return `AnnealingResultData` or `NECVectorAnnealerResultData` instances for annealing and NEC vector annealer experiments, respectively. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Added a test case for the NEC Vector Annealer workflow in , including job submission and result retrieval. ([#768](https://github.com/qBraid/qBraid/pull/768))
- Added unit tests for `AnnealingResultData`, `NECVectorAnnealerResultData`, and `AnnealingExperimentMetadata` classes. ([#768](https://github.com/qBraid/qBraid/pull/768))
- PR compliance workflow that checks that `CHANGELOG.md` is updated with each PR, and if not, issues a reminder ([#772](https://github.com/qBraid/qBraid/pull/772))
- Workflow to bump semantic version in `_version.py` ([#773](https://github.com/qBraid/qBraid/pull/773))
- Changed `qbraid.runtime.NoiseModel` from an `Enum` to a `dataclass` and introduced `qbraid.runtime.NoiseModelSet` to manage multiple `NoiseModel` instances. An `Enum` was too restrictive since its values are fixed, so a more flexible structure was needed for loading noise model data from an API. Using a dataclass allows storing brief descriptions of noise models. `NoiseModelSet` ensures naming consistency and provides easy add, remove, and get operations for provider classes. ([#773](https://github.com/qBraid/qBraid/pull/773))
- Make noise models optional in `DeviceData` schema ([#784](https://github.com/qBraid/qBraid/pull/784))

```python
from qbraid.runtime.noise import NoiseModel, NoiseModelSet

ideal_model = NoiseModel("ideal", "Ideal noise model for simulations")
custom_model = NoiseModel("custom", "Custom noise model with specific parameters")

models = NoiseModelSet()
models.add(ideal_model)
models.add(custom_model)

retrieved_model = models.get("ideal")
print(f"Retrieved model: {retrieved_model.name} - {retrieved_model.description}")

models.add("ideal", "Updated ideal model", overwrite=True)

for name, model in models.items():
    print(f"{name}: {model.description}")

models.remove("custom")
```

- Moved `ExperimentType` enum into `qbraid.programs` ([#777](https://github.com/qBraid/qBraid/pull/777))
- Renamed `qbraid.programs.circuits` to `qbraid.programs.gate_model` to match enum value ([#777](https://github.com/qBraid/qBraid/pull/777))

### Fixed
- Fixed spelling error of `test_quera_simulator_workflow` in `test.test_device` module. ([#768](https://github.com/qBraid/qBraid/pull/768))

## [0.8.2] - 2024-09-30

### Improved / Modified
- Improved `IonQJob.status` and added overriding `IonQJob.metadata` method that uses status caching and refreshes all job metadata when in non-terminal state. ([#765](https://github.com/qBraid/qBraid/pull/765))
- Improved `QbraidJob.cancel` method so more accurately indicate whether job cancel request was successful or not ([#766](https://github.com/qBraid/qBraid/pull/766))
- Modified output JSON format of `QbraidJob.metadata` to mirror that of the `qbraid.runtime.schemas.RuntimeJobModel` ([#766](https://github.com/qBraid/qBraid/pull/766))

### Dependencies
- Update amazon-braket-sdk requirement from <1.88.0,>=1.83.0 to >=1.83.0,<1.89.0 ([#767](https://github.com/qBraid/qBraid/pull/767))

## [0.8.1] - 2024-09-26

### Added
- Added `ValidationLevel` int enum that controls whether the behavior of runtime `QuantumDevice.validate` method, allowing either `NONE`, `WARN`, or `RAISE` ([#762](https://github.com/qBraid/qBraid/pull/762))
- Added `NoiseModelWrapper` class that allows dynamically setting the value of the `NoiseModel.Other` enum ([#762](https://github.com/qBraid/qBraid/pull/762))
- Added `DeviceData` schema to improve the way we process JSON device data recieved from the qBraid API  ([#762](https://github.com/qBraid/qBraid/pull/762))

### Improved / Modified
- Added optional `RuntimeOptions` argument to `QuantumDevice` class to enable overriding default options upon instantiation ([#762](https://github.com/qBraid/qBraid/pull/762))
- Added `RuntimeOptions.merge` method to allow combining to options objects with preference to the values and/or validators of either ([#762](https://github.com/qBraid/qBraid/pull/762))
- Organized all pydantic schemas used in qBraid runtime under (new) module `qbraid.runtime.schemas` ([#762](https://github.com/qBraid/qBraid/pull/762))

### Fixed
- Fixed `pkg_resources` import error bug. Not shipped with Python > 3.9, so needed lazy import ([#762](https://github.com/qBraid/qBraid/pull/762))

### Dependencies
- Update qbraid-core requirement from >=0.1.22 to >=0.1.24 ([#762](https://github.com/qBraid/qBraid/pull/762))
- Added [ipympl](https://matplotlib.org/ipympl/) to `qbraid[visualization]` extras to allow enhance matplotlib animations with `flair-visual` ([#762](https://github.com/qBraid/qBraid/pull/762))

## [0.8.0] - 2024-09-23

### Added
- Added `qbraid.programs.typer` module containing custom types (`Qasm2StringType` and `Qasm3StringType`) that can be used instead of `str` for more accurate static typing, as well as instance variables (`Qasm2String` and `Qasm3String`) that can be used for `isinstance` checks against both OpenQASM 2 and 3 strings ([#745](https://github.com/qBraid/qBraid/pull/745))
- Added `qbraid.runtime.enums.NoiseModel` enum for various noise model options that we may support on managed simulators in the future. This is not a supported feature just yet, so this enum is really just a placeholder. ([#745](https://github.com/qBraid/qBraid/pull/745))
- Added `qbraid.runtime.azure` module with `AzureQuantumProvider` class to enable access to QPUs and simulators from IonQ, Quantinuum, and Rigetti, as well as the Microsoft resource estimator, using Azure credentials ([#723](https://github.com/qBraid/qBraid/pull/723))
- Added `qbraid.programs.typer.QbraidMetaType` custom type instances e.g. `IonQDict`, `BaseQasmInstanceMeta` ([#752](https://github.com/qBraid/qBraid/pull/752))
- Added `qbraid.runtime.Options` for more control over transpile, transform, and validation steps ([#752](https://github.com/qBraid/qBraid/pull/752))
- Added `QbraidProvider.estimate_cost` method to enable getting the estimated number of qBraid credits it will cost to run a quantum job on a given device ([#754](https://github.com/qBraid/qBraid/pull/754))

```python
from azure.quantum import Workspace

from qbraid.runtime.azure import AzureQuantumProvider

workspace = Workspace(...)

provider = AzureQuantumProvider(workspace)

device = provider.get_device("quantinuum.sim.h1-1sc")

circuit = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
creg c0[3];
h q[0];
cx q[0], q[1];
cx q[1], q[2];
measure q[0] -> c0[0];
measure q[1] -> c0[1];
measure q[2] -> c0[2];
"""

job = device.run(circuit, shots=100)
job.wait_for_final_state()

result = job.result()
counts = result.measurement_counts()

print(counts) # {"000": 100}
```

### Improved / Modified
- Updated construction of `TargetProfile` in `QbraidProvider` to populate provider from API instead of defaulting to fixed value 'qBraid'. ([#744](https://github.com/qBraid/qBraid/pull/744))
- Generalized native runtime submission flow to pave the way for support of new devices apart from the QIR simulator. Updated various routines including creating target profile and constructing payload so they are no longer specific to just the `qbraid_qir_simulator`, but can be adapted to new devices that come online fairly quickly. ([#745](https://github.com/qBraid/qBraid/pull/745))
- Defined azure runtime program specs for devices based on provider / input data format ([#752](https://github.com/qBraid/qBraid/pull/752))
- Moved IonQ dict "transform" from IonQ provider into transpiler conversions to be accessible from azure provider as well ([#752](https://github.com/qBraid/qBraid/pull/752))
- Updated `qbraid.runtime.JobStatus` enum to support displaying custom status message if/when available ([#752](https://github.com/qBraid/qBraid/pull/752))
- Updated the `qbraid.runtime.provider.QuantumProvider` methods `get_device` and `get_devices` to now cache the results, speeding up subsequent calls. Users still have ability to bypass this cache by using a `bypass_cache` argument. ([#755](https://github.com/qBraid/qBraid/pull/755))

```python
import time

from qbraid.runtime.native import QbraidProvider

qbraid_provider = QbraidProvider()

start = time.time()
qbraid_devices = qbraid_provider.get_devices() # equivalent to bypass_cache=True
stop = time.time()

print(f"Original time: {stop - start:.6f} seconds")  # 0.837230 seconds

start_cache = time.time()
devices_cached = qbraid_provider.get_devices(bypass_cache=False)
stop_cache = time.time()

print(f"Cached time: {stop_cache - start_cache:.6f} seconds")  # 0.000117 seconds
```

**Unified Result class**

- Refactored runtime provider result handling: the `qbraid.runtime.QuantumJob.result` method now returns a unified `qbraid.runtime.Result` type, providing a consistent interface across all quantum device modalities. Specific result types (e.g., `GateModel`, `AHS`) are represented by the abstract `qbraid.runtime.ResultData` class, with each instance corresponding to a `qbraid.runtime.ExperimentType` (e.g., `GATE_MODEL`, `AHS`, etc.). Experiment-specific methods, such as retrieving measurement counts, are now accessed through the `Result.data` attribute, while general metadata (`job_id`, `device_id`, `success`) remains easily accessible through the `Result` class. This strikes a balance between the structured yet overly nested `qiskit.result.Result` and the disconnected result schemas in `braket.task_result`. See examples below for usage. ([#756](https://github.com/qBraid/qBraid/pull/756))


```python
# Example 1: Gate Model Experiment via QbraidProvider

from qbraid.runtime import QbraidProvider, GateModelResultData

provider = QbraidProvider()
job = provider.get_device("qbraid_qir_simulator").run(circuit, shots=1000)
result = job.result()

# Unified access to metadata and experiment-specific data
print(f"device_id: {result.device_id}, job_id: {result.job_id}, success: {result.success}")
print(result.data.get_counts())  # e.g., {"00": 486, "11": 514}
```

```python
# Example 2: AHS Experiment via BraketProvider

from qbraid.runtime.aws import BraketProvider
from qbraid.runtime import AhsResultData, AhsShotResult

provider = BraketProvider()
job = provider.get("arn:aws:braket:us-east-1::device/qpu/quera/Aquila").run(ahs_program, shots=1000)
result = job.result()

# Unified access to metadata and experiment-specific data
print(f"device_id: {result.device_id}, job_id: {result.job_id}, success: {result.success}")
print(result.data.measurements)  # List of AhsShotResult instances
```
- Improved the `qbraid.transpiler.conversions.qasm2.qasm2_to_ionq` method by adding support for registers in quantum gate arguments. See example below - ([#771](https://github.com/qBraid/qBraid/pull/771))

```python
from qbraid.transpiler.conversions.qasm2 import qasm2_to_ionq

qasm_str = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
x q[0];
y q;
"""

print(qasm2_to_ionq(qasm_str))
```

outputs - 

```python
{'qubits': 3, 'circuit': [{'gate': 'x', 'target': 0}, 
                          {'gate': 'y', 'target': 0}, 
                          {'gate': 'y', 'target': 1}, 
                          {'gate': 'y', 'target': 2}]}
```

### Deprecated
- `result.measurement_counts()` method(s) from result objects retured by `qbraid.runtime.QuantumJob.result()`. Intead, for gate model jobs, measurement counts dictionary now accessible via `result.data.get_counts()`. ([#756](https://github.com/qBraid/qBraid/pull/756))

### Removed
- Removed `qbraid.runtime.DeviceActionType` enum. Functionally replaced by `qbraid.runtime.ExperimentType`. ([#756](https://github.com/qBraid/qBraid/pull/756))
- Removed `qbraid.runtime.QuantumJobResult`. Replaced by `qbraid.runtime.Result`. ([#756](https://github.com/qBraid/qBraid/pull/756))
- Removed `qbraid.runtime.GateModelJobResult`. Replaced by `qbraid.runtime.GateModelResultData`. ([#756](https://github.com/qBraid/qBraid/pull/756))

### Fixed
- Fixed `qbraid.transpiler.transpile` bug where the shortest path wasn't always being favored by the rustworkx pathfinding algorithm. Fixed by adding a bias parameter to both the `ConversionGraph` and `Conversion` classes that attributes as small weight to each conversion by default. ([#745](https://github.com/qBraid/qBraid/pull/745))

### Dependencies
- Added `qbraid[azure]` extra to project ([#723](https://github.com/qBraid/qBraid/pull/723))
- Update sphinx-autodoc-typehints requirement from <2.3,>=1.24 to >=1.24,<2.4 ([#746](https://github.com/qBraid/qBraid/pull/746))
- Update qiskit-ibm-runtime requirement from <0.29,>=0.25.0 to >=0.25.0,<0.30 ([#751](https://github.com/qBraid/qBraid/pull/751))
- Update sphinx-autodoc-typehints requirement from <2.4,>=1.24 to >=1.24,<2.5 ([#750](https://github.com/qBraid/qBraid/pull/750))
- Update amazon-braket-sdk requirement from <1.87.0,>=1.83.0 to >=1.83.0,<1.88.0 ([#748](https://github.com/qBraid/qBraid/pull/748))
- Update pennylane requirement from <0.38 to <0.39 ([#749](https://github.com/qBraid/qBraid/pull/749))
- Added `flair-visual` to `qbraid[visulization]` extra to allow viewing animations of QuEra Simulator jobs run through qBraid. ([#756](https://github.com/qBraid/qBraid/pull/756))

## [0.7.3] - 2024-08-26

### Dependencies
- Update amazon-braket-sdk requirement from <1.85.0,>=1.83.0 to >=1.83.0,<1.87.0 (to support new Rigetti Ankaa-2 device) ([#741](https://github.com/qBraid/qBraid/pull/741))

## [0.7.2] - 2024-08-21

### Added
- Custom pytest decorator to mark remote tests ([#735](https://github.com/qBraid/qBraid/pull/735))
- Attribute `simulator` of type `bool` to `qbraid.runtime.TargetProfile` to replace `qbraid.runtime.DeviceType` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Attribute `local` of type `bool` to `qbraid.runtime.ibm.QiskitBackend.profile` to replace `qbraid.runtime.DeviceType` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Method `qbraid.runtime.GateModelResultBuilder.counts_to_measurements` to abstract redundant code from subclasses ([#735](https://github.com/qBraid/qBraid/pull/735))

### Improved / Modified
- Values of `qbraid.runtime.DeviceActionType` Enum to correspond to programs modules ([#735](https://github.com/qBraid/qBraid/pull/735))
- Static type checking in compliance with `mypy` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Renamed `qbraid.runtime.GateModelResultBuilder.raw_counts` $\rightarrow$ `get_counts` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Updated `qbraid.runtime.TargetProfile` for more idiomatic usage of `pydantic.BaseModel` for field validation and property access ([#735](https://github.com/qBraid/qBraid/pull/735))
- `qbraid.runtime.GateModelResultBuilder.measurements` now returns `None` by default instead of being abstract method. ([#735](https://github.com/qBraid/qBraid/pull/735))

### Removed
- `qbraid.runtime.DeviceType` Enum ([#735](https://github.com/qBraid/qBraid/pull/735))
- PR compliance workflow ([#735](https://github.com/qBraid/qBraid/pull/735))

### Fixed
- qiskit runtime job is terminal state check bug ([#735](https://github.com/qBraid/qBraid/pull/735))
- OQC provider get_devices and device status method bugs. Fixed by adding json decoding step ([#738](https://github.com/qBraid/qBraid/pull/738))

### Dependencies
- Bumped qiskit dependency to qiskit>=0.44,<1.3 ([#737](https://github.com/qBraid/qBraid/pull/737))
