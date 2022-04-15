Overview
=========

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


Installation
-------------

The qBraid CLI is available exclusively through `qBraid Lab <https://lab.qbraid.com>`_.
Login (or create an account) and then open Termainal to get started using the CLI.

.. code-block:: console

   $ which qbraid
   /usr/bin/qbraid


Usage
------

.. code-block:: bash

   qbraid <command>      

+---------------------------------------+---------------------------------------------------+
| **<command>**                         | **Description**                                   |
+---------------------------------------+---------------------------------------------------+
| ``install <package> <environment>``   | Install packages into specific environment.       |
+---------------------------------------+---------------------------------------------------+
| ``enable account <environment>``      | Enable AWS quantum jobs through qBraid.           |
+---------------------------------------+---------------------------------------------------+
| ``disable account <environment>``     | Disable AWS quantum jobs through qBraid.          |
+---------------------------------------+---------------------------------------------------+
| ``credits``                           | Shows how many qBraid credits you have left.      |
+---------------------------------------+---------------------------------------------------+
| ``freeze <environment>``              | Output installed packages in requirements form.   |
+---------------------------------------+---------------------------------------------------+
| ``show <environment>``                | Show information about installed packages.        |
+---------------------------------------+---------------------------------------------------+
| ``list <environment>``                | List installed packages.                          |
+---------------------------------------+---------------------------------------------------+
| ``envs``                              | List installed environments.                      |
+---------------------------------------+---------------------------------------------------+
| ``help``                              | Show help for commands.                           |
+---------------------------------------+---------------------------------------------------+
