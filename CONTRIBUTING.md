# Contributing

Welcome! Happy to see you want to help us make the project better.

The following is a summary of relevant commands, procedures, and best practices for developers contributing to qBraid. _Note:_ Some commands are specific to a Debian environment, and unless stated otherwise, all commands are assumed to be executed from the qBraid repository root.

## Installing from source

You can install the qBraid-SDK from source by cloning this repository and running a pip install command in the root directory:

```bash
git clone https://github.com/qbraid/qBraid.git
cd qBraid
pip install -e .
```

## Documentation

To generate the API reference documentation locally:

```bash
pip install 'tox>=4.2'
tox -e docs
```

Alternatively:

```bash
pip install -r docs/requirements.txt
cd docs
make html
```

Both methods will run Sphinx in your shell. If the build results in an `InvocationError` due to a
duplicate object description, try `rm docs/stubs/*` to empty the old stubs directory, and then
re-start the build. If the build succeeds, it will say `The HTML pages are in build/html`. You can
view the generated documentation in your browser (on OS X) using:

```bash
open build/html/index.html
```

You can also view it by running a web server in that directory:

```bash
cd build/html
python3 -m http.server
```

Then open your browser to `http://localhost:8000`. If you make changes to the docs that aren't
reflected in subsequent builds, run `make clean html`, which will force a full rebuild.

### API Docs

