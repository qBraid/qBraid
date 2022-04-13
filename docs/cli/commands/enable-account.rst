.. _cmds_enable_account:

qbraid enable account
=======================

Enable quantum jobs through qBraid.

.. code-block:: bash

    qbraid enable account <environment>


qBraid environments with support for quantum jobs include:
    - ``aws_braket``
    - ``qbraid_sdk``


Positional arguments
---------------------

``<environment>`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ qbraid enable account qbraid_sdk
    You are now submitting jobs with qBraid Quantum Jobs.
    Every job you run will be taken care of with our API, so no access keys are necessary.
    To disable run the command:  qbraid disable account qbraid_sdk
    $ qbraid enable account qbraid_sdk
    You have already enabled quantum jobs to be submitted with qBraid.


.. seealso::

    - :ref:`qbraid envs<cmds_envs>`
    - :ref:`qbraid disable account<cmds_disable_account>`