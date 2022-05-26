.. _cli_envs_pip:

qbraid envs <environment> pip
==============================

Run pip commands in environment.

.. code-block:: bash

    qbraid envs <environment> pip <command> [options]


Run ``pip --help`` to get a full list of available commands.


Examples
---------

.. code-block:: console
    
    $ qbraid envs qbraid_sdk pip install pip-install-test
    Collecting pip-install-test
    Downloading pip_install_test-0.5-py3-none-any.whl (1.7 kB)
    Installing collected packages: pip-install-test
    Successfully installed pip-install-test-0.5
    $ qbraid envs qbraid_sdk pip show pip-install-test
    Name: pip-install-test
    Version: 0.5
    Summary: A minimal stub package to test success of pip install
    ...


.. seealso::

    - `pip docs <https://pip.pypa.io/en/stable/>`_