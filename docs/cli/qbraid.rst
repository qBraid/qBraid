.. _cli:

qbraid
=======

.. |br| raw:: html

   <br />

.. raw:: html
   
   <h1 style="text-align: center">
      <img src="../_static/logo.png" alt="qbraid logo" style="width:50px;height:50px;">
      <span> qBraid</span>
      <span style="color:#808080"> | CLI</span>
   </h1>
   <p style="text-align:center;font-style:italic;color:#808080">
      Universal Command Line Interface for interacting with all parts of the qBraid platform.
   </p>


**Version 0.4.1**

Commands
---------
+---------------------------------------+---------------------------------------------------+
| ``qbraid envs``                       | Manage qBraid environments.                       |
+---------------------------------------+---------------------------------------------------+
| ``qbraid jobs``                       | Manage qBraid Quantum Jobs.                       |
+---------------------------------------+---------------------------------------------------+
| ``qbraid kernels``                    | Manage qBraid kernels.                            |
+---------------------------------------+---------------------------------------------------+

Quick Start
-------------

The qBraid CLI is available exclusively through `qBraid Lab <https://lab.qbraid.com>`_.
Login (or create an account) and then open Termainal to get started using the CLI.

.. code-block:: console

   $ qbraid
   -------------------------------
   * Welcome to the qBraid CLI! *
   -------------------------------

   - Use `qbraid -h` to see available commands.

   - Use `qbraid --version` to display the current version.

   Reference Docs: https://docs.qbraid.com/en/latest/cli/qbraid.html

**List environments** installed in your qBraid Lab instance using:

.. code-block:: console
   
   $ qbraid envs list
   # installed environments:
   #
   qsharp                         /opt/.qbraid/environments/qsharp_b54crn
   default                  jobs  /opt/.qbraid/environments/qbraid_000000
   qbraid_sdk               jobs  /home/jovyan/.qbraid/environments/qbraid_sdk_9j9sjy
   custom_env                     /home/jovyan/.qbraid/environments/custom_env_lj3zlt

Environments with the ``jobs`` keyword listed before their path support
qBraid Quantum Jobs. To use qBraid Quantum Jobs in an environment, it must have
`Amazon Braket <https://docs.aws.amazon.com/braket/index.html>`_ installed.

By default, your qBraid terminal opens using Python (and pip) from ``/opt/conda/bin``.
Packages that are installed directly at this top-level will *not* persist between sessions.
Instead, use the qBraid CLI to **install new packages** directly into one of your listed
qBraid environments:

.. code-block:: console

   $ qbraid envs activate custom_env          # activate environment
   $ python -m pip install amazon-braket-sdk  # pip install package
   $ deactivate

Once Amazon Braket is installed in an environment, **add** and **enable quantum jobs**:

.. code-block:: console

   $ qbraid jobs add custom_env     # configure quantum jobs
   $ qbraid jobs enable custom_env  # toggle quantum jobs on

Congrats! Every AWS job you run in this environment will now be submitted through the qBraid API,
so **no access keys are necessary**. At any time, you can switch back to using your own AWS credentials
by disabling quantum jobs:

.. code-block:: console

   $ qbraid jobs disable custom_env  # toggle quantum jobs off
