<img width=full alt="qbraid-sdk-header" src="https://user-images.githubusercontent.com/46977852/224456452-605e51f2-193d-4789-863e-e51cdd4b0a54.png">

<p align="center">
  <a href="https://github.com/qBraid/qBraid/actions/workflows/main.yml">
    <img src="https://github.com/qBraid/qBraid/actions/workflows/main.yml/badge.svg?branch=main" alt="CI"/>
  </a>
  <a href="https://codecov.io/gh/qBraid/qBraid">
    <img src="https://codecov.io/gh/qBraid/qBraid/branch/main/graph/badge.svg?token=1UTM0XZB7A" alt="codecov"/>
  </a>
  <a href="https://docs.qbraid.com/en/latest/?badge=latest">
    <img src="https://readthedocs.com/projects/qbraid-qbraid/badge/?version=latest" alt="Documentation Status"/>
  </a>
  <a href="https://pypi.org/project/qbraid/">
    <img src="https://img.shields.io/pypi/v/qbraid.svg?color=blue" alt="PyPI version"/>
  </a>
  <a href="https://pepy.tech/project/qbraid">
    <img src="https://static.pepy.tech/badge/qbraid" alt="Downloads"/>
  </a>
  <a href="https://www.gnu.org/licenses/gpl-3.0.html">
    <img src="https://img.shields.io/github/license/qBraid/qbraid.svg" alt="License"/>
  </a>
  <a href="https://discord.gg/TPBU2sa8Et">
    <img src="https://img.shields.io/discord/771898982564626445.svg?color=pink" alt="Discord"/>
  </a>
</p>

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

