.. _sdk_providers:

Providers
==========

.. code-block:: python

    >>> from qbraid.runtime import QbraidProvider
    >>> provider = QbraidProvider()
    >>> QbraidProvider.get_devices()
    ...
    >>> device = provider.get_device('device_id')


.. seealso::

    - https://github.com/qBraid/qbraid-lab-demo/blob/main/qbraid_sdk/qbraid_sdk_providers.ipynb