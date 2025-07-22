# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Types of changes:

- `Added`: for new features.
- `Improved / Modified`: for changes to existing functionality.
- `Deprecated`: for soon-to-be removed features.
- `Removed`: for now removed features.
- `Fixed`: for any bug fixes.
- `Dependencies`: for updates to external libraries or packages.

## [Unreleased]

### Added

### Improved / Modified

### Deprecated

### Removed

### Fixed

### Dependencies

## [0.9.8] - 2025-07-22

### Improved / Modified

- Removed legacy `pkg_resources` logic for loading entry points (`qbraid._entrypoints`), as support for Python 3.9 has been dropped and the project now requires Python 3.10 or higher. ([#1002](https://github.com/qBraid/qBraid/issues/1002))
- Populated basis gates property in profile of AWS Braket provider device ([#1003](https://github.com/qBraid/qBraid/pull/1003))
- Throw a `UserWarning` instead of a `ValueError` when checking for the sum of result probabilities from job to be equal
to 1 ([#1004](https://github.com/qBraid/qBraid/pull/1004)).
- House keeping updates ([#1012](https://github.com/qBraid/qBraid/pull/1012))
  - Removed deprecated modules (`qbraid.programs.circuits`, `qbraid.runtime.qiskit`, and `qbraid.runtime.braket`)
  - Updated readme, contributing, citation, and various project config files.
- Updated `QiskitRuntimeProvider` default channel to `ibm_quantum_platform` in preparation for the sunsetting of the IBM Quantum channel in favor of IBM Cloud. See `qiskit-ibm-runtime` updated instructions for [account setup](https://github.com/Qiskit/qiskit-ibm-runtime/blob/0.40.1/README.md#account-setup). ([#1011](https://github.com/qBraid/qBraid/pull/1011))
- Implemented `autoqasm_to_qasm3` conversion extra in transpiler for support of AutoQASM to QASM3 conversion. Added `"autoqasm"` program type to program registry. ([#1013](https://github.com/qBraid/qBraid/pull/1013))

### Fixed

- Fixed handling of IBM job results for different creg names. Specifically, generalized `measurements()` and `get_counts()` methods in `QiskitGateModelResultBuilder` to account for mixed classical register names, and for classical register names other than "c" and "meas". ([#1011](https://github.com/qBraid/qBraid/pull/1011))

### Dependencies

- Updated `qiskit-ibm-runtime` requirement from <0.39,>=0.25.0 to >=0.25.0,<0.41 ([#991](https://github.com/qBraid/qBraid/pull/991))
- Updated `pydantic` requirement from >2.0.0 to >2.0.0,<=2.11.1 ([#991](https://github.com/qBraid/qBraid/pull/991))
- Remove `qiskit-qir` (deprecated) from `qbraid[qir]` dependency extras ([#1001](https://github.com/qBraid/qBraid/pull/1001))
- Updated `amazon-braket-sdk` requirement from >=1.83.0,<1.94.0 to >=1.83.0,<1.96.0 ([#1009](https://github.com/qBraid/qBraid/pull/1009))

## [0.9.7] - 2025-06-13

### Added

- Added `CudaQKernel.serialize` method that converts cudaq program to QIR string for `run_input` compatible format for `QbraidDevice.submit`. ([#972](https://github.com/qBraid/qBraid/pull/972))
- Added support for batch jobs for devices from Azure provider. The `AzureQuantumDevice.submit` method now accepts single and batched `qbraid.programs.QPROGRAM` inputs. ([#953](https://github.com/qBraid/qBraid/issues/953))
- Added `ax_margins` argument to `plot_conversion_graph` to prevent possible clipping. ([#993](https://github.com/qBraid/qBraid/pull/993))

### Improved / Modified

- Updated `TimeStamps` schema to auto-compute `executionDuration` from `createdAt` and `endedAt` if not explicitly provided. ([#983](https://github.com/qBraid/qBraid/pull/983))
- Enhanced `TimeStamps` to accept both `datetime.datetime` objects for `createdAt` and `endedAt` (previously only accepted ISO-formatted strings). ([#983](https://github.com/qBraid/qBraid/pull/983))
- Added a `measurement_probabilties` argument to the `GateModelResultData` class. ([#785](https://github.com/qBraid/qBraid/issues/785))

### Removed

- Removed `queue_position` from result details, as it is always `None` and not applicable. ([#983](https://github.com/qBraid/qBraid/pull/983))

### Fixed

- Fixed lazy importing bug in `plot_histogram` method ([#972](https://github.com/qBraid/qBraid/pull/972))
- Fixed bug which caused all `braket` conversions to be unavailable if `cirq` was not installed due to an eager top-level import in `braket_to_cirq.py` which should have been done lazily ([#982](https://github.com/qBraid/qBraid/pull/982))
- Made Pulser unit test version-agnostic to support any installed Pulser version. ([#983](https://github.com/qBraid/qBraid/pull/983))
- Fixed the bug that included unregistered program type in `ConversionGraph`. ([#986](https://github.com/qBraid/qBraid/pull/986))

### Dependencies

- Migrated to `setuptools>=77` due to TOML-table based `project.license` deprecation in favor of SPDX expression in compliance with [PEP 639](https://peps.python.org/pep-0639) ([#973](https://github.com/qBraid/qBraid/pull/973))
- Bumped `qbraid-core` dependency to v0.1.39 ([#975](https://github.com/qBraid/qBraid/pull/975))

## [0.9.6] - 2025-05-02

### Added

- Added `QbraidJob.async_result()` to support async result retrieval using `await`. ([#945](https://github.com/qBraid/qBraid/pull/945))
- Added `QbraidDevice.set_target_program_type`, allowing you to set a specific `ProgramSpec` (from `TargetProfile`) alias as the default ([#952](https://github.com/qBraid/qBraid/pull/952)). For example, if a device supports both "qasm2" and "qasm3", you can now restrict transpilation to one format:

```python
from qbraid.runtime import IonQProvider

provider = IonQProvider()

device = provider.get_device("simulator")

device.metadata()["runtime_config"]["target_program_type"] # ['qasm2', 'qasm3']

device.set_target_program_type("qasm2")

device.metadata()["runtime_config"]["target_program_type"] # 'qasm2'
```

However the original `TargetProfile.program_spec` value remains frozen:

```python
device.profile.program_spec
# [<ProgramSpec('builtins.str', 'qasm2')>,
#  <ProgramSpec('builtins.str', 'qasm3')>]
```

- Added support for Pasqal devices through the `AzureQuantumProvider` with `pulser` program type ([#947](https://github.com/qBraid/qBraid/pull/947)). For example:

```python
import numpy as np
import pulser
from azure.quantum import Workspace
from qbraid.runtime import AzureQuantumProvider

connection_string = "[Your connection string here]"
workspace = Workspace.from_connection_string(connection_string)

provider = AzureQuantumProvider(workspace=workspace)

input_data = {}

qubits = {
    "q0": (0, 0),
    "q1": (0, 10),
    "q2": (8, 2),
    "q3": (1, 15),
    "q4": (-10, -3),
    "q5": (-8, 5),
}
register = pulser.Register(qubits)

sequence = pulser.Sequence(register, pulser.DigitalAnalogDevice)
sequence.declare_channel("ch0", "rydberg_global")

amp_wf = pulser.BlackmanWaveform(1000, np.pi)
det_wf = pulser.RampWaveform(1000, -5, 5)
pulse = pulser.Pulse(amp_wf, det_wf, 0)
sequence.add(pulse, "ch0")

device = provider.get_device("pasqal.sim.emu-tn")

job = device.run(sequence, shots=1)

job.wait_for_final_state()

job.status()  # <COMPLETED: 'job has successfully run'>

result = job.result()

result.data.get_counts()  # {'100110': 1}
```

- Added support for transpiling between [pyqpanda3](https://pyqpanda-toturial.readthedocs.io/) and QASM2 with `pyqpanda3` program type ([#963](https://github.com/qBraid/qBraid/pull/963))

### Improved / Modified

- Prepped tests for supporting `qiskit>=2.0` ([#955](https://github.com/qBraid/qBraid/pull/955))
- Updated the `qbraid.runtime.aws.BraketProvider` to include an `aws_session_token` during initialization. Users can now choose to supply their temporary AWS credentials instead of permanent account secrets to access AWS - ([#968](https://github.com/qBraid/qBraid/pull/968))

```python
from qbraid.runtime.aws import BraketProvider

aws_access_key = "YOUR_TEMP_ACCESS_KEY"
aws_secret_key = "YOUR_TEMP_SECRET_KEY"
aws_session_token = "YOUR_CURRENT_SESSION_TOKEN"

provider = BraketProvider(aws_access_key, aws_secret_key, aws_session_token)
print(provider.get_devices())

# [<qbraid.runtime.aws.device.BraketDevice('arn:aws:braket:us-west-1::device/qpu/rigetti/Ankaa-3')>,
#  <qbraid.runtime.aws.device.BraketDevice('arn:aws:braket:us-east-1::device/qpu/quera/Aquila')>,
#  ...]
```

### Removed

- Removed the `strict=False` parameter from the `pydantic_core.core_schema.union_schema()` calls in the `__get_pydantic_core_schema__` method(s) in `qbraid.runtime.schemas.base`. `strict` parameter no longer included in the `pydantic-core` API for that method as of release [v0.2.30](https://github.com/pydantic/pydantic-core/releases/tag/v2.30.0), PR [#1638](https://github.com/pydantic/pydantic-core/pull/1638). ([#946](https://github.com/qBraid/qBraid/pull/946))

### Fixed

- Fixed Amazon Braket remote test by changing catch `JobStateError` to `TimeoutError` ([#948](https://github.com/qBraid/qBraid/pull/948))
- Fixed upper bound of html length check in pytket circuit drawer test ([#950](https://github.com/qBraid/qBraid/pull/950))
- Fixed simulator check for Azure target profiles ([#956](https://github.com/qBraid/qBraid/pull/956))

### Dependencies

- Added `pydantic-core` to project requirements ([#946](https://github.com/qBraid/qBraid/pull/946))
- Updated `pyqasm` dependency to `>=0.3.2, <0.4.0` ([#964](https://github.com/qBraid/qBraid/pull/964))

## [0.9.5] - 2025-03-26

### Added

- Added `qbraid.runtime.get_providers()` and corresponding `qbraid.runtime.PROVIDERS` which is a list of the provider aliases that can be passed to the `qbraid.runtime.load_job()`function. ([#887](https://github.com/qBraid/qBraid/pull/887))

```python
>>> from qbraid.runtime import PROVIDERS
>>> print(PROVIDERS)
['aws', 'azure', 'ibm', 'ionq', 'oqc', 'qbraid']
```

- Added bin script + logic in version bump workflow to automatically update `CITATION.ff` ([#915](https://github.com/qBraid/qBraid/pull/915))
- Added a workflow for deploying to GitHub Pages on release publication or manual dispatch. ([#917](https://github.com/qBraid/qBraid/pull/917))
- Added `pytest.skip` statements to Azure remote tests to skip them when the relevant device is not online. ([#934](https://github.com/qBraid/qBraid/pull/934))

### Improved / Modified

- Disabled validation step in remote (native) IonQ runtime test when constructing `IonQDict` via `qiskit-ionq` ([#915](https://github.com/qBraid/qBraid/pull/915))
- Enabled loading `azure.quantum.Workspace` from `AZURE_QUANTUM_CONNECTION_STRING` environment variable in `AzureQuantumProvider` class ([#915](https://github.com/qBraid/qBraid/pull/915))
- Populated basis gates property in profile of IBM Quantum provider backends ([#930](https://github.com/qBraid/qBraid/pull/930))
- Adjusted docs side navigation search styling for better alignment. ([#917](https://github.com/qBraid/qBraid/pull/917))
- Added support for interpreting `zz` as a QIS gate in `openqasm3_to_ionq` and refactored `determine_gateset` accordingly ([#917](https://github.com/qBraid/qBraid/pull/917))
- Modified `openqasm3_to_ionq` to emit warning instead of raise error when circuits contains measurements. ([#917](https://github.com/qBraid/qBraid/pull/917))
- Set 20 minute timeout for daily github actions workflow ([#919](https://github.com/qBraid/qBraid/pull/919))
- Temporarily skip remote OQC tests because the QCaaS servers will be offline until March 17, 2025. ([#931](https://github.com/qBraid/qBraid/pull/931))
- Updated `QiskitRuntimeProvider` class with better docstring annotations for specifying either `ibm_quantum` or `ibm_cloud` channel ([#933](https://github.com/qBraid/qBraid/pull/933))
- `QuantumJob.wait_for_final_state` now raises `TimeoutError` on timeout instead of `JobStateError` ([#943](https://github.com/qBraid/qBraid/pull/943))
- Updated job ID type annotations to support both `str` and `int` (for compatibility with QUDORA) ([#943](https://github.com/qBraid/qBraid/pull/943))
- Updated `qbraid._logging` so that `logging.basicConfig` is only set if `LOG_LEVEL` environment variable is defined. ([#943](https://github.com/qBraid/qBraid/pull/943))

### Removed

- Removed `qasm3_drawer` function in favor of `pyqasm.draw` ([#943](https://github.com/qBraid/qBraid/pull/943))

### Fixed

- Updated `bump-version.yml` to track `qbraid/_version.py` instead of `pyproject.toml`. ([#917](https://github.com/qBraid/qBraid/pull/917))
- Fixed bug where `BraketQuantumTask._task.arn` undefined if instaniated without `AwsQuantumTask` object ([#917](https://github.com/qBraid/qBraid/pull/917))
- Fixed bug where doing `repr(result)` would cause `result.details['opeQasm']` to be set to `...` ([#919](https://github.com/qBraid/qBraid/pull/919))
- Loosened relative tolerance for `distribute_counts` function in requiring probs to sum to 1 from default 1e-9 to 1e-7 ([#933](https://github.com/qBraid/qBraid/pull/933))

### Dependencies

- Updated qBraid-CLI dependency to >= 0.10.0 ([#915](https://github.com/qBraid/qBraid/pull/915))
- Migrated from `bloqade` to `bloqade-analog` ([#920](https://github.com/qBraid/qBraid/pull/920))
- Added `pyqasm[visualization]` to optional dependencies ([#943](https://github.com/qBraid/qBraid/pull/943))

## [0.9.4] - 2025-02-20

### Added

- Added `qibo` to dynamic `QPROGRAM_REGISTRY` imports ([#891](https://github.com/qBraid/qBraid/pull/891))
- Fixed `plt.show` / `plt.save_fig` bug in `plot conversion_graph` ([#893](https://github.com/qBraid/qBraid/pull/893))
- Added [IonQ Forte Enterpres](https://ionq.com/quantum-systems/forte-enterprise) devices to `IonQProvider` runtime tests ([#894](https://github.com/qBraid/qBraid/pull/894))
- Added `CudaQKernel` class to support `cudaq.PyKernel` as "native" program type ([#895](https://github.com/qBraid/qBraid/pull/895))
- Added `qibo_to_qasm2` conversion to transpiler ([#895](https://github.com/qBraid/qBraid/pull/895))
- Added `stim` to dynamic `QPROGRAM_REGISTRY` imports and `stim_to_cirq` conversion to transpiler ([#895](https://github.com/qBraid/qBraid/pull/895))
- Added `Qasm2KirinString` metatype to support qasm2 strings adapted for QuEra kirin qasm parser through qBraid native runtime. ([#896](https://github.com/qBraid/qBraid/pull/896))
- Added `translate` functions as alias for `transpile`, but also that can chain multiple conversions together ([#899](https://github.com/qBraid/qBraid/pull/899)). For example:

```python
from qbraid import translate

circuit_out = translate(circuit_in, "qasm3", "braket", "cirq")
```

- Added logger `DEBUG` statements to QuantumDevice that track with the steps in job submission runtime ([#906](https://github.com/qBraid/qBraid/pull/906))
- Expanded list of natively supported hardware vendors to include Rigetti, OQC, and IQM ([#906](https://github.com/qBraid/qBraid/pull/906))
- Added `qbraid.runtime.load_provider` function to allow instantiating provider via a single interface using entrypoints based on provider name ([#906](https://github.com/qBraid/qBraid/pull/906))

```python
from qbraid.runtime import load_provider, QbraidProvider

provider = load_provider("qbraid")
assert isintance(provider, QbraidProvider)

# follows suit for 'aws', 'ibm', 'oqc', 'azure', 'ionq', etc.
```

### Improved / Modified

- Updated conversion graph and `QPROGRAM_REGISTRY` on README.md ([#891](https://github.com/qBraid/qBraid/pull/891))
- Improved `plot_runtime_conversion_scheme` by removing edges not within `ConversionScheme.max_path_depth` ([#893](https://github.com/qBraid/qBraid/pull/893))
- Updated native runtime `QbraidProvider` and `QbraidDevice` to support list of `ProgramSpec` loaded from API "runInputTypes" of type `list[str]` instead of single "runPackage" of type `str`. ([#896](https://github.com/qBraid/qBraid/pull/896))
- Updated `qasm3_to_ionq`: no longer need to check if `pyqasm` is installed as it is now a core project dependency ([#905](https://github.com/qBraid/qBraid/pull/905))

### Fixed

- Handling of empty counts dict in `format_counts` pre-processing function ([#899](https://github.com/qBraid/qBraid/pull/899))
- Skipping NEC remote tests if device is not online ([#899](https://github.com/qBraid/qBraid/pull/899))

## [0.9.3] - 2025-01-27

### Added

- Added `cudaq` to `QPROGRAM_REGISTRY` dynamic import list ([#882](https://github.com/qBraid/qBraid/pull/882))
- Added `qiskit_ionq` conversion to transpiler and refactored `IonQDevice._apply_qiskit_ionq_conversion` accordingly ([#882](https://github.com/qBraid/qBraid/pull/882))
- Added `qbraid.runtime.load_job` function that uses entrypoints to load provider job class and create instance with job id ([#883](https://github.com/qBraid/qBraid/pull/883))

```python
from qbraid.runtime import load_job

qbraid_native_job = load_job("<job_id>", "qbraid") # qbraid.runtime.QbraidJob
qbraid_braket_task = load_job("<task_arn>", "aws") # qbraid.runtime.BraketQuantumTask
...
```

- Added `QuantumProgram.serialize` method to streamline creation of `ProgramSpec` classes in `QbraidProvider` ([#883](https://github.com/qBraid/qBraid/pull/883))

### Improved / Modified

- Switched all `QbraidJob` sub-classes to only require `job_id` as positional argument, and any other args that used to be required for auth can now be loaded with credentials from environment variables ([#883](https://github.com/qBraid/qBraid/pull/883))
- Allow some minimum tolerance when checking for the sum of result probabilities from job to be equal to 1 ([#889](https://github.com/qBraid/qBraid/pull/889))

### Fixed

- Updated plot conversion graph test to account for rustworkx v0.16.0 release ([#880](https://github.com/qBraid/qBraid/pull/882))

## [0.9.2] - 2025-01-23

### Added

- Added `id` gate to list of supported IonQ gates (but is still skipped in `IonQDict` conversion step) ([#880](https://github.com/qBraid/qBraid/pull/880))
- Added `qiskit-ionq` integration into `IonQDevice.run` method so that if user has `qiskit-ionq` installed, we just go directly through their native `qiskit.QuantumCircuit` $\rightarrow$ `IonQDict` conversion rather than using our own. ([#880](https://github.com/qBraid/qBraid/pull/880))

```python
from qiskit import QuantumCircuit

from qbraid.runtime import IonQProvider
from qbraid.programs.gate_model.ionq import GateSet


circuit = QuantumCircuit(1)
circuit.u(0.1, 0.2, 0.3, 0)

provider = IonQProvider()
device = provider.get_device("simulator")

job = device.run(circuit, shots=100, gateset=GateSet.NATIVE, ionq_compiler_synthesis=False)
```

If `qiskit-ionq` not installed, the above code will fail. But with `qiskit-ionq` installed, it will work.

### Improved / Modified

- Improved `IonQDevice.transform` method with try/except logic using `pyqasm.unroll` ([#880](https://github.com/qBraid/qBraid/pull/880))

### Fixed

- Fixed type checking in transpiler `weight` and `requires_extras` annotations / decorators ([#880](https://github.com/qBraid/qBraid/pull/880))

## [0.9.1] - 2025-01-14

### Added

- Added support for OpenQASM 3.0 to CUDA-Q kernel transpilation ([#857](https://github.com/qBraid/qBraid/pull/857)). Usage example:

```python
In [1]: from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_cudaq
In [2]: program = """
   ...: OPENQASM 3.0;
   ...: include "stdgates.inc";
   ...: qubit q;
   ...: bit b;
   ...: h q;
   ...: b = measure q;
   ...: """

In [3]: print(openqasm3_to_cudaq(program))
module attributes {quake.mangled_name_map = {__nvqpp__mlirgen____nvqppBuilderKernel_YA8BX8A573 = "__nvqpp__mlirgen____nvqppBuilderKernel_YA8BX8A573_PyKernelEntryPointRewrite"}} {
  func.func @__nvqpp__mlirgen____nvqppBuilderKernel_YA8BX8A573() attributes {"cudaq-entrypoint"} {
    %0 = quake.alloca !quake.veq<1>
    %1 = quake.extract_ref %0[0] : (!quake.veq<1>) -> !quake.ref
    call @__nvqpp__mlirgen____nvqppBuilderKernel_X4UUVQL2OR(%1) : (!quake.ref) -> ()
    %measOut = quake.mz %1 name "" : (!quake.ref) -> !quake.measure
    return
  }
  func.func @__nvqpp__mlirgen____nvqppBuilderKernel_X4UUVQL2OR(%arg0: !quake.ref) {
    quake.h %arg0 : (!quake.ref) -> ()
    return
  }
}
```

- Introduced `max_attempts` parameter in `random_circuit` function ([#871](https://github.com/qBraid/qBraid/pull/871))
- Added `prepare` as `RuntimeOption` field in `QuantumDevice` ([#871](https://github.com/qBraid/qBraid/pull/871))
- Added `validate_for_gateset` method in `IonQProgram` ([#871](https://github.com/qBraid/qBraid/pull/871))

### Improved / Modified

- Changed `QuantumDevice.to_ir` method to `QuantumDevice.prepare` ([#871](https://github.com/qBraid/qBraid/pull/871))
- Updated `remove_idle_qubits` function for updated `qiskit` version ([#871](https://github.com/qBraid/qBraid/pull/871))
- Incorporated `SamplerV2` and job / result primitives for qiskit migration ([#871](https://github.com/qBraid/qBraid/pull/871))

### Fixed

- Fixed `random_circuit` function so that when specifying `ionq`, the resulting program only uses gates supported by IonQ. ([#871](https://github.com/qBraid/qBraid/pull/871))
- Qiskit migration fixes ([#876](https://github.com/qBraid/qBraid/pull/876)):
  - fix num args passed to `SamplerV2.run`
  - raise `NotImplementedError` for `QiskitJob.queue position()` if not available
  - Account for `DataBin` pub result data type `c` attribute instead of `meas`

## [0.9.0] - 2024-12-19

### Added

- Added testing code coverage for custom `rzz`, `u3`, and `u2` for Cirq $\rightarrow$ PyQuil ([#862](https://github.com/qBraid/qBraid/pull/862))

### Improved / Modified

- Vastly reduced size of `qbraid.passes.qasm`, `qbraid.programs.gate_model.qasm2` and `qbraid.programs.gate_model.qasm3` modules as a result of `pyqasm` integration. ([#808](https://github.com/qBraid/qBraid/pull/808))
- Restricted PyPI publish jobs to specific actors for better security and maintainability. ([#862](https://github.com/qBraid/qBraid/pull/862))
- Updated `MANIFEST.in` to refine file inclusion/exclusion and enhanced `pyproject.toml` by adjusting dependencies and aligning with `requirements.txt`. ([#862](https://github.com/qBraid/qBraid/pull/862))
- Enhanced qbraid transpiler QASM2 to Cirq for external gate handling, and updated custom Cirq `RZZGate` to use radians convention to more closely match cirq API. ([#862](https://github.com/qBraid/qBraid/pull/862))

### Removed

- Dropped support for Python 3.9 ([#808](https://github.com/qBraid/qBraid/pull/808))

### Fixed

- Removed Python 3.9 from daily test matrix ([#862](https://github.com/qBraid/qBraid/pull/862))
- Fixed OQC test edge case datetime bug ([#862](https://github.com/qBraid/qBraid/pull/862))

### Dependencies

- Integrated `pyqasm` as project dependency. ([#808](https://github.com/qBraid/qBraid/pull/808))

## [0.8.10] - 2024-12-13

### Fixed

- Fixed type annotations for constraint parameters to support nested lists and mixed types, such as list[list[str]] and list[list[Union[str, int]]] in qbraid/runtime/schemas/experiment.py.([#859](https://github.com/qBraid/qBraid/pull/859)) [[1]](diffhunk://#diff-a7087c56dd9323acc4777f8bc0bfab64908f18a93e9e6e6fa8abdb663da8fbfaL236-R244) [[2]](diffhunk://#diff-a7087c56dd9323acc4777f8bc0bfab64908f18a93e9e6e6fa8abdb663da8fbfaL259-R266)
- Updates to tests: Modified the test_qubo_solve_params_model function to reflect the updated types for the constraint parameters in tests/runtime/test_schemas.py.

### Added

- Added `p` to `z` gate name mapping to `openqasm3_to_ionq` conversion ([#854](https://github.com/qBraid/qBraid/pull/854))
- Added `preflight` parameter to the `submit` method and to the `RuntimeJobModel` class ([#856](https://github.com/qBraid/qBraid/pull/856))
- Added remote test for native IonQ runtime ([#856](https://github.com/qBraid/qBraid/pull/856))
- Added `distribute_counts` function to adjust probabilistic counts ensuring the total equals the number of shots. ([#858](https://github.com/qBraid/qBraid/pull/858))
- Added support for controlled gates in `openqasm3_to_ionq` conversion ([#858](https://github.com/qBraid/qBraid/pull/858)):

```text
cx, cy, cz, crx, cry, crz, ch, ccnot, cs, csi, ct, cti, cv, cvi
```

### Improved / Modified

- Unit tests that require the `pyqir` dependency are now automatically skipped if pyqir is not installed. ([#846](https://github.com/qBraid/qBraid/pull/846))
- Renamed the function `replace_gate_name` to `replace_gate_names` and updated its implementation to accept a dictionary of gate name mappings instead of individual old and new gate names. (`qbraid/passes/qasm/compat.py`) ([#854](https://github.com/qBraid/qBraid/pull/854))
- Updated the `IonQDevice.transform` method to replace gate names in the input using the newly defined `IONQ_GATE_MAP` before loading and transforming the program ([#855](https://github.com/qBraid/qBraid/pull/855))
- Updated gate naming conventions in `IONQ_QIS_GATES` list for consistency with [IonQ supported gates API](https://docs.ionq.com/api-reference/v0.3/writing-quantum-programs#supported-gates) ([#856](https://github.com/qBraid/qBraid/pull/856))
- Updated the `rebase` function to include `gate_mappings` and `case_sensitive` parameters for gate name replacement.([#856](https://github.com/qBraid/qBraid/pull/856))
- Updated the `rebase` function to handle gate mappings with predicates. ([#858](https://github.com/qBraid/qBraid/pull/858))
- Refactored gate mappings and added validation for gate parameters and qubit counts in `openqasm3_to_ionq` conversion ([#858](https://github.com/qBraid/qBraid/pull/858))
- Integrated `distribute_counts` function in `convert_to_counts` method in `IonQJob` ([#858](https://github.com/qBraid/qBraid/pull/858))

### Fixed

- Fixed `nec_vector_annealer` remote test by generalizing solutions (results) check ([#852](https://github.com/qBraid/qBraid/pull/852))

## [0.8.9] - 2024-12-06

### Added

- Added "new" classes to the relevant runtime module scopes ([#843](https://github.com/qBraid/qBraid/pull/843)):

  - `qbraid.schemas`: `AhsExperimentMetadata` model, `USD` and `Credits` classes
  - `qbraid.runtime`: `ValidationLevel` enum
  - `qbraid.runtime.native`: Device-specific `ResultData` subclasses

- Added `plot_runtime_conversion_scheme` function to visualize the conversion graph and the target program types for a specific device. This enhancement clarifies which program types are available as input when submitting a quantum job to a particular device. See usage example below. ([#845](https://github.com/qBraid/qBraid/pull/845))

```python
from qbraid.runtime import QbraidProvider
from qbraid.visualization import plot_runtime_conversion_scheme

provider = QbraidProvider()

device = provider.get_device("qbraid_qir_simulator")

device.update_scheme(max_path_depth=1)

plot_runtime_conversion_scheme(device, legend=True)
```

- Display seed in bottom left corner of conversion graph if `plot_conversion_graph` called with `legend=True` ([#849](https://github.com/qBraid/qBraid/pull/849))

### Improved / Modified

- Made remote tests for `QbraidDevice("nec_vector_annealer")` more robust ([#843](https://github.com/qBraid/qBraid/pull/843))
- Updated doc string & improved type hinting of `qbraid.load_program` ([#849](https://github.com/qBraid/qBraid/pull/849))

### Fixed

- Resolved an issue where passing `bloqade.builder.assign.BatchAssign` to `QbraidDevice("quera_aquila")` caused the transpile step to incorrectly wrap its output list in another list, leading to errors in `QuantumDevice.validate` and `QuantumDevice.to_ir`. The native `QbraidDevice` class now adapts when the transpile input is a single object but the output is a list, properly iterating through the sub-batch for final submission. ([#843](https://github.com/qBraid/qBraid/pull/843))

## [0.8.8] - 2024-11-25

### Added

- Added support for specifying different `quera_qasm_simulator` backends in the `QbraidDevice.run` method using the "backend" keyword argument (e.g., "cirq", "cirq-gpu") ([#836](https://github.com/qBraid/qBraid/pull/836))
- Add native runtime support for AHS experiment types, specifically for QuEra Aquila device ([#837](https://github.com/qBraid/qBraid/pull/837))
- Added `QbraidJob.queue_position()` method ([#838](https://github.com/qBraid/qBraid/pull/838))

### Improved / Modified

- Enhanced type hinting for the `Result.data` property by leveraging a custom `typing.TypeVar`, enabling automatic adaptation to the specific `ResultData` subclass being accessed. ([#836](https://github.com/qBraid/qBraid/pull/836))
- Improved type annotations and updated runtime test cases / structure ([#837](https://github.com/qBraid/qBraid/pull/837))
- Updated validators for `AhsExperimentMetadata` pydantic model/schema ([#838](https://github.com/qBraid/qBraid/pull/838))

## [0.8.7] - 2024-11-21

### Improved / Modified

- `OQCDevice.transform()` method now removes "include" statements from qasm strings, as they are not supported by the OQC cloud. ([#831](https://github.com/qBraid/qBraid/pull/831))
- Extended `OQCDevice.get_next_window()` to fallback and attempt to extract next (or current) start window from `OQCClient.get_qpu_execution_estimates()` if `OQCClient.get_next_window()` raises an exception (e.g. for non-AWS windows). Now can return next widow `datetime` for Toshiko QPU. ([#831](https://github.com/qBraid/qBraid/pull/831))
- Updated `OQCDevice.submit()` to so that we no longer explicitly set the `CompilerConfig` defaults and rather leave optional arguments as `None` if not provided. ([#831](https://github.com/qBraid/qBraid/pull/831))

### Removed

- Removed `qbraid.passes.compat.rename_qasm_registers()`. Function did not work properly, and is no longer even needed for OQC runtime as submission format is now `qasm3`, not `qasm2`. ([#831](https://github.com/qBraid/qBraid/pull/831))

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
- Updated native runtime logic for NEC vector annealer to support "qubo" program spec type. Offset argument / attribute removed from `qbraid.programs.annealing.Problem`. `QbraidDevice.run` flow now derives "offset" paramater from `params` argument (of type `QuboSolveParams`, now required). This allows a more straightfoward procedure (with more visiblity) when submitting programs from `pyqubo.Module`. See code example below. ([#820](https://github.com/qBraid/qBraid/pull/820))

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
- OQC provider url + timeout params added to `__init__`, and target profile updates to include new device metadata fields returned by `OQCClient`, particularly in relation to Toshiko QPU ([#825](https://github.com/qBraid/qBraid/pull/825))
- Updated `random_circuit` function to use transpiler to consider all possible random circuit generators package funcs starting from the one with the closest conversion path to the specified target package. Reverses the logic of `ConversionGraph.get_sorted_closest_targets` with new function `ConversionGraph.get_sorted_closest_sources()` ([#829](https://github.com/qBraid/qBraid/pull/829))

### Fixed

- Fixed `qasm2_to_qasm3()` conversion error cause by `qbraid/transpiler/conversions/qasm2/qelib_qasm3.qasm` not being included in `MANIFEST.in` ([#825](https://github.com/qBraid/qBraid/pull/825))
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
- Updated `QbraidJob.result` method to return `AnnealingResultData` or `NECVectorAnnealerResultData` instances for annealing and NEC vector annealer experiments, respectively. ([#768](https://github.com/qBraid/qBraid/pull/768))
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
- Added `DeviceData` schema to improve the way we process JSON device data recieved from the qBraid API ([#762](https://github.com/qBraid/qBraid/pull/762))

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
