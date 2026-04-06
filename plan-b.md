# Plan B: Add RigettiProvider.setup() with Process Management

## Context

After Plan A consolidates URLs into QCSClient, we add a `setup()` method to `RigettiProvider` that:
1. Interactively gathers credentials (refresh token, client ID, issuer)
2. Accepts optional quilc/qvm endpoints or starts local processes
3. Tracks process ownership and cleans up on exit (only kills processes we started)

## Files to modify

- `qbraid/runtime/rigetti/provider.py` — Add `setup()`, `_cleanup()`, helpers, `RigettiProviderError`
- `tests/runtime/rigetti/test_provider.py` — Add `TestRigettiProviderSetup` tests
- `tests/runtime/rigetti/conftest.py` — Add provider fixture

## Steps

### Step 1: Refactor `__init__` — extract `_build_qcs_client()`

Extract client construction into a `@staticmethod` so `setup()` can reuse it. Add process tracking attributes (`_quilc_process`, `_qvm_process`, `_cleanup_registered`).

### Step 2: Add `RigettiProviderError`

Exception class for setup-related errors.

### Step 3: Add static helpers

- `_is_port_in_use(port)` — TCP socket probe
- `_find_binary(name)` — `shutil.which()` + `~/.qbraid/rigetti/bin/`
- `_wait_for_port(port, timeout)` — Poll until port accepts connections

### Step 4: Add process management

- `_start_quilc(binary_path)` — Popen, wait for port 5555
- `_start_qvm(binary_path)` — Popen, wait for port 5000
- `_cleanup()` — terminate/wait/kill owned processes only
- `_signal_handler()` — calls `_cleanup()`, re-raises

### Step 5: Implement `setup()`

Signature: `setup(self, *, refresh_token, client_id, issuer, quilc_endpoint, qvm_endpoint, grpc_endpoint, start_quilc, start_qvm, interactive)`

Flow: gather creds → rebuild QCSClient with URLs → handle quilc/qvm lifecycle → register cleanup

### Step 6: Stub `_download_forest_sdk()`

Raises `RigettiProviderError` with manual install instructions. Full download deferred.

### Step 7: Write tests

All tests mock subprocesses — no real quilc needed.

## Verification

```bash
python -m pytest tests/runtime/rigetti/ -v
tox -e format-check
```
