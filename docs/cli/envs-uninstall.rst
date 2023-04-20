.. _cli_envs_uninstall:

qbraid envs uninstall
======================

Uninstall qBraid environment.

.. code-block:: bash

    qbraid envs uninstall [env_name]


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
    qiskit                   jobs  /home/jovyan/.qbraid/environments/qiskit_9y9siy
    $ qbraid envs uninstall qiskit
    $ qbraid envs list
    # installed environments:
    #
    qsharp                         /opt/.qbraid/environments/qsharp_b54crn
    default                  jobs  /opt/.qbraid/environments/qbraid_000000


.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`
