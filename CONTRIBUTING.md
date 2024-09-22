# Contributing

Welcome! Happy to see you want to help us make the project better.

The following is a summary of relevant commands, procedures, and best practices for developers contributing to qBraid. *Note:* Some commands are specific to a Debian environment, and unless stated otherwise, all commands are assumed to be executed from the qBraid repository root.

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
pip install -e '.[docs]'
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

## Pull Requests

Before submitting a pull request (PR), ensure your contributions comply with the [Developer's Certificate of Origin](https://developercertificate.org/), confirming your right to submit the work under this project's [LICENSE](LICENSE). Contributors are encouraged to [sign commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits), however, it is not required.

For code changes, please ensure that:
1. All new code includes corresponding unit tests and satisfies code coverage.
2. Docstrings are thorough and accurate for both new and updated features.
3. All integration tests, including remote tests (as applicable), are passing.
4. New functions and classes are annotated with Python type hints to support `py.typed`.
5. (Optional) Yor name and affiliation are added to [CITATION.cff](CITATION.cff).

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
   - Verify that code formatting complies with project standards. Use `pylint: disable` only when neccessary, and document any exceptions or updates to the project's code style configurations. New functions and classes must be annotated with Python type hints to support `py.typed`.

### Submitting a Pull Request
When you are ready to submit a PR:

- **Title**: Choose a title that is short, detailed, and easily understandable.
- **Description**: Provide a brief description of the changes. Include the context and motivation behind the PR, if relevant.
- **Link Issues**: If your PR resolves an open issue, link it using the keyword "Closes" followed by the issue number (e.g., `Closes #123`).

Remember, it's perfectly fine to submit a draft pull request if your code is still a work-in-progress. We're here to help!