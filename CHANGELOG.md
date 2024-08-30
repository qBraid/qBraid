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
- Added `qbraid.programs.qasm_typer` module containing custom types (`Qasm2String` and `Qasm3String`) that can be used instead of `str` for more accurate static typing, as well as instance variables (`Qasm2Instance` and `Qasm3Instance`) that can be used for `isinstance` checks against both OpenQASM 2 and 3 strings ([#745](https://github.com/qBraid/qBraid/pull/745))
- Added `qbraid.runtime.enums.NoiseModel` enum for various noise model options that we may support on managed simulators in the future. This is not a supported feature just yet, so this enum is really just a placeholder. ([#745](https://github.com/qBraid/qBraid/pull/745))

### Improved / Modified
- Updated construction of `TargetProfile` in `QbraidProvider` to populate provider from API instead of defaulting to fixed value 'qBraid'. ([#744](https://github.com/qBraid/qBraid/pull/744))
- Generalized native runtime submission flow to pave the way for support of new devices apart from the QIR simulator. Updated various routines including creating target profile and constructing payload so they are no longer specific to just the `qbraid_qir_simulator`, but can be adapted to new devices that come online fairly quickly. ([#745](https://github.com/qBraid/qBraid/pull/745))

### Deprecated

### Removed

### Fixed
- Fixed `qbraid.transpiler.transpile` bug where the shortest path wasn't always being favored by the rustworkx pathfinding algorithm. Fixed by adding a bias parameter to both the `ConversionGraph` and `Conversion` classes that attributes as small weight to each conversion by default. ([#745](https://github.com/qBraid/qBraid/pull/745))

### Dependencies

## [0.7.3] - 2024-08-26

### Dependencies
- Bumped Amazon Braket dependency to support new Rigetti Ankaa-2 device ([#741](https://github.com/qBraid/qBraid/pull/741))

## [0.7.2] - 2024-08-21

### Added
- Custom pytest decorator to mark remote tests ([#735](https://github.com/qBraid/qBraid/pull/735))
- Attribute `simulator` of type `bool` to `qbraid.runtime.TargetProfile` to replace `qbraid.runtime.DeviceType` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Attribute `local` of type `bool` to `qbraid.runtime.qiskit.QiskitBackend.profile` to replace `qbraid.runtime.DeviceType` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Method `qbraid.runtime.GateModelJobResult.counts_to_measurements` to abstract redundant code from subclasses ([#735](https://github.com/qBraid/qBraid/pull/735))

### Improved / Modified
- Values of `qbraid.runtime.DeviceActionType` Enum to correspond to programs modules ([#735](https://github.com/qBraid/qBraid/pull/735))
- Static type checking in compliance with `mypy` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Renamed `qbraid.runtime.GateModelJobResult.raw_counts` $\rightarrow$ `get_counts` ([#735](https://github.com/qBraid/qBraid/pull/735))
- Updated `qbraid.runtime.TargetProfile` for more idiomatic usage of `pydantic.BaseModel` for field validation and property access ([#735](https://github.com/qBraid/qBraid/pull/735))
- `qbraid.runtime.GateModelJobResult.measurements` now returns `None` by default instead of being abstract method. ([#735](https://github.com/qBraid/qBraid/pull/735))

### Removed
- `qbraid.runtime.DeviceType` Enum ([#735](https://github.com/qBraid/qBraid/pull/735))
- PR compliance workflow ([#735](https://github.com/qBraid/qBraid/pull/735))

### Fixed
- qiskit runtime job is terminal state check bug ([#735](https://github.com/qBraid/qBraid/pull/735))
- OQC provider get_devices and device status method bugs. Fixed by adding json decoding step ([#738](https://github.com/qBraid/qBraid/pull/738))

### Dependencies
- Bumped qiskit dependency to qiskit>=0.44,<1.3 ([#737](https://github.com/qBraid/qBraid/pull/737))