Using the SDK on [qBraid Lab](https://docs.qbraid.com/projects/lab/en/latest/lab/overview.html) means direct, pre-configured access to QPUs from IonQ, Oxford Quantum Circuits, QuEra, and Rigetti, as well as on-demand simulators from AWS, all with no additional access keys or API tokens required. See [qBraid Quantum Jobs](https://docs.qbraid.com/projects/lab/en/latest/lab/quantum_jobs.html) for more.

### Local install

The qBraid-SDK, and all of its dependencies, can also be installed using pip:

```bash
pip install qbraid
```

You can also [install from source](CONTRIBUTING.md#installing-from-source) by cloning this repository and running a pip install command in the root directory of the repository:

```bash
git clone https://github.com/qBraid/qBraid.git
cd qBraid
pip install .
```

*Note*: The qBraid-SDK requires Python 3.9 or greater.

If using locally, follow linked instructions to configure your
[qBraid](#local-account-setup),
[AWS](https://github.com/aws/amazon-braket-sdk-python#boto3-and-setting-up-aws-credentials),
and [IBMQ](https://github.com/Qiskit/qiskit-ibm-provider#provider-setup)
credentials.

### Check version

You can view the version of the qBraid-SDK you have installed within Python using the following:

```python
In [1]: import qbraid

In [2]: qbraid.__version__
```

## Documentation & Tutorials

qBraid documentation is available at
[docs.qbraid.com](https://docs.qbraid.com/en/stable/).

See also:

- [API Reference](https://docs.qbraid.com/en/stable/api/qbraid.html)
- [User Guide](https://docs.qbraid.com/en/stable/sdk/overview.html)
- [Example Notebooks](https://github.com/qBraid/qbraid-lab-demo)

## Quickstart

### Transpiler

Construct a quantum program of any supported program type.

Below, `SUPPORTED_QPROGRAMS` maps shorthand identifiers for supported quantum programs, each corresponding to a type in the typed `QPROGRAM` Union.
For example, 'qiskit' maps to `qiskit.QuantumCircuit` in `QPROGRAM`. Notably, 'qasm2' and 'qasm3' both represent raw OpenQASM strings.
This arrangement simplifies targeting and transpiling between different quantum programming frameworks.

```python
>>> from qbraid.programs import SUPPORTED_QPROGRAMS
>>> SUPPORTED_QPROGRAMS
{'cirq': 'cirq.circuits.circuit.Circuit',
 'qiskit': 'qiskit.circuit.quantumcircuit.QuantumCircuit',
 'pyquil': 'pyquil.quil.Program',
 'pytket': 'pytket._tket.circuit.Circuit',
 'braket': 'braket.circuits.circuit.Circuit',
 'openqasm3': 'openqasm3.ast.Program',
 'qasm2': 'str',
 'qasm3': 'str'}
```

Pass any quantum program of type `qbraid.programs.QPROGRAM` to the `load_program()` and specify a target package
from `SUPPORTED_QPROGRAMS` to "transpile" your circuit to a new program type:

```python
>>> from qbraid.interface import random_circuit
>>> from qbraid.transpiler import transpile
>>> qiskit_circuit = random_circuit("qiskit")
>>> cirq_circuit = transpile(qiskit_circuit, "cirq")
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

The same functionality can be achieved using the underlying `transpile()` function directly:

```python
>>> from qbraid.transpiler import transpile
>>> cirq_circuit = transpile(qiskit_circuit, "cirq")
```

Behind the scenes, the qBraid-SDK uses ``networkx`` to create a directional graph that maps all possible conversions between supported program types:

```python
from qbraid.transpiler import ConversionGraph
from qbraid.visualization import plot_conversion_graph

graph = ConversionGraph()

graph.plot()
```

<img align="middle" width="full" alt="conversion_graph" src="https://qbraid-static.s3.amazonaws.com/conversion_graph.png">

You can use the native conversions supported by qBraid, or define your own custom nodes and/or edges. For [example](https://github.com/qBraid/qbraid-qir?tab=readme-ov-file#add-qir-node-to-qbraid-conversion-graph):

```python
from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid.transpiler import Conversion

conversion = Conversion("qasm3", "qir", qasm3_to_qir)

graph.add_conversion(conversion)

graph.plot()
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
aws_ionq_aria2                      OFFLINE
aws_rigetti_aspen_m3                ONLINE
ibm_q_brisbane                      ONLINE
...

```

You can get a Python list of device objects using:

```python
from qbraid.providers import QbraidProvider

provider = QbraidProvider()
qdevices = provider.get_devices()
```

Or, instantiate a known device by ID via the `QbraidProvider.get_device()` method,
and submit quantum jobs from any supported program type:

```python
>>> from qbraid import get_jobs
>>> from qbraid.providers import QbraidProvider
>>> provider = QbraidProvider()
>>> aws_device = provider.get_device("aws_oqc_lucy")
>>> ibm_device = provider.get_device("ibm_q_brisbane")
>>> aws_job = aws_device.run(qiskit_circuit, shots=1000)
>>> ibm_job = ibm_device.run(cirq_circuit, shots=1000)
>>> get_jobs()
Displaying 2 most recent jobs:

Job ID                                              Submitted                  Status
------                                              ---------                  ------
aws_oqc_lucy-exampleuser-qjob-zzzzzzz...            2023-05-21T21:13:47.220Z   QUEUED
ibm_q_brisbane-exampleuser-qjob-xxxxxxx...          2023-05-21T21:13:48.220Z   RUNNING
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
<img align="right" width="300" alt="api_key" src="https://qbraid-static.s3.amazonaws.com/manage-account.png">

To use the qBraid-SDK locally (outside of qBraid Lab), you must add your account
credentials:

1. Create a qBraid account or log in to your existing account by visiting
   [account.qbraid.com](https://account.qbraid.com/)
2. Copy your API Key token from the left side of
    your [account page](https://account.qbraid.com/):

3. Save your API key from step 2 by calling
   `QbraidSession.save_config()`:

```python
from qbraid_core import QbraidSession

session = QbraidSession(api_key='API_KEY')
session.save_config()
```

The command above stores your credentials locally in a configuration file `~/.qbraid/qbraidrc`,
where `~` corresponds to your home (`$HOME`) directory. Once saved, you can then connect to the
qBraid API and leverage functions such as `get_devices()` and `get_jobs()`.

### Load Account from Environment Variables

Alternatively, the qBraid-SDK can discover credentials from environment
variables:

```shell
export QBRAID_API_KEY='QBRAID_API_KEY'
```

Then instantiate the session without any arguments

```python
from qbraid_core import QbraidSession

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

```markdown
[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git)
```

Use the badge in your project's `README.rst`:

```rst
.. image:: https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png
    :target: https://account.qbraid.com?gitHubUrl=https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
    :width: 150px
```

## Contributing

- Interested in contributing code, or making a PR? See
  [CONTRIBUTING.md](CONTRIBUTING.md)
- For feature requests and bug reports:
  [Submit an issue](https://github.com/qBraid/qBraid/issues)
- For discussions, and specific questions about the qBraid-SDK [join our discord community](https://discord.gg/TPBU2sa8Et)
- For questions that are more suited for a forum, post to
  [Quantum Computing Stack Exchange](https://quantumcomputing.stackexchange.com/)
  with the [`qbraid`](https://quantumcomputing.stackexchange.com/questions/tagged/qbraid) tag.

## License

[GNU General Public License v3.0](LICENSE)
