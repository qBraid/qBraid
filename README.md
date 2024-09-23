<img width=full alt="qbraid-sdk-header" src="https://user-images.githubusercontent.com/46977852/224456452-605e51f2-193d-4789-863e-e51cdd4b0a54.png">

<p align="center">
  <a href="https://github.com/qBraid/qBraid/actions/workflows/main.yml">
    <img src="https://github.com/qBraid/qBraid/actions/workflows/main.yml/badge.svg?branch=main" alt="CI"/>
  </a>
  <a href="https://codecov.io/gh/qBraid/qBraid">
    <img src="https://codecov.io/gh/qBraid/qBraid/branch/main/graph/badge.svg?token=1UTM0XZB7A" alt="codecov"/>
  </a>
  <a href="https://sdk.qbraid.com/en/latest/">
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
  <a href="https://doi.org/10.5281/zenodo.12627597">
    <img src="https://zenodo.org/badge/DOI/10.5281/zenodo.12627597.svg" alt="DOI">
  </a>
</p>

The qBraid-SDK is a platform-agnostic quantum runtime framework designed for both quantum software and hardware providers.

This Python-based tool streamlines the full lifecycle management of quantum jobs&mdash;from defining program specifications to job submission and through to the post-processing and visualization of results. Unlike existing runtime frameworks that focus their automation and abstractions on quantum components, qBraid adds an extra layer of abstractions that considers the ultimate IR needed to encode the quantum program and securely submit it to a remote API. Notably, the qBraid-SDK does not adhere to a fixed circuit-building library, or quantum program representation. Instead, it empowers providers to dynamically register any desired input program type as the target based on their specific needs. This flexibility is extended by the framework’s modular pipeline, which facilitates any number of additional program validation, transpilation, and compilation steps.

By addressing the full scope of client-side software requirements necessary for secure submission and management of quantum jobs, the qBraid-SDK vastly reduces the overhead and redundancy typically associated with the development of internal pipelines and cross-platform integrations in quantum computing.