Our docs are written using reStructuredText (reST), which is the default plaintext markup language used by [Sphinx](https://docs.readthedocs.io/en/stable/intro/getting-started-with-sphinx.html). It's pretty straightforward once you get the hang of it. If you're unfamiliar, [reStructuredText Primer](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#restructuredtext-primer) is a good place to start.

### Docstrings

This project uses [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)
to specify attributes, arguments, exceptions, returns, and other related info. The docstrings are compiled into HTML using Sphinx,
so to add relative links, in-line markup, bulleted lists, code-blocks, or do other types of formatting inside of docstrings, use
the `reST` syntax mentioned (linked) above.

## Testing

To run all unit tests:

```bash
pip install 'tox>=4.2'
tox -e unit-tests
```

You can pass in additional `pytest` arguments directly to `tox` as follows:

```bash
tox -e unit-tests -- {your-arguments}
```

For example, to run just qBraid runtime tests, excluding all remote tests:

```bash
tox -e unit-tests -- tests/runtime --remote false
```

Alternatively:

```bash
pip install pytest
pytest {path-to-test}
```

Running unit tests with tox will automatically generate a coverage report, which can be viewed by
opening `tests/_coverage/index.html` in your browser. The latest code coverage report generated
from the `main` branch can be viewed at https://app.codecov.io/gh/qBraid/qBraid/tree/main.

To run linters and doc generators and unit tests:

```bash
tox
```

### Testing Philosophy

Every PR should include unit tests covering the code it changes. Coverage is a floor, not the
goal — tests exist to expose bugs and prevent regressions, not to turn a number green.

**Avoid self-reinforcing tests.** A test that feeds a helper fabricated input and asserts the
helper's current output passes just as happily when the helper is wrong. Test what the function
is actually trying to achieve, end-to-end, rather than restating its implementation.

**Mock data must mirror production.** QRNs, job documents, device documents, result payloads,
user records, and timestamps should be copied from — or modeled directly on — real records.
Invented fixtures tend to omit required fields, use the wrong types, or miss enum values, which
produces tests that pass against a shape the API never returns.

Where a vendor SDK ships response models (pydantic or otherwise), build fixtures by passing a raw
payload through the vendor's own validator rather than hand-constructing model objects. The
fixture is then checked against the real schema on every run, and upstream drift surfaces as a
validation error naming the field instead of a silently divergent test.

**Write the test that would have caught the bug.** When you fix a bug, add a test reproducing the
exact scenario, and say so in the test's docstring. For a new feature, work through what goes
wrong with real inputs — malformed or partial vendor responses, missing optional fields, single
vs. batch paths, unmapped enum members — and cover those.

**Verify against the real service at least once.** Mocked tests can only confirm the code matches
the shape you assumed. Before a vendor integration merges, exercise it against the live API with
real credentials and capture what comes back; use those payloads as the basis for the mocked
fixtures. Keep the credentialed tests in the suite behind the `remote` marker
(see [Running Tests Requiring Remote Access](#running-tests-requiring-remote-access)) so they are
skipped by default but can be re-run whenever the vendor's API changes.

### Running Tests Requiring Remote Access

Some of our tests interact with remote APIs and require specific credentials, such as those from qBraid or other third-party services. By default, these tests do not run to avoid unintended network operations and the need for all developers to have access to necessary credentials.

**Enabling Remote Tests:**

1. **Environment Variable**: Set the `QBRAID_RUN_REMOTE_TESTS` environment variable to `true` to enable these tests. They will run if this variable is explicitly set, allowing for integration into various CI/CD pipelines without altering command line test invocations directly.
2. **Command Line Argument**: You can also directly control the execution of remote tests using the `--remote` flag with pytest. This method overrides the environment variable setting:

- To skip remote tests (useful for local development where remote resources are not needed or available):

```bash
pytest tests --remote false
```

- To enable remote tests (ensures that tests requiring external resources are executed):

```bash
pytest tests --remote true
```

## Code Style

Our project enforces code style using a combination of tools including [isort](https://github.com/PyCQA/isort), [pylint](https://github.com/pylint-dev/pylint), [black](https://github.com/psf/black), and [mypy](https://github.com/python/mypy). These tools are configured according to project-specific settings in `pyproject.toml`.

When coding:

- Use annotations like `pylint: disable`, `fmt: off`, `type: ignore`, or `pragma: no cover` only as a last resort.
- Ensure all functions and classes include Python type hints to support `py.typed` and improve type-checking accuracy.
- Public APIs should follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

### Type Annotations

The project targets Python 3.10+, so use modern built-in generics ([PEP 585](https://peps.python.org/pep-0585/)) and union syntax ([PEP 604](https://peps.python.org/pep-0604/)). Do **not** import basic collection or union types from `typing`.

```python
# Correct
def process(data: str | None, items: list[str], config: dict[str, Any]) -> tuple[int, bool]:
    ...

# Incorrect
from typing import Dict, List, Optional, Tuple

def process(data: Optional[str], items: List[str], config: Dict[str, Any]) -> Tuple[int, bool]:
    ...
```

- **Collections**: use `list`, `dict`, `set`, `tuple` — not `List`, `Dict`, `Set`, `Tuple`.
- **Unions**: use `X | Y` and `X | None` — not `Union[X, Y]` or `Optional[X]`.
- **Still fine to import from `typing`**: `Any`, `Callable`, `Type`, `TypeVar`, `Protocol`, `Final`, `TYPE_CHECKING`, and other constructs with no built-in equivalent. `Type` is deliberately on this list — `typing.Type` remains the convention in this codebase, so there is no need to reach for `type[...]`. The two are also not interchangeable at runtime: `typing.Type[int] != type[int]` (distinct objects with distinct hashes, `typing._GenericAlias` vs `types.GenericAlias`), the inequality propagates through composites such as `Optional[...]`, and `type[...]` resolves the name `type` at evaluation time, so a module- or class-level binding named `type` shadows the builtin and breaks the annotation. Type checkers treat the two the same; runtime introspection does not.

Both features work at runtime on every supported version, so `from __future__ import annotations` is not needed for them. Keep that import only where it is load-bearing — most commonly when annotations reference names imported under `if TYPE_CHECKING:`, which would otherwise raise `NameError` at runtime.

This applies to new code and to code you are already modifying for other reasons. Do **not** retrofit existing modules just to satisfy it: a typing-only sweep through otherwise untouched code adds review burden and churns `git blame` for no functional gain.

### Fail Loudly on Missing Data

When a field is expected to exist, access it directly. Do not paper over its absence with a default value.

```python
# Correct — a malformed payload raises immediately, at the source
def process_result(status: str, cost: float, time_stamps: dict[str, Any]) -> Result:
    """Accept explicit, typed parameters."""
    return Result(status=status, cost=cost, timeStamps=time_stamps, resultData={})

# Incorrect — unpacks a raw dict with silent fallbacks
def process_result(data: dict[str, Any]) -> Result:
    return Result(
        status=data.get("status", "UNKNOWN"),
        cost=float(data.get("cost", 0)),
        timeStamps=data.get("timeStamps"),
        resultData=data.get("resultData", {}),
    )
```

A default that stands in for missing data does not prevent the failure — it delays it, and moves
it somewhere that no longer points at the cause. A `KeyError` on the response you just received is
far cheaper to diagnose than a device that silently advertises `num_qubits=None`, or a job whose
status quietly reads `UNKNOWN` because the vendor added an enum member.

- Use `.get()` only when a key is **genuinely optional**, and handle the `None` explicitly.
- Prefer passing explicit, typed parameters over threading raw dicts through call chains.
- When a vendor SDK ships response models, validate the payload once at the boundary (e.g. in the
  session/client) and let the rest of the code read typed attributes. Validation gives you
  fail-loud behavior for every required field at no cost, and the error names the offending field.
- The same applies to lookup tables keyed on vendor data: index directly (`_STATUS_MAP[status]`)
  so an unmapped value raises, rather than `.get(status, SOME_DEFAULT)`, which hides it.

## Integration checklists

Adding a provider or a program type touches registration surfaces spread across the whole
repo, and the history of merged provider PRs shows every surface below has been forgotten
at least once — five providers in a row shipped without loader overloads (backfilled in
[#1350](https://github.com/qBraid/qBraid/pull/1350)), Open Quantum shipped without
discovery entry points ([#1347](https://github.com/qBraid/qBraid/pull/1347)), two
providers merged without remote tests, and the README provider list trails the actual
provider set. These checklists are compiled from that audit plus the current state of the
integrations. Where a guard test exists, it is named — run it before pushing.

### Adding a runtime provider

**Implementation**

- [ ] `qbraid/runtime/<name>/` — `provider.py`, `device.py`, `job.py`, and a public
  `exceptions.py` (exceptions get their own importable module, exported from the package;
  `qbraid/runtime/quantinuum/` is the reference shape). `__init__.py` carries the
  autosummary docstring and `__all__`.
- [ ] Vendor-status lookup is fail-loud: index the map directly and raise on unmapped
  values (see [Fail Loudly on Missing Data](#fail-loudly-on-missing-data)).

**Registration — the invisible surfaces**

- [ ] `pyproject.toml` entry points, **both** groups:
  `[project.entry-points."qbraid.providers"]` and `[project.entry-points."qbraid.jobs"]`.
  Discovery via `get_providers()` / `load_provider()` / `load_job()` needs both.
- [ ] `qbraid/runtime/loader.py`: the `TYPE_CHECKING` import plus a `load_provider` and a
  `load_job` `@overload`, in alphabetical position.
  `tests/runtime/test_loader.py::test_loader_overloads_match_entrypoints` fails if you
  forget.
- [ ] `qbraid/runtime/__init__.py`: `_lazy` dict entry, `TYPE_CHECKING` imports, and the
  docstring autosummary listing.

**Dependencies**

- [ ] Optional-dependency extra in `pyproject.toml`, with an upper bound — vendor SDKs
  routinely break within a minor series (qnexus 0.48.x shipped an undeclared import three
  releases running; oqc-qcaas-client 3.23.0 removed an enum member the SDK read at import).
- [ ] `requirements-dev.txt`, so CI actually installs the SDK and runs your tests. If the
  vendor SDK cannot co-resolve with the main environment (mimiqcircuits pins
  `protobuf>=6.30` against cirq-google's `<6`), do **not** leave the suite silently
  skipping: add an isolated tox env and workflow job instead — see `unit-tests-qperfect`
  in `tox.ini` and `test-qperfect` in `.github/workflows/main.yml`. Codecov merges that
  job's report with the matrix job's, so coverage still counts.

**Docs**

- [ ] `docs/api/qbraid.runtime.rst`: add the submodule to the autosummary list
  (alphabetical).
- [ ] `docs/conf.py` `autodoc_mock_imports`: add the vendor SDK if any module imports it
  at module scope — the docs build installs no extras and autosummary imports the whole
  package. Keep vendor imports lazy where you can; note that runtime-evaluated
  `X | Y` annotations over mocked names crash the build, so either add
  `from __future__ import annotations` or quote the alias.
- [ ] `README.md`: add the provider to the linked provider list in the qBraid Runtime
  install section.
- [ ] Provider guide on [docs.qbraid.com](https://docs.qbraid.com/v2/sdk/user-guide/runtime)
  (separate repo) — the README links resolve there.

**Tests**

- [ ] `tests/runtime/<name>/` unit tests with production-shaped fixtures (see
  [Testing Philosophy](#testing-philosophy)).
- [ ] `tests/runtime/<name>/test_<name>_remote.py` behind the `remote` marker, exercised
  against the live API at least once before merge (see
  [Running Tests Requiring Remote Access](#running-tests-requiring-remote-access)).
- [ ] The directory must **collect** cleanly without the extra installed:
  `pytest.importorskip` at module top, or `collect_ignore` in the directory's
  `conftest.py`. Watch module-level `parametrize` arguments — they evaluate at import
  time, so a guarded import that fails still crashes collection if the decorator names it.

**Bookkeeping**

- [ ] `CHANGELOG.md` entry under `[Unreleased]` (style notes at the top of that file).
- [ ] Keep the new package typed if possible; if it must join the `[tool.mypy]` `exclude`
  list in `pyproject.toml`, say why in the PR.

**Verify**

```bash
tox -e unit-tests -- tests/runtime/<name> tests/runtime/test_loader.py --remote false
tox -e docs
python -c "from qbraid.runtime import get_providers; print(get_providers())"
```

Then once more in a clean environment *without* the extra: the test directory must skip,
not error.

### Adding a program type

- [ ] `qbraid/programs/<family>/<name>.py` wrapper class (`gate_model/`, `ahs/`, or
  `annealing/`).
- [ ] `qbraid/programs/_import.py`: add the lazy import hook and the module list entry.
- [ ] `pyproject.toml` `[project.entry-points."qbraid.programs"]`: `alias = wrapper path`.
  Derive the alias from the package name — every entry in `NATIVE_REGISTRY` does.
- [ ] At least one transpiler edge: `qbraid/transpiler/conversions/<src>/<src>_to_<alias>.py`,
  registered in that conversions package's `__init__.py` (import, `__all__`, docstring
  autosummary). Extras-gated conversions carry `@requires_extras`.
- [ ] Regenerate the conversion-graph art: `python bin/generate_conversion_graph.py` and
  commit both SVGs — `tests/transpiler/test_conversion_graph_diagram.py` rejects stale
  art. An alias reachable only through an extras package goes in that script's
  `EXTERNAL_ALIASES`; a type with no edges goes in `ISOLATED_TYPES`.
- [ ] `docs/conf.py` mocks and dependency handling: same rules as providers.
- [ ] Tests: wrapper unit tests, and conversion tests asserting round-trip or unitary
  equivalence rather than string equality. Adding `tests/fixtures/<alias>/` circuit
  builders enrolls the type in the shared interface tests.
- [ ] `CHANGELOG.md` entry.

**Verify**

```bash
python bin/generate_conversion_graph.py   # must be a no-op after your commit
pytest tests/transpiler/test_conversion_graph_diagram.py
python -c "from qbraid.programs import QPROGRAM_REGISTRY; print(QPROGRAM_REGISTRY)"
```

## Pull Requests

Before submitting a pull request (PR), ensure your contributions comply with the [Developer's Certificate of Origin](https://developercertificate.org/), confirming your right to submit the work under this project's [LICENSE](LICENSE). Contributors are encouraged to [sign commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits), however, it is not required.

For code changes, please ensure that:

1. All new code includes corresponding unit tests and satisfies code coverage.
2. Docstrings are thorough and accurate for both new and updated features.
3. All integration tests, including remote tests (as applicable), are passing.
4. New functions and classes are annotated with Python type hints to support `py.typed`.

### Integration Tests

Run the following commands locally to confirm that your changes meet our quality standards and will pass all integration tests:

1. **Unit Tests**

   - Command: `tox -e unit-tests`
   - Ensure all unit tests pass and new or modified code meets `codecov` requirements. For remote tests that require credentials, set the `QBRAID_RUN_REMOTE_TESTS=true` environment variable.

2. **Documentation**

   - Command: `tox -e docs`
   - Check that documentation builds successfully. Include thorough and accurate docstrings for all new or updated code. Update Sphinx tree stubs as needed to reflect any changes to the structure of package modules.

3. **Code Style**
   - Command: `tox -e format-check`
   - Verify that code formatting complies with project standards. Use `pylint: disable` only when necessary, and document any exceptions or updates to the project's code style configurations. New functions and classes must be annotated with Python type hints to support `py.typed`.

### Submitting a Pull Request

When you are ready to submit a PR:

- **Title**: Choose a title that is short, detailed, and easily understandable.
- **Description**: Provide a brief description of the changes. Include the context and motivation behind the PR, if relevant.
- **Link Issues**: If your PR resolves an open issue, link it using the keyword "Closes" followed by the issue number (e.g., `Closes #123`).
- **Changelog**: Add an entry under the relevant heading in the `[Unreleased]` section of [CHANGELOG.md](CHANGELOG.md), following the style notes at the top of that file. Keep it to one or two sentences describing the user-visible change, and link your PR. Detail about root cause, diagnosis, and implementation belongs in the PR description, not the changelog.

Writing the changelog entry by hand, either in the original commit or as a follow-up, is the normal path. If you are a maintainer and forgot one, commenting `/update-changelog` on the PR will draft the entries from the diff and push them to your branch. It is a convenience, not a required step, and the result is worth a read before merging.

Remember, it's perfectly fine to submit a draft pull request if your code is still a work-in-progress. We're here to help!

### Updating Examples Submodule

```bash
git submodule sync
git submodule init
git submodule update --remote --recursive
git submodule update --remote --merge
git add examples
git commit -m "update examples submodule"
```
