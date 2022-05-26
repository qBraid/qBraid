.. _cli_envs_uninstall:

qbraid envs <environment> uninstall
====================================

Uninstall qBraid environment.

.. code-block:: bash

    qbraid envs <environment> uninstall


Examples
---------

.. code-block:: console

    $ qbraid envs list
    Installed environments:
    qsharp
    default
    qiskit
    Use `qbraid envs <environment> -h` to see available commands.
    $ qbraid envs qiskit uninstall
    $ qbraid envs list
    Installed environments:
    qsharp
    default
    Use `qbraid envs <environment> -h` to see available commands.


.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`
