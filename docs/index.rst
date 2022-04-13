Documentation
==============
   
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
   display: inline-block;
   vertical-align: middle;
   float: none;
   width: 25%;
   padding: 0 10px;
   }

   /* Remove extra left and right margins, due to padding */
   .row {
   text-align: center;
   margin:0 auto;
   }

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
   <h1 style="text-align: center">
      <img src="_static/logo.png" alt="qbraid logo" style="width:50px;height:50px;">
      <span> qBraid</span>
      <span style="color:#808080"></span>
   </h1>
   <p style="text-align:center;font-style:italic;color:#808080">
      A cloud-based platform for quantum computing.
   </p>
   <div class="row">
   <div class="column">
      <a href="lab/overview.html">
         <div class="card">
            <h3>Lab</h3>
            <img src="_static/cards/jupyter.png" alt="terminal" style="width:60px;height:60px;">
         </div>
      </a>
   </div>
   
   <div class="column">
      <a href="cli/overview.html">
         <div class="card">
            <h3>CLI</h3>
            <img src="_static/cards/terminal.png" alt="terminal" style="width:60px;height:60px;">
         </div>
      </a>
   </div>
   
   <div class="column">
      <a href="sdk/overview.html">
         <div class="card">
            <h3>SDK</h3>
            <img src="_static/cards/python.png" alt="terminal" style="width:60px;height:60px;">
         </div>
      </a>
   </div>
   </div>

   </body>
   </html>

|

.. toctree::
   :maxdepth: 1
   :caption: qBraid Lab
   :hidden:

   lab/overview

.. toctree::
   :maxdepth: 1
   :caption: qBraid CLI
   :hidden:

   cli/overview
   cli/reference

.. toctree::
   :maxdepth: 1
   :caption: qBraid SDK
   :hidden:

   sdk/overview
   sdk/getstart
   sdk/intro
   sdk/circuits
   sdk/devices
   sdk/jobs
   sdk/results

.. toctree::
   :maxdepth: 1
   :caption: API Reference
   :hidden:

   api/qbraid
   api/qbraid.api
   api/qbraid.interface
   api/qbraid.transpiler
   api/qbraid.devices


.. Indices and Tables
.. ------------------

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
