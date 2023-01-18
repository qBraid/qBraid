.. _lab_quantumjobs:

Quantum Jobs
=============

Introductory paragraph / overview about quantum jobs ....

Make sure to include pictures, code, and links throughout this guide so anyone can follow it.

For RST syntax and how to include pictures / links etc. just try to look at the other
pages as reference and copy that. There's also rst cheat sheets available online.


Get credits
------------

Text about what qBraid credits are and broadly how they work. Talk about how you can get credits
via an access code (link `Add an access key <account.html#add-access-key>`_) or how you can buy
credits in bundles via https://account.qbraid.com/billing.

Then, after redeeming access key or purchasing credits have them verify that the credits have been
added to their account. Include pictures as needed.


Setup environment
-------------------

Directions to launch lab and open environment manager. Mention how environments with the 
``quantum jobs`` tag are ones that include quantum jobs. Example install Amazon Braket 
environment and link to  `Install environment <environments.html#install-environment>`_ section.
Make sure to remind them to activate the environment as well.


Enable qBraid jobs
--------------------

Have them open terminal (pictures help) and enter

.. code-block:: console
    
    $ qbraid envs list
    Installed environments:
    default
    qiskit
    amazon_braket
    qbraid_sdk
    Use `qbraid envs -h` to see available commands.


and make sure they see their installed environment name e.g. Amazon Braket.
Link to CLI commands if possible. Then desribe how you can enable
quantum jobs with

.. code-block:: console
    
    qbraid jobs enable amazon_braket


Submit a quantum job
---------------------

Walk through opening an Amazon Braket notebook from the ``qbraid-tutorials`` folder
or somewhere else, and submitting a quantum job to a remote simulator.

Show them the next CLI commands

.. code-block:: console
    
    qbraid jobs list
    qbraid jobs get-credits

and how their job is listed and credits have been subtracted.


Manage quantum jobs
--------------------

Then have them open the QJOBS labextension in the sidebar and see their job in the list.
Show them how their credits are in the top right, and how they can filter for jobs based
on status and provider. Describe the refresh button and how it retrieves their jobs, updates
their credits, and gets the latest job status.

Open the drop down of the job they just submitted and have them look at the details of their job.




