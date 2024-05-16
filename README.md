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

The qBraid-SDK is a platform-agnostic quantum runtime framework designed for both quantum software and hardware providers.

This Python-based tool streamlines the full lifecycle management of quantum jobs&mdash;from defining program specifications to job submission, and through to the post-processing and visualization of results. Distinguishing itself through a streamlined and highly-configurable approach to cross-platform integration, the qBraid-SDK *does not assume a fixed target software framework*. Instead, it allows providers to dynamically register any desired run input program type as the target, depending on their specific needs. These program types are interconnected via a graph-based transpiler, where each program type is represented as a node and supported conversions as edges. The breadth, depth, and connectivity of this `ConversionGraph` can be customized by the provider.

The framework also facilitates the insertion of additional program validations, circuit transformations, and transpiler/compiler steps into its modular pipeline through a comprehensive `TargetProfile`. This profile encapsulates both device properties (such as number of qubits, maximum shots, native gate set) and the software requirements (`ProgramSpec`) needed to submit a job, vastly reducing the overhead and redundancy typically associated with cross-platform integrations in quantum computing.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)

## Key Features

### 1. Quantum Program Integration

Offers native support for 10 major quantum programming libraries including 20+ inter-library conversions with the ability to
dynamically register new program types and conversions on the fly. This enables flexible program submissions to cater to the unique capabilities and constraints of your preferred framework, facilitated by a unique conversion map that automatically adapts quantum programs during runtime according to the given specifications.

### 2. Modular Design

- `qbraid.programs`: Extracts and manages metadata from supported quantum program types, with the flexibility to introduce new types.
- `qbraid.transpiler`: Bridges different quantum programming IRs through native and customizable circuit conversions.
- `qbraid.transforms`: Ensures quantum programs conform to hardware specifications through essential runtime transformations.
- `qbraid.runtime`: Defines essential abstractions for providers, devices, jobs, and results, integrated through a coherent runtime profile.
- `qbraid.visualization`: Provides tools for visualizing quantum circuits and experimental data, enhancing data interpretation.

### 3. Extensibility and Customization

The framework encourages community contributions and extensions, supporting an evolving ecosystem of program types and conversions, adaptable to specific provider needs. By providing a comprehensive runtime solution, the qBraid-SDK offers significant advantages to *both hardware and software providers*:

- **Reduces Overhead**: Minimizes the effort required to develop client-side applications for securely submitting and managing quantum experiments remotely.
- **Enhances Integration**: Facilitates seamless integration and interoperability of quantum software tools across all layers of the stack.
- **Broad Compatibility**: Supports a diverse range of API complexities, catering to both established players like IBM and AWS as well as emerging providers.

## Installation & Setup

<img align="right" width="300" alt="qbraid-sdk-env" src="https://github.com/qBraid/qBraid/assets/46977852/c82d61b4-2518-4c7e-8f48-05106afa708e">

