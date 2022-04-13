.. _cmds_help:

qbraid help
============

Show help for commands.

.. code-block:: bash

    qbraid help


Examples
---------

.. code-block:: console

    $ qbraid help
    Usage: qbraid <command>
    Commands:
        install <package> <environment>                            Install packages into specific environment.
        enable account <environment>                               Enable AWS quantum jobs through qBraid.
        disable account <environment>                              Disable AWS quantum jobs through qBraid.
        credits                                                    Shows how many qBraid credits you have left.
        freeze <environment>                                       Output installed packages in requirements form.
        show <environment>                                         Show information about installed packages.
        list <environment>                                         List installed packages.
        envs                                                       List installed environments.
        help                                                       Show help for commands.
    General Options:                                             
    You can pass any optional pip commands as well :)
