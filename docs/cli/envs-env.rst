.. _cli_envs_name:

qbraid envs <environment>
==========================

Manage qBraid environment.

Arguments
----------
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs amazon_braket``           | Manage Amazon Braket environment.                 |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs cirq_openfermion``        | Manage Cirq & OpenFermion environment.            |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs pennylane``               | Manage Pennylane environment.                     |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs pulser``                  | Manage Pulser environment.                        |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs pyquil``                  | Manage pyQuil environment.                        |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs default``                 | Manage Default quantum development environment.   |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs qbraid_sdk``              | Manage qBraid SDK environment.                    |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs qiskit``                  | Manage Qiskit environment.                        |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs qsharp``                  | Manage Microsoft Q# environment.                  |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs qutech_qi``               | Manage QuTech QI-SDK environment.                 |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs qutech_qne``              | Manage QuTech QNE-ADK environment.                |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs tensorflow``              | Manage TensorFlow environment.                    |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs unitary_fund``            | Manage Unitary Fund environment.                  |
+-----------------------------------------+---------------------------------------------------+

Commands
---------
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs <environment> pip``       | Run pip commands in environment.                  |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs <environment> activate``  | Activate qBraid environment.                      |
+-----------------------------------------+---------------------------------------------------+
| ``qbraid envs <environment> uninstall`` | Uninstall qBraid environment.                     |
+-----------------------------------------+---------------------------------------------------+

.. toctree::
   :maxdepth: 1

   envs-env-activate
   envs-env-pip
   envs-env-uninstall