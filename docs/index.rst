.. _home:

qBraid Documentation
=====================

A cloud-based platform for quantum computing.

.. rst-class:: lead grey-text ml-2
   
.. raw:: html

   <html>
   <head>
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <style>
   * {
   box-sizing: border-box;
   }

   body {
   font-family: Arial, Helvetica, sans-serif;
   }

   /* Float four columns side by side */
   .column {
   float: left;
   width: 25%;
   padding: 0 10px;
   }

   /* Remove extra left and right margins, due to padding */
   .row {margin: 0 -5px;}

   /* Clear floats after the columns */
   .row:after {
   content: "";
   display: table;
   clear: both;
   }

   /* Responsive columns */
   @media screen and (max-width: 600px) {
   .column {
      width: 100%;
      display: block;
      margin-bottom: 20px;
   }
   }

   /* Style the counter cards */
   .card {
   box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2);
   padding: 16px;
   text-align: center;
   background-color: #f1f1f1;
   }
   </style>
   </head>
   <body>

   <div class="row">
   <div class="column">
      <div class="card">
         <h3>Lab</h3>
         <p>Some text</p>
      </div>
   </div>
   
   <div class="column">
      <div class="card">
         <h3>CLI</h3>
         <p>Some text</p>
      </div>
   </div>
   
   <div class="column">
      <div class="card">
         <h3>SDK</h3>
         <p>Some text</p>
      </div>
   </div>
   </div>

   </body>
   </html>


Features
---------

.. image:: _static/logo.png
   :align: left
   :width: 275px
   :target: qBraid_

.. _qBraid: https://qbraid.com/home.html


- **Lab**: Customized JupyterLab console built specifically for quantum computing developers, researchers, and students.

..

- **CLI**: Gain access to quantum hardware from D-Wave, IonQ, Rigetti, Oxford Quantum Circuits, and more, using qBraid credits, all from one account.

..

- **SDK**: Python toolkit for building and executing quantum programs. Interface between quantum circuit building frontends including Qiskit, Pennylane, Cirq, Amazon Braket, and pyQuil.



.. toctree::
   :maxdepth: 1
   :caption: Overview
   :hidden:

   overview/lab
   overview/cli
   overview/sdk

.. toctree::
   :maxdepth: 1
   :caption: User Guide
   :hidden:

   guide/getstart
   guide/intro
   guide/circuits
   guide/devices
   guide/jobs
   guide/results

.. toctree::
   :maxdepth: 1
   :caption: CLI Reference
   :hidden:

   cli/qbraid


.. toctree::
   :maxdepth: 1
   :caption: SDK Reference
   :hidden:

   sdk/qbraid
   sdk/qbraid.api
   sdk/qbraid.interface
   sdk/qbraid.transpiler
   sdk/qbraid.devices


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
