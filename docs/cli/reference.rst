Reference
==========

The qBraid CLI comes pre-installed in qBraid Lab.

.. code-block:: console

   $ which qbraid
   /usr/bin/qbraid

Run ``qbraid help`` to list the available commands.

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


.. toctree::
   :maxdepth: 1
   :caption: Commands

   commands/activate
   commands/credits
   commands/disable-account
   commands/enable-account
   commands/envs
   commands/freeze
   commands/help
   commands/install
   commands/list
   commands/show
