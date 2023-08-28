.. _lab_julia:

Julia
======

`Julia <https://julialang.org/>`_ is a high-performance, high-level programming language known for its ease of use and impressive computational
capabilities, especially in numerical and scientific computing, machine learning, data science, and most recently, quantum computing! Julia is
available on qBraid Lab with pre-configured IJulia notebooks, and with a number of quantum computing software packages pre-installed.

Bloqade Lab Image
-------------------

.. image:: ../_static/julia/qbraid_julia_bloqade.png
    :align: center
    :width: 40%
    :alt: qBraid x Julia x Bloqade
    :target: javascript:void(0);

`Bloqade <https://queracomputing.github.io/Bloqade.jl/stable/>`_ is a `Julia Language <https://julialang.org/>`_ package developed for
quantum computation and quantum simulation based on the neutral-atom architecture with the ability to submit tasks to
`QuEra's Aquila quantum processor <https://www.quera.com/aquila>`_. Bloqade is available working out-of-the-box through qBraid Lab, is free-to-use,
and requires little to no setup. Built on top of Ubuntu Server 20.04 LTS, this image includes:

- The latest version of Julia and Bloqade
- `Yao.jl <https://yaoquantum.org/>`_
- `Revise.jl <https://github.com/timholy/Revise.jl>`_
- `BenchmarkTools.jl <https://juliaci.github.io/BenchmarkTools.jl/stable/>`_
- `PythonCall.jl <https://cjdoris.github.io/PythonCall.jl/stable/>`_
- Conda package manager, provided by `Mamba <https://mamba.readthedocs.io/en/latest/index.html>`_
- Jupyter Lab interface with dedicated Julia and Python kernels
- Integrated Terminal for interactive command-line sessions

See `qBraid system info <system.html>`_ for more.


Step 0: Redeem Access Key
^^^^^^^^^^^^^^^^^^^^^^^^^^

Login to `account.qbraid.com <https://account.qbraid.com/>`_. On the left side of your dashboard, inside the **Plan** card, click **Manage**.

.. image:: ../_static/julia/00_manage.png
    :width: 90%
    :alt: Manage account
    :target: javascript:void(0);


.. image:: ../_static/julia/01_access_key.png
    :align: right
    :width: 400px
    :alt: Bloqade access key
    :target: javascript:void(0);
  
|

Scroll down to find the card marked **Access Key**. Enter code ``NEUTRALATOM`` and click **Submit**.
This will grant you access to the Bloqade Lab image as well as a number of other premium features.

For more on creating an account and adding an access key, see `Account <account.html>`_.

|

Step 1: Select Image & Launch Lab
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At the top of your account page, open the image drop down. Select the option named **Bloqade_2vCPU_4GB**,
and then click Launch Lab. Pulling the Bloqade image may take 2-3 minutes the first time. The next time you
launch Lab, it will load much more quickly. See `Launch Lab <getting_started.html#launch-lab>`_.

.. image:: ../_static/julia/10_launch_bloqade.png
    :align: center
    :width: 70%
    :alt: Launch Bloqade Image
    :target: javascript:void(0);
  
|

Step 2: Develop with Notebooks or from Command-Line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once qBraid Lab is loaded, you are all set! No further setup is required. In the middle of your screen you can click the **Julia 1.9** kernel
to open a new Jupyter Notebook configured with the Julia executable. Alternatively, you can click to open **Terminal** and run an interactive
``julia`` session from the command-line. In this qBraid Lab image, Bloqade is pre-installed and pre-compiled, so you should be able to get started
using ``Bloqade`` right away.

.. image:: ../_static/julia/11_bloqade_lab.png
    :align: center
    :width: 95%
    :alt: Bloqade Lab Image
    :target: javascript:void(0);
  
|


Step 3: Explore More Features
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `Environment Manager <environments.html>`_, located in the right sidebar of qBraid Lab, provides a graphical user interface for
creating and managing Python virtual environments. This particular Lab image comes with a pre-installed Bloqade Python Wrapper environment.
Clicking **Activate** will create a corresponding IPykernel, and allow you to run Jupyter Notebooks using the ``bloqade`` Python package.

In the bottom right corner qBraid Lab, click **Start Tour** for an interactive walkthrough. You can re-start the tour and access other useful
links from the Help drop-down in the top menu bar. To stop and/or restart your session, click **File** > **Hub Control Panel** > **Stop My Server**.
For more on the qBraid Lab interface, and managing your qBraid Lab session, see `Getting Started <getting_started.html>`_.


Configuration
---------------

In qBraid Lab, the ``JULIA_DEPOT_PATH`` is set to ``/opt/.julia``. This default setting means that any additional Julia packages
installed will be stored at the system level, and therefore will not persist between sessions. To persist additional packages,
caches, configs, and other Julia updates, they must be saved at the user level (e.g. ``/home/jovyan/.julia``). This can be done by updating
the depot path:

.. code-block:: bash
    
    export JULIA_DEPOT_PATH="/home/jovyan/.julia:$JULIA_DEPOT_PATH"


See `Julia environment variables <https://docs.julialang.org/en/v1/manual/environment-variables/#JULIA_DEPOT_PATH>`_ for more.


Troubleshooting
----------------

Julia kernel not connecting
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are unable to connect to the Julia kernel, make sure that you do not have any ``Project.toml`` or ``Manifest.toml`` in your working directory,
as these project dependencies may conflict with pre-installed packages and cause the kernel to fail. If you are still having trouble, try restarting
your session. If the problem continues to persist, please `contact us <https://qbraid.com/contact-us/>`_.

.. seealso::

    `Project.toml and Manifest.toml <https://pkgdocs.julialang.org/v1/toml-files/#Project-and-Manifest>`_
