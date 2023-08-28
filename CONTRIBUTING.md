# Contributing

Welcome! Happy to see you want to help us make the project better.

The following is a summary of important commands and protocols for developers contributing to qBraid. Note that all
commands assume a Debian environment, and that all commands (except the initial repository cloning command) assume
your current working directory is the qBraid repo root.

## Pull request checklist

1. `tox -e unit-tests`: All unit tests are passing. New + modified code has corresponding unit tests and satisfy `codecov` checks. To run remote tests (i.e. those requiring qBraid/AWS/IBM credentials), set environment variable `QBRAID_RUN_REMOTE_TESTS=True`.
2. `tox -e docs`: Doc builds are passing. New + modified code has appropriate docstrings and tree stubs are updated, if applicable.
3. `tox -e linters`: Code passes linters and formatters checks. Any exceptions or updates to code style configs are documented.
4. `python tools/verify_headers.py`: New files have appropriate licensing headers. Running headers script passes checks.

## Installing from source

You can install the qBraid-SDK from source by cloning this repository and running a pip install command in the root directory:

```bash
git clone https://github.com/qbraid/qBraid.git
cd qBraid
python3 -m pip install -e .
```

## Documentation

To generate the API reference documentation locally:

```bash
pip install 'tox'
tox -e docs
```

Alternatively:
```bash
pip install -e ".[docs]"
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
Then open your browser to http://localhost:8000. If you make changes to the docs that aren't
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
pip install 'tox'
tox -e unit-tests
```

You can also pass in various pytest arguments to run selected tests:

```bash
tox -e unit-tests -- {your-arguments}
```

Alternatively:

```bash
pip install -e ".[test]"
pytest {path-to-test}
```

Running unit tests with tox will automatically generate a coverage report, which can be viewed by
opening `tests/_coverage/index.html` in your browser.

To run linters and doc generators and unit tests:
```bash
tox
```

## Code Style

For code style, our project uses a combination of [isort](https://github.com/PyCQA/isort), [pylint](https://github.com/pylint-dev/pylint),
and [black](https://github.com/psf/black). Each of these tools is setup with its own default configuration specific to this project in `pyproject.toml`.


