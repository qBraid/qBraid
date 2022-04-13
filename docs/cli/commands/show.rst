.. _cmds_show:

qbraid show
============

Display information about a package installed in a virtual environment.

.. code-block:: bash

    qbraid show <environment> <package>


Positional arguments
---------------------

``<environment>`` : Name of qBraid virtual environment. |br|
``<package>`` : Name of package for which to display information.

.. |br| raw:: html

    <br></br>


Examples
---------

.. code-block:: console

    $ qbraid show qbraid_sdk qiskit
    Name: qiskit
    Version: 0.34.2
    Summary: Software for developing quantum computing programs
    ...


.. seealso::

    - :ref:`qbraid envs<cmds_envs>`
    - :ref:`qbraid list<cmds_freeze>`
    - `pip show <https://pip.pypa.io/en/stable/cli/pip_show/#pip-show>`_