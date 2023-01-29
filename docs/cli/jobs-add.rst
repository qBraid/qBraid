.. _cli_jobs_add:

qbraid jobs add
================

Add qBraid Quantum Jobs to environment.

.. code-block:: bash

    qbraid jobs add [env_name]


Positional Arguments
---------------------

``env_name`` : Name of environment. Values from: ``qbraid envs list``.


Examples
---------

.. code-block:: console

    $ qbraid envs list
    # installed environments:
    #
    qsharp                         /opt/.qbraid/environments/qsharp_b54crn
    default                  jobs  /opt/.qbraid/environments/qbraid_000000
    custom_env                     /home/jovyan/.qbraid/environments/custom_env_lj3zlt
    $ qbraid jobs add custom_env
    Success! Your custom_env environment now supports qBraid Quantum Jobs.

    To enable Quantum Jobs, run: `qbraid jobs enable custom_env`
    $ qbraid envs list
    # installed environments:
    #
    qsharp                         /opt/.qbraid/environments/qsharp_b54crn
    default                  jobs  /opt/.qbraid/environments/qbraid_000000
    custom_env               jobs  /home/jovyan/.qbraid/environments/custom_env_lj3zlt


.. note::

    Quantum jobs can only be added to environments which have `Amazon Braket <https://docs.aws.amazon.com/braket/index.html>`_ installed.

.. seealso::

    - :ref:`qbraid jobs enable<cli_jobs_enable>`
    - :ref:`qbraid envs list<cli_envs_list>`