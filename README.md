<img width=full alt="qbraid-sdk-header" src="https://user-images.githubusercontent.com/46977852/224456452-605e51f2-193d-4789-863e-e51cdd4b0a54.png">

[![CI](https://github.com/qBraid/qBraid/actions/workflows/main.yml/badge.svg)](https://github.com/qBraid/qBraid/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/qBraid/qBraid/branch/main/graph/badge.svg?token=1UTM0XZB7A)](https://codecov.io/gh/qBraid/qBraid)
[![Documentation Status](https://readthedocs.com/projects/qbraid-qbraid/badge/?version=latest)](https://docs.qbraid.com/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

The qBraid-SDK is a Python toolkit for cross-framework abstraction, transpilation, and execution of quantum programs.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)


## Features

- Unified quantum frontend interface. **Transpile** quantum circuits between supported packages. Leverage the capabilities of multiple frontends through **simple, consistent protocols**.
- Build once, target many. **Create** quantum programs using your preferred circuit-building package, and **execute** on any backend that interfaces with a supported frontend.
- Benchmark, compare, interpret results. Built-in **compatible** post-processing enables comparing results between runs and **across backends**.


## Installation

For the best experience, install the qBraid-SDK environment on [qBraid Lab](https://lab.qbraid.com). Login (or create an account) and then follow the steps to [install an environment](https://docs.qbraid.com/en/latest/lab/environments.html#install-environment).

The qBraid-SDK, and all of its dependencies, can also be installed using pip:

```bash
pip install qbraid
```

## Quickstart

For more in-depth examples, see [user guide](https://docs.qbraid.com/en/latest/sdk/overview.html) and [demo notebooks](https://github.com/qBraid/qbraid-lab-demo).

### Transpiler

Construct a quantum program of any supported program type, 

```python
>>> from qbraid import QPROGRAM_LIBS
>>> QPROGRAM_LIBS
['braket', 'cirq', 'qiskit', 'pyquil', 'pytket']
```

and use the `circuit_wrapper()` to convert to any other supported program type:

```python
>>> from qbraid import circuit_wrapper
>>> from qbraid.interface import random_circuit
>>> qiskit_circuit = random_circuit("qiskit")
>>> cirq_circuit = circuit_wrapper(qiskit_circuit).transpile("cirq")
>>> print(qiskit_circuit)
          ┌────────────┐
q_0: ──■──┤ Rx(3.0353) ├
     ┌─┴─┐└───┬────┬───┘
q_1: ┤ H ├────┤ √X ├────
     └───┘    └────┘    
>>> print(cirq_circuit)
0: ───H───X^0.5────────
      │
1: ───@───Rx(0.966π)───
```

### Devices & Jobs

Search for quantum backend(s) on which to execute your program.

```python
>>> from qbraid import get_devices
>>> get_devices()
Device status updated 0 minutes ago

Device ID                           Status
---------                           ------
aws_oqc_lucy                        ONLINE
aws_rigetti_aspen_m2                OFFLINE
aws_rigetti_aspen_m3                ONLINE
ibm_q_perth                         ONLINE
...

```

Apply the `device_wrapper()`, and send quantum jobs to any supported backend, from any supported program type:

```python
>>> from qbraid import device_wrapper, get_jobs
>>> aws_device = device_wrapper("aws_oqc_lucy")
>>> ibm_device = device_wrapper("ibm_q_perth")
>>> aws_job = aws_device.run(qiskit_circuit, shots=1000)
>>> ibm_job = ibm_device.run(cirq_circuit, shots=1000)
>>> get_jobs()
Displaying 2 most recent jobs:

Job ID                                              Submitted                  Status
------                                              ---------                  ------
aws_oqc_lucy-exampleuser-qjob-zzzzzzz...            2023-05-21T21:13:47.220Z   QUEUED
ibm_q_perth-exampleuser-qjob-xxxxxxx...             2023-05-21T21:13:48.220Z   RUNNING
...
```

Compare results in a consistent, unified format:

```python
>>> aws_result = aws_job.result()
>>> ibm_result = ibm_job.result()
>>> aws_result.measurement_counts()
{'00': 483, '01': 14, '10': 486, '11': 17}
>>> ibm_result.measurement_counts()
{'00': 496, '01': 12, '10': 479, '11': 13}
```

## Local Setup

To use the qBraid-SDK locally (outside of qBraid Lab), you must add your account credentials:

1. Create a qBraid account or log in to your existing account by visiting https://account.qbraid.com
2. Copy your API (refresh) token from your qBraid account page:
- Login to your account and open DevTools / inspector window (MacOS: Option-Command-I)
- Go to Application -> Storage -> Cookies -> https://account.qbraid.com
- The value corresponding to `REFRESH` is your API refresh token.
  Note, this token is updated monthly.
3. Take your account email and refresh token from step 2, and save it by calling `QbraidSession.save_config()`:

```python
from qbraid.api import QbraidSession

session = QbraidSession(user_email='USER_EMAIL', refresh_token='REFRESH_TOKEN')
session.save_config()
```

The command above stores your credentials locally in a configuration file called `qbraidrc` in `$HOME/.qbraid`, where `$HOME` is your home directory. Once saved you can then connect to the qBraid API and leverage functions such as `get_devices()` and `get_jobs()`.

### Load Account from Environment Variables

Alternatively, the qBraid-SDK can discover credentials from environment variables:

```bash
export JUPYTERHUB_USER='USER_EMAIL'
export REFRESH='REFRESH_TOKEN'
```

Then instantiate the session without any arguments

```python
from qbraid.api import QbraidSession

session = QbraidSession()
```

## Documentation

The API reference can be found on [Read the Docs](https://docs.qbraid.com/en/latest/api/qbraid.html).

To generate the API reference documentation locally:

```bash
pip install tox<4
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

## Testing

To run all unit tests:

```bash
pip install tox<4
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

## License

[GNU General Public License v3.0](LICENSE)