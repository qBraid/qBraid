.. _cmds_install:

.. role:: raw-html(raw)
   :format: html

qbraid install
===============

Install package into a virtual environment.

.. code-block:: bash

    qbraid install <package> <environment>


Positional arguments
---------------------

``<package>`` : Name package to install. |br|
``<environment>`` : Name of qBraid virtual environment.

.. |br| raw:: html

    <br></br>


Examples
---------

.. code-block:: console
    
    $ qbraid install pip-install-test aws_braket
    Collecting pip-install-test
    Downloading pip_install_test-0.5-py3-none-any.whl (1.7 kB)
    Installing collected packages: pip-install-test
    Successfully installed pip-install-test-0.5
    $ qbraid show aws_braket pip-install-test
    Name: pip-install-test
    Version: 0.5
    Summary: A minimal stub package to test success of pip install
    ...


.. seealso::

    - :ref:`qbraid envs<cmds_envs>`
    - `pip install <https://pip.pypa.io/en/stable/cli/pip_install/#pip-install>`_