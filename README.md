<img width=full alt="qbraid-sdk-header" src="https://user-images.githubusercontent.com/46977852/224456452-605e51f2-193d-4789-863e-e51cdd4b0a54.png">

[![CI](https://github.com/qBraid/qBraid/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/qBraid/qBraid/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/qBraid/qBraid/branch/main/graph/badge.svg?token=1UTM0XZB7A)](https://codecov.io/gh/qBraid/qBraid)
[![Documentation Status](https://readthedocs.com/projects/qbraid-qbraid/badge/?version=latest)](https://docs.qbraid.com/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The qBraid-SDK is a Python toolkit for cross-framework abstraction, transpilation, and execution of quantum programs.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)

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
To run all unit tests:
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

### API Authentication

Update `qbraid/api/config_data.py` to the desired API url, e.g.

```
qbraid_api_url = "https://api-staging-1.qbraid.com/api"
```

and make sure your IP Address is white-listed on MongoDB.

To allow authenticated requests you must populate your `~/.qbraidrc` file with your qBraid account email and refresh token. Tox does this programmatically via the `set_config()` function in `qbraid/api/tests/test_api_config.py` using inhereted environments variables `JUPYTERHUB_USER` and `REFRESH`. To get your refresh token:

- Login to account.qbraid.com and open DevTools
- Go to Application -> Storage -> Cookies -> https://account.qbraid.com
- The value corresponding to REFRESH is your refresh token.
  Note, your refresh token is updated monthly.
