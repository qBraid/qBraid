<img width=full alt="qbraid-sdk-header" src="https://user-images.githubusercontent.com/46977852/224456452-605e51f2-193d-4789-863e-e51cdd4b0a54.png">

[![CI](https://github.com/qBraid/qBraid/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/qBraid/qBraid/actions/workflows/main.yml)
[![codecov](https://codecov.io/gh/qBraid/qBraid/branch/main/graph/badge.svg?token=1UTM0XZB7A)](https://codecov.io/gh/qBraid/qBraid)
[![Documentation Status](https://readthedocs.com/projects/qbraid-qbraid/badge/?version=latest)](https://docs.qbraid.com/en/latest/?badge=latest)
[![PyPI version](https://img.shields.io/pypi/v/qbraid.svg?color=blue)](https://pypi.org/project/qbraid/)
[![Downloads](https://img.shields.io/pypi/dm/qbraid.svg?color=blue)](https://pypi.org/project/qbraid/)
[![License](https://img.shields.io/github/license/qBraid/qbraid.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Discord](https://img.shields.io/discord/771898982564626445.svg?color=pink)](https://discord.gg/TPBU2sa8Et)

The qBraid-SDK is a Python toolkit for cross-framework abstraction,
transpilation, and execution of quantum programs.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)

## Features

- Unified quantum frontend interface. **Transpile** quantum circuits between
  supported packages. Leverage the capabilities of multiple frontends through
  **simple, consistent protocols**.
- Build once, target many. **Create** quantum programs using your preferred
  circuit-building package, and **execute** on any backend that interfaces with
  a supported frontend.
- Benchmark, compare, interpret results. Built-in **compatible** post-processing
  enables comparing results between runs and **across backends**.

## Installation & Setup

<img align="right" width="300" alt="qbraid-sdk-env" src="https://github.com/qBraid/qBraid/assets/46977852/c82d61b4-2518-4c7e-8f48-05106afa708e">

For the best experience, install the qBraid-SDK environment on
[lab.qbraid.com](https://lab.qbraid.com). Login (or
[create an account](https://account.qbraid.com)) and follow the steps to
[install an environment](https://docs.qbraid.com/projects/lab/en/latest/lab/environments.html#install-environment).

Using the SDK on qBraid Lab means direct, pre-configured access to all
[Amazon Braket supported devices](https://docs.aws.amazon.com/braket/latest/developerguide/braket-devices.html)
with no additional access keys or API tokens required. See
[qBraid Quantum Jobs](https://docs.qbraid.com/projects/lab/en/latest/lab/quantum_jobs.html)
for more.

### Local install

The qBraid-SDK, and all of its dependencies, can also be installed using pip:

```bash
pip install qbraid
```

If using locally, follow linked instructions to configure your
[qBraid](#local-account-setup),
[AWS](https://github.com/aws/amazon-braket-sdk-python#boto3-and-setting-up-aws-credentials),
and [IBMQ](https://github.com/Qiskit/qiskit-ibm-provider#provider-setup)
credentials.

## Documentation & Tutorials

qBraid documentation is available at
[docs.qbraid.com](https://docs.qbraid.com/en/stable/).

See also:

- [API Reference](https://docs.qbraid.com/en/stable/api/qbraid.html)
- [User Guide](https://docs.qbraid.com/en/stable/sdk/overview.html)
- [Example Notebooks](https://github.com/qBraid/qbraid-lab-demo)

## Quickstart

### Transpiler

Construct a quantum program of any supported program type,

```python
>>> from qbraid import QPROGRAM_LIBS
>>> QPROGRAM_LIBS
['braket', 'cirq', 'qiskit', 'pyquil', 'pytket', 'qasm2', 'qasm3']
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
0: ───@───Rx(0.966π)───
      │
1: ───H───X^0.5────────
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

Apply the `device_wrapper()`, and send quantum jobs to any supported backend,
from any supported program type:

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

## Local account setup
<img align="right" width="300" alt="api_key" src="https://github.com/qBraid/qBraid/assets/46977852/c13d6035-194b-4520-84c1-e57e7f9f4340">

To use the qBraid-SDK locally (outside of qBraid Lab), you must add your account
credentials:

1. Create a qBraid account or log in to your existing account by visiting
   [account.qbraid.com](https://account.qbraid.com/)
2. Copy your API Key token from the left side of
    your [account page](https://account.qbraid.com/):

3. Save your API key from step 2 by calling
   `QbraidSession.save_config()`:

```python
from qbraid.api import QbraidSession

session = QbraidSession(api_key='API_KEY')
session.save_config()
```

The command above stores your credentials locally in a configuration file `~/.qbraid/qbraidrc`,
where `~` corresponds to your home (`$HOME`) directory. Once saved, you can then connect to the
qBraid API and leverage functions such as `get_devices()` and `get_jobs()`.

### Load Account from Environment Variables

Alternatively, the qBraid-SDK can discover credentials from environment
variables:

```bash
export JUPYTERHUB_USER='USER_EMAIL'
export QBRAID_API_KEY='QBRAID_API_KEY'
```

Then instantiate the session without any arguments

```python
from qbraid.api import QbraidSession

session = QbraidSession()
```

## Launch on qBraid

The "Launch on qBraid" button (below) can be added to any public GitHub
repository. Clicking on it automaically opens qBraid Lab, and performs a
`git clone` of the project repo into your account's home directory. Copy the
code below, and replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub
info.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)

Use the badge in your project's `README.md`:

```
[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git)
```

Use the badge in your project's `README.rst`:

```
.. image:: https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png
    :target: https://account.qbraid.com?gitHubUrl=https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
    :width: 150px
```

## Contributing

- Interested in contributing code, or making a PR? See
  [CONTRIBUTING.md](CONTRIBUTING.md)
- For feature requests and bug reports:
  [Submit an issue](https://github.com/qBraid/qBraid/issues)
- For discussions, and specific questions about the qBraid SDK, qBraid Lab, or
  other topics, [join our discord community](https://discord.gg/TPBU2sa8Et)
- For questions that are more suited for a forum, post to
  [Quantum Computing Stack Exchange](https://quantumcomputing.stackexchange.com/)
  with the [`qbraid`](https://quantumcomputing.stackexchange.com/questions/tagged/qbraid) tag.
  
- Want your open-source project featured as its own runtime environment on
  qBraid Lab? Fill out our
  [New Environment Request Form](https://forms.gle/a4v7Kdn7G7bs9jYD8)

## License

[GNU General Public License v3.0](LICENSE)
