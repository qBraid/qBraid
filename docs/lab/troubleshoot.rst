.. _lab_troubleshoot:

Troubleshooting
================

If you encounter an error that isn't included on this page or if the solution provided doesn't work, please
`reach out to us on Discord <https://discord.gg/gwBebaBZZX>`_, email us at request@qbraid.com, or
`open a bug report <https://github.com/qbraid/community/issues/new?assignees=&labels=bug&template=bug_report.md>`_.

Error launching Lab
---------------------

If you get one of the following errors while launching Lab,

- 400: Bad Request
- 500: Internal Server Error
- 503: Service Unavailable
- Spawn failed

your qBraid Lab server failed to start. Follow the prompts on the screen, or if none are given,
return to https://account.qbraid.com, and click **Launch Lab** to try again.


Lab server errors
------------------

If you get one of the following errors from inside Lab, 

- Service unavailable or unreachable
- File Save Error

you need to restart your qBraid Lab server. For these types of errors, refreshing the page won't work.
Instead, you need to pull down a new Lab image, which can only be done from the qBraid Hub Control Panel:

Go to **File** > **Hub Control Panel**, or type https://lab.qbraid.com/hub/home directly into your
browser. From there, click **Stop My Server** > **Start My Server** > **Launch Server**, and wait for Lab to reload.

ModuleNotFoundError
--------------------

While running a notebook, if you get a ``ModuleNotFoundError`` after an import statement:

1. Check to make sure you are using the correct notebook kernel for your environment,
see `Switch notebook kernel <kernels.html#switch-notebook-kernel>`_.

2. If you are using the correct kernel, the package you are trying to import may not be installed
in that environment. See `Install new package <environments.html#install-new-package>`_.

NoRegionError
--------------

If you are running an Amazon Braket notebook and get a ``NoRegionError``, it's likely that you have not enabled Quantum Jobs. Run

.. code-block::

  $ qbraid jobs enable amazon_braket
  
 and restart your kernel, and try running the notebook again. 

 .. seealso::
   
    -  _`Quantum Jobs <quantumjobs.html>`_




