.. _sdk_providers:

Providers
==========

.. code-block:: python

    >>> from qbraid.runtime.native import QbraidProvider
    >>> provider = QbraidProvider()
    >>> QbraidProvider.get_devices()
    ...
    >>> device = provider.get_device('qbraid_qir_simulator')
