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
    Installed environments:
    qsharp
    default
    qiskit
    Use `qbraid envs -h` to see available commands.
    $ qbraid envs qiskit uninstall
    $ qbraid envs list
    Installed environments:
    qsharp
    default
    Use `qbraid envs -h` to see available commands.


.. seealso::

    - :ref:`qbraid envs list<cli_envs_list>`