[<img src="https://qbraid-static.s3.amazonaws.com/logos/Launch_on_qBraid_white.png" width="150">](https://account.qbraid.com?gitHubUrl=https://github.com/qBraid/qBraid.git)

---

![Runtime Diagram](https://qbraid-static.s3.amazonaws.com/qbraid-runtime.png)

## Resources

- [User Guide](https://docs.qbraid.com/sdk/user-guide/)
- [API Reference](https://sdk.qbraid.com/en/stable/api/qbraid.html)
- [Example Notebooks](https://github.com/qBraid/qbraid-lab-demo)

## Installation & Setup

For the best experience, install the qBraid-SDK environment on [lab.qbraid.com](https://lab.qbraid.com). Login (or
[create an account](https://account.qbraid.com)) and follow the steps to
[install an environment](https://docs.qbraid.com/lab/user-guide/environments#install-environment). Using the SDK on [qBraid Lab](https://docs.qbraid.com/lab/user-guide/overview) means direct, pre-configured access to QPUs from IonQ, Oxford Quantum Circuits, QuEra, Rigetti, and IQM, as well as on-demand simulators from qBraid and AWS. See [qBraid Quantum Jobs](https://docs.qbraid.com/lab/user-guide/quantum-jobs) for more.

### Local install

The qBraid-SDK, and all of its dependencies, can be installed using pip:

```bash
pip install qbraid
```

You can also [install from source](CONTRIBUTING.md#installing-from-source) by cloning this repository and running a pip install command in the root directory of the repository:

```bash
git clone https://github.com/qBraid/qBraid.git
cd qBraid
pip install .
```

> *Note:* The qBraid-SDK requires Python 3.9 or greater.

To use [qBraid Runtime](https://docs.qbraid.com/sdk/user-guide/runtime) locally, you must also install the necessary extras and configure your account credentials according to the device(s) that you are targeting. Follow the linked, provider-specific, instructions for the [QbraidProvider](https://docs.qbraid.com/sdk/user-guide/runtime_native), [BraketProvider](https://docs.qbraid.com/sdk/user-guide/runtime_braket), [QiskitRuntimeProvider](https://docs.qbraid.com/sdk/user-guide/runtime_ibm), [IonQProvider](https://docs.qbraid.com/sdk/user-guide/runtime_ionq), and [OQCProvider](https://docs.qbraid.com/sdk/user-guide/runtime_oqc), as applicable.

## Quickstart

### Check version

You can view the version of the qBraid-SDK you have installed and get detailed information about the installation within Python using the following commands:

```python
In [1]: import qbraid

In [2]: qbraid.__version__

In [3]: qbraid.about()
```

### Transpiler

Graph-based approach to quantum program type conversions.

Below, `QPROGRAM_REGISTRY` maps shorthand identifiers for supported quantum programs, each corresponding to a type in the typed `QPROGRAM` Union. For example, 'qiskit' maps to `qiskit.QuantumCircuit` in `QPROGRAM`. Notably, 'qasm2' and 'qasm3' both represent raw OpenQASM strings. This arrangement simplifies targeting and transpiling between different quantum programming frameworks.

```python
>>> from qbraid import QPROGRAM_REGISTRY
>>> QPROGRAM_REGISTRY
{'cirq': cirq.circuits.circuit.Circuit,
 'qiskit': qiskit.circuit.quantumcircuit.QuantumCircuit,
 'pennylane': pennylane.tape.tape.QuantumTape,
 'pyquil': pyquil.quil.Program,
 'pytket': pytket._tket.circuit.Circuit,
 'braket': braket.circuits.circuit.Circuit,
 'openqasm3': openqasm3.ast.Program,
 'pyqir': pyqir.Module,
 'qasm2': str,
 'qasm3': str}
```

Pass any registered quantum program along with a target package from
`QPROGRAM_REGISTRY` to "transpile" your circuit to a new program type:

```python
>>> from qbraid import random_circuit, transpile
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

Behind the scenes, the qBraid-SDK uses [rustworkx](https://www.rustworkx.org/) to create a
directional graph that maps all possible conversions between supported program types:

```python
from qbraid import ConversionGraph

# Loads native conversions from QPROGRAM_REGISTRY
graph = ConversionGraph()

graph.plot(legend=True)
```

<img src="https://qbraid-static.s3.amazonaws.com/conversion_graph_extras_legend.png" style="width: 65%;">

You can use the native conversions supported by qBraid, or define your own. For [example](https://docs.qbraid.com/sdk/user-guide/transpiler#conversion-graph):

```python
from unittest.mock import Mock

from qbraid import Conversion, register_program_type

# replace with any program type
register_program_type(Mock, alias="mock")

# replace with your custom conversion function
example_qasm3_to_mock_func = lambda x: x

conversion = Conversion("qasm3", "mock", example_qasm3_to_mock_func)

graph.add_conversion(conversion)

# using a seed is helpful to ensure reproducibility
graph.plot(seed=20, k=3, legend=True)
```

### QbraidProvider

Run experiements using on-demand simulators provided by qBraid. Retrieve a list of available devices:

```python
from qbraid import QbraidProvider

provider = QbraidProvider()
devices = provider.get_devices()
```

Or, instantiate a known device by ID and submit quantum jobs from any supported program type:

```python
device = provider.get_device("qbraid_qir_simulator")
jobs = device.run([qiskit_circuit, braket_circuit, cirq_circuit, qasm3_str], shots=1000)

results = [job.result() for job in jobs]
batch_counts = [result.data.get_counts() for result in results]

print(batch_counts[0])
# {'00': 483, '01': 14, '10': 486, '11': 17}
```

And visualize the results:

```python
from qbraid.visualization import plot_distribution, plot_histogram

plot_distribution(batch_counts)

plot_histogram(batch_counts)
```

## Get Involved

[![Community](https://img.shields.io/badge/Community-DF0982)](https://github.com/qBraid/community)
[![GitHub Issues](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/qBraid/qBraid/issues)
[![Stack Exchange](https://img.shields.io/badge/StackExchange-qbraid-orange?logo=stackexchange)](https://quantumcomputing.stackexchange.com/questions/tagged/qbraid)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.gg/TPBU2sa8Et)

- Interested in contributing code, or making a PR? See
  [CONTRIBUTING.md](CONTRIBUTING.md)
- For feature requests and bug reports:
  [Submit an issue](https://github.com/qBraid/qBraid/issues)
- For discussions, and specific questions about the qBraid-SDK [join our discord community](https://discord.gg/TPBU2sa8Et)
- For questions that are more suited for a forum, post to [QCSE](https://quantumcomputing.stackexchange.com/) with the [`qbraid`](https://quantumcomputing.stackexchange.com/questions/tagged/qbraid) tag.

## Launch on qBraid

The "Launch on qBraid" button (top) can be added to any public GitHub
repository. Clicking on it automaically opens qBraid Lab, and performs a
`git clone` of the project repo into your account's home directory. Copy the
code below, and replace `YOUR-USERNAME` and `YOUR-REPOSITORY` with your GitHub
info.

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

## License

[GNU General Public License v3.0](LICENSE)
