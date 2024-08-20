# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Types of changes:
- `Added`: for new features.
- `Improved`: for improvements to existing functionality.
- `Deprecated`: for soon-to-be removed features.
- `Removed`: for now removed features.
- `Fixed`: for any bug fixes.

## [Unreleased]

### Added
- Custom pytest decorator to mark remote tests ([#735](https://github.com/qBraid/qBraid/pull/735))
- Attribute `simulator` of type `bool` to `qbraid.runtime.TargetProfile` to replace `qbraid.runtime.DeviceType` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Attribute `local` of type `bool` to `qbraid.runtime.qiskit.QiskitBackend.profile` to replace `qbraid.runtime.DeviceType` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Method `qbraid.runtime.GateModelJobResult.counts_to_measurements` to abstract redundant code from subclasses ([#735](https://github.com/qBraid/qBraid/pull/735))
- `qbraid.runtime.azure` module with `AzureQuantumProvider` class to enable access to QPUs and simulators from IonQ, Quantinuum, and Rigetti, as well as the Microsoft resource estimator, using Azure credentials ([#723](https://github.com/qBraid/qBraid/pull/723))

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

### Improved / modified
- Values of `qbraid.runtime.DeviceActionType` Enum to correspond to programs modules ([#735](https://github.com/qBraid/qBraid/pull/735))
- Static type checking in compliance with `mypy` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Renamed `qbraid.runtime.GateModelJobResult.raw_counts` $\rightarrow$ `get_counts` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Updated `qbraid.runtime.TargetProfile` for more idiomatic usage of `pydantic.BaseModel` for field validation and property access ([#735](https://github.com/qBraid/qBraid/pull/735))
- `qbraid.runtime.GateModelJobResult.measurements` now returns `None` by default instead of being abstract method. ([#735](https://github.com/qBraid/qBraid/pull/735))

### Deprecated

### Removed
- `qbraid.runtime.DeviceType` Enum ([#735](https://github.com/qBraid/qBraid/pull/735))
- PR compliance workflow ([#735](https://github.com/qBraid/qBraid/pull/735))

### Fixed
- qiskit runtime job is terminal state check bug ([#735](https://github.com/qBraid/qBraid/pull/735))