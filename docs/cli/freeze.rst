.. _cmds_freeze:

qbraid freeze
==============

Get packages installed in virtual environment in requirements form.

.. code-block:: bash

    qbraid freeze <environment>


Positional arguments
---------------------

``<environment>`` : Name of qBraid virtual environment.


Examples
---------

.. code-block:: console 

    $ qbraid freeze aws_braket
    absl-py==0.15.0
    alembic @ file:///home/conda/feedstock_root/build_artifacts/alembic_1636656371607/work
    amazon-braket-default-simulator==1.5.0
    amazon-braket-ocean-plugin==1.0.9
    amazon-braket-pennylane-plugin==1.6.0
    amazon-braket-schemas==1.8.0
    amazon-braket-sdk==1.18.0
    ...


.. seealso::

    - :ref:`qbraid envs<cmds_envs>`
    - :ref:`qbraid list<cmds_list>`
    - `pip freeze <https://pip.pypa.io/en/stable/cli/pip_freeze/#pip-freeze>`_