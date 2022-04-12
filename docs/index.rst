.. include:: _static/s5defs.txt
   
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
   <span style="color:#808080"> | Docs</span>
   </h1>
   <br></br>
   <div class="row">
   <div class="column">
      <a href="overview/lab.html">
         <div class="card">
            <h3>Lab</h3>
            <p>Some text</p>
         </div>
      </a>
   </div>
   
   <div class="column">
      <a href="overview/cli.html">
         <div class="card">
            <h3>CLI</h3>
            <p>Some text</p>
         </div>
      </a>
   </div>
   
   <div class="column">
      <a href="overview/sdk.html">
         <div class="card">
            <h3>SDK</h3>
            <p>Some text</p>
         </div>
      </a>
   </div>
   </div>

   </body>
   </html>


:white:`Docs`
--------------

.. toctree::
   :titlesonly:
   :caption: Overview
   :hidden:

   Lab <overview/lab>
   CLI <overview/cli>
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
   :caption: CLI API
   :hidden:

   cli/qbraid


.. toctree::
   :maxdepth: 1
   :caption: SDK API
   :hidden:

   sdk/qbraid
   sdk/qbraid.api
   sdk/qbraid.interface
   sdk/qbraid.transpiler
   sdk/qbraid.devices


.. Indices and Tables
.. ------------------

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
