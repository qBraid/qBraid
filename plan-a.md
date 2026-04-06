# Plan A: Consolidate URLs into QCSClient, Remove ExecutionOptions

## Context

`QCSClient` already supports `grpc_api_url`, `quilc_url`, and `qvm_url` as constructor parameters. Currently `RigettiDevice` manually builds `ExecutionOptions` and passes them to every API call — this is redundant. The SDK uses the client's `grpc_api_url` by default when `execution_options=None` and `quantum_processor_id` is provided.

## Files to modify

- `qbraid/runtime/rigetti/provider.py` — Pass URL params to QCSClient constructor
- `qbraid/runtime/rigetti/device.py` — Remove ExecutionOptions, use `self._qcs_client.quilc_url`
- `qbraid/runtime/rigetti/job.py` — Remove `execution_options` from all API calls
- `tests/runtime/rigetti/test_rigetti_device.py` — Remove `TestBuildExecutionOptions`, update submit tests
- `tests/runtime/rigetti/test_rigetti_job.py` — Remove `execution_options` assertions
- `tests/runtime/rigetti/conftest.py` — Add `quilc_url` to mock client

## Steps

### Step 1: Update `provider.py`

Pass `grpc_api_url`, `quilc_url`, `qvm_url` to `QCSClient(...)` constructor, reading from env vars with defaults.

### Step 2: Simplify `device.py`

- Remove `_build_execution_options()`, `self.execution_options`, constants, and related imports
- In `transform()`: use `self._qcs_client.quilc_url` instead of `os.getenv(...)`
- In `_submit()`: remove `execution_options` from `qpu_submit()` call

### Step 3: Simplify `job.py`

Remove `execution_options=self._device.execution_options` from `retrieve_results()` and `cancel_job()` calls.

### Step 4: Update tests

- Delete `TestBuildExecutionOptions` class
- Update submit/status/cancel/result tests to remove execution_options assertions
- Add `quilc_url` property to `mock_qcs_client` fixture

## Verification

```bash
python -m pytest tests/runtime/rigetti/ -v
tox -e format-check
```