For the best experience, install the qBraid-SDK environment on
[lab.qbraid.com](https://lab.qbraid.com). Login (or
[create an account](https://account.qbraid.com)) and follow the steps to
[install an environment](https://docs.qbraid.com/projects/lab/en/latest/lab/environments.html#install-environment).

Using the SDK on [qBraid Lab](https://docs.qbraid.com/projects/lab/en/latest/lab/overview.html) means direct, pre-configured access to QPUs from IonQ, Oxford Quantum Circuits, QuEra, and Rigetti, as well as on-demand simulators from AWS, all with no additional access keys or API tokens required. See [qBraid Quantum Jobs](https://docs.qbraid.com/projects/lab/en/latest/lab/quantum_jobs.html) for more.

### Local install

The qBraid-SDK, and all of its dependencies, can also be installed using pip:

```shell
pip install qbraid
```

You can also [install from source](CONTRIBUTING.md#installing-from-source) by cloning this repository and running a pip install command in the root directory of the repository:

```shell
git clone https://github.com/qBraid/qBraid.git
cd qBraid
pip install .
```

> *Note:* The qBraid-SDK requires Python 3.9 or greater.

If using locally, follow linked instructions to configure your
[qBraid](#local-account-setup),
[AWS](https://github.com/aws/amazon-braket-sdk-python#boto3-and-setting-up-aws-credentials), [IBM](https://github.com/Qiskit/qiskit-ibm-runtime?tab=readme-ov-file#account-setup), and/or [IonQ](https://cloud.ionq.com/settings/keys) credentials.

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

Below, `QPROGRAM_REGISTRY` maps shorthand identifiers for supported quantum programs, each corresponding to a type in the typed `QPROGRAM` Union.
For example, 'qiskit' maps to `qiskit.QuantumCircuit` in `QPROGRAM`. Notably, 'qasm2' and 'qasm3' both represent raw OpenQASM strings.
This arrangement simplifies targeting and transpiling between different quantum programming frameworks.

```python
>>> from qbraid.programs import QPROGRAM_REGISTRY
>>> QPROGRAM_REGISTRY
{'cirq': 'cirq.circuits.circuit.Circuit',
 'qiskit': 'qiskit.circuit.quantumcircuit.QuantumCircuit',
 'pyquil': 'pyquil.quil.Program',
 'pytket': 'pytket._tket.circuit.Circuit',
 'braket': 'braket.circuits.circuit.Circuit',
 'openqasm3': 'openqasm3.ast.Program',
 'qasm2': 'str',
 'qasm3': 'str'}
```

Pass any registered quantum program along with a target package from
`QPROGRAM_REGISTRY` to "transpile" your circuit to a new program type:

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

Behind the scenes, the qBraid-SDK uses ``networkx`` to create a directional graph that maps all possible conversions between supported program types:

```python
from qbraid.transpiler import ConversionGraph
from qbraid.visualization import plot_conversion_graph

graph = ConversionGraph()

graph.plot()
```

<img align="middle" width="full" alt="conversion_graph" src="https://qbraid-static.s3.amazonaws.com/conversion_graph_extras.png">

You can use the native conversions supported by qBraid, or define your own custom nodes and/or edges. For [example](https://github.com/qBraid/qbraid-qir?tab=readme-ov-file#add-qir-node-to-qbraid-conversion-graph):

```python
from qbraid_qir.qasm3 import qasm3_to_qir
from qbraid.transpiler import Conversion

conversion = Conversion("qasm3", "pyqir", qasm3_to_qir)

graph.add_conversion(conversion)

graph.plot()
```

### QbraidProvider

Run experiements using on-demand simulators provided by qBraid using the `qbraid.runtime.native.QbraidProvider`. You can get a Python list of device objects using:

```python
from qbraid.runtime.native import QbraidProvider

provider = QbraidProvider()
qdevices = provider.get_devices()
```

Or, instantiate a known device by ID via the `QbraidProvider.get_device()` method,
and submit quantum jobs from any supported program type:

```python
device = provider.get_device("qbraid_qir_simulator")
jobs = device.run([qiskit_circuit, braket_circuit, cirq_circuit, qasm3_str], shots=1000)
results = [job.result() for job in jobs]

print(results[0].measurement_counts())
# {'00': 483, '01': 14, '10': 486, '11': 17}
```

## Local account setup

<img align="right" width="300" alt="api_key" src="https://qbraid-static.s3.amazonaws.com/manage-account.png">

To use the qBraid-SDK locally (outside of qBraid Lab), you must add your account
credentials:

1. Create a qBraid account or log in to your existing account by visiting
   [account.qbraid.com](https://account.qbraid.com/)
2. Copy your API Key token from the left side of
    your [account page](https://account.qbraid.com/):

### Save account to disk

Once you have your API key from step 2 by, you can save it locally in a configuration file `~/.qbraid/qbraidrc`,
where `~` corresponds to your home (`$HOME`) directory:

| :warning: Account credentials are saved in plain text, so only do so if you are using a trusted device. |
|:---------------------------|

```python
from qbraid.runtime.native import QbraidProvider

provider = QbraidProvider(api_key='API_KEY')
provider.save_config()
```

Once the account is saved on disk, you can instantiate the provider without any arguments:

```python
from qbraid.runtime.native import QbraidProvider

provider = QbraidProvider()
```

### Load account from environment variables

Alternatively, the qBraid-SDK can discover credentials from environment variables:

```shell
export QBRAID_API_KEY='QBRAID_API_KEY'
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
