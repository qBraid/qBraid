# qBraid-SDK
[![Unit tests](https://github.com/qBraid/qBraid/actions/workflows/tests.yml/badge.svg)](https://github.com/qBraid/qBraid/actions/workflows/tests.yml)
[![Docs](https://github.com/qBraid/qBraid/actions/workflows/docs.yml/badge.svg)](https://github.com/qBraid/qBraid/actions/workflows/docs.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The qBraid-SDK is a highly-extensible, hardware-agnostic sdk/toolkit for running quantum programs.

<a href="https://qbraid.com/">
    <img src="/docs/_static/logo.png"
         alt="qbraid logo"
         width="250px"
         align="right">
</a>

## Installation
You can install from source by cloning this repository and running a pip install command in the
root directory:

```
git clone https://github.com/qbraid/qBraid.git
cd qBraid
python3 -m pip install -e .
```

## Documentation
To generate the API reference documentation locally:
```
pip install tox
tox -e docs
``` 
Alternatively:
```
pip install -e ".[docs]"
cd docs
make html
```
Both methods will run Sphinx in your shell. If the build results in an `InvocationError` due to a 
duplicate object description, try `rm docs/stubs/*` to empty the old stubs directory, and then 
re-start the build. If the build succeeds, it will say `The HTML pages are in build/html`. You can 
view the generated documentation in your browser (on OS X) using:
```
open build/html/index.html
```
You can also view it by running a web server in that directory:
```
cd build/html
python3 -m http.server
```
Then open your browser to http://localhost:8000. If you make changes to the docs that aren't
reflected in subsequent builds, run `make clean html`, which will force a full rebuild.

## Testing
Update line 14 of `./tox.ini` to the desired API url and make sure your IP Address is white-listed on MongoDB. Then, to run all unit tests:
```
tox -e unit-tests
```
You can also pass in various pytest arguments to run selected tests:
```
tox -e unit-tests -- {your-arguments}
```
Alternatively:
```
pip install -e ".[test]"
pytest {path-to-test}
```
Running unit tests with tox will automatically generate a coverage report, which can be viewed by
opening `tests/_coverage/index.html` in your browser.

To run linters and doc generators and unit tests:
```
tox
```

