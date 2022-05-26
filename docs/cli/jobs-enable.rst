.. _cli_jobs_enable:

qbraid jobs enable
====================

Enable qBraid Quantum Jobs.

.. code-block:: bash

    qbraid jobs enable --name


Required Parameters
--------------------

``--name -n`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ qbraid jobs enable -n qbraid_sdk
    You are now submitting jobs with qBraid Quantum Jobs.
    Every job you run will be taken care of with our API, so no access keys are necessary. 

    To disable, run: `qbraid jobs disable -n qbraid_sdk`


qBraid environments with support for quantum jobs include ``aws_braket`` and ``qbraid_sdk``.

.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`
    - :ref:`qbraid jobs disable<cli_jobs_disable>`