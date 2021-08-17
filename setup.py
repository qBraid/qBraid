from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("qbraid/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

setup(
    name="qbraid",
    version=version,
    description="Platform for accessing quantum computers",
    url="https://github.com/qBraid/qBraid",
    author="qBraid Development Team",
    author_email="noreply@qBraid.com",
    license="Restricted",
    packages=find_packages(exclude=["test*"]),
    install_requires=requirements,
    python_requires=">=3.7.2",
    entry_points={
        "qbraid.transpiler": [
            "braket = qbraid.transpiler.braket:BraketCircuitWrapper",
            "cirq = qbraid.transpiler.cirq:CirqCircuitWrapper",
            "qiskit = qbraid.transpiler.qiskit:QiskitCircuitWrapper",
            "qbraid = qbraid.transpiler.qbraid:QbraidCircuitWrapper"
        ],
        "qbraid.devices": [
            "aws = qbraid.devices.aws:BraketDeviceWrapper",
            "google = qbraid.devices.google:CirqSimulatorWrapper",
            "ibm = qbraid.devices.ibm:QiskitBackendWrapper"
        ]
    },
    zip_safe=False,
)
