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
      A Command Line Interface for interacting with all parts of the qBraid platform.
   </p>


**Version 0.2.0**

The qBraid CLI is available exclusively through `qBraid Lab <https://lab.qbraid.com>`_.
Login (or create an account) and then open Termainal to get started using the CLI.

.. code-block:: console

   $ which qbraid
   /usr/bin/qbraid

.. code-block:: console

   $ qbraid
   -------------------------------
   * Welcome to the qBraid CLI! *
   -------------------------------

   - Use `qbraid -h` to see available commands.

   - Use `qbraid --version` to display the current version.

   Reference Docs: https://qbraid-qbraid.readthedocs-hosted.com/en/latest/cli/qbraid.html

Commands
---------
+---------------------------------------+---------------------------------------------------+
| ``qbraid envs``                       | Manage qBraid environments.                       |
+---------------------------------------+---------------------------------------------------+
| ``qbraid jobs``                       | Manage qBraid Quantum Jobs.                       |
+---------------------------------------+---------------------------------------------------+
| ``qbraid kernels``                    | Manage qBraid kernels.                            |
+---------------------------------------+---------------------------------------------------+

