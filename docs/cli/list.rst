.. _cmds_list:

qbraid list
============

List packages installed in virtual environment.

.. code-block:: bash

    qbraid list <environment>


Positional arguments
---------------------

``<environment>`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console

    $ qbraid list aws_braket
    Package                         Version
    ------------------------------- -----------
    absl-py                         0.15.0
    alembic                         1.7.5
    amazon-braket-default-simulator 1.5.0
    amazon-braket-ocean-plugin      1.0.9
    amazon-braket-pennylane-plugin  1.6.0
    amazon-braket-schemas           1.8.0
    amazon-braket-sdk               1.18.0
    ...

.. seealso::

    - :ref:`qbraid envs<cmds_envs>`
    - :ref:`qbraid freeze<cmds_freeze>`
    - `pip list <https://pip.pypa.io/en/stable/cli/pip_list/#pip-list>`_

