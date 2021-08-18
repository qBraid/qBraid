from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

with open("qbraid/_version.py") as f:
    version = f.readlines()[-1].split()[-1].strip("\"'")

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="qbraid",
    version=version,
    license="Restricted",
    author="qBraid Development Team",
    author_email="noreply@qBraid.com",
    description="Platform for accessing quantum computers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/qBraid/qBraid/",
    project_urls={
        "Bug Tracker": "https://github.com/qBraid/qBraid/issues",
    },
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    keywords=["qbraid", "quantum"],
    packages=find_packages(exclude=["tests*"]),
    install_requires=requirements,
    extras_require={
        "test": [
            "black",
            "jupyter",
            "pylint",
            "pytest",
            "sphinx",
            "sphinx-autodoc-typehints",
            "sphinx-rtd-theme",
        ]
    },
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
