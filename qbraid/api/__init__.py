"""
==========================
 API (:mod:`qbraid.api`)
==========================

.. currentmodule:: qbraid.api

.. autosummary::
   :toctree: ../stubs/

   get_devices
   ibmq_least_busy_qpu
   refresh_devices
   update_config
   ApiError
   AuthError
   ConfigError
   RequestsApiError

.. autoclass:: QbraidSession
 
   .. automethod:: __init__

   .. rubric:: Methods

   .. autosummary::
   
      ~QbraidSession.__init__
      ~QbraidSession.close
      ~QbraidSession.delete
      ~QbraidSession.get
      ~QbraidSession.get_adapter
      ~QbraidSession.get_redirect_target
      ~QbraidSession.head
      ~QbraidSession.merge_environment_settings
      ~QbraidSession.mount
      ~QbraidSession.options
      ~QbraidSession.patch
      ~QbraidSession.post
      ~QbraidSession.prepare_request
      ~QbraidSession.put
      ~QbraidSession.rebuild_auth
      ~QbraidSession.rebuild_method
      ~QbraidSession.rebuild_proxies
      ~QbraidSession.request
      ~QbraidSession.resolve_redirects
      ~QbraidSession.send
      ~QbraidSession.should_strip_auth

   .. rubric:: Attributes

   .. autosummary::

      ~QbraidSession.base_url
      ~QbraidSession.user_email
      ~QbraidSession.id_token
      ~QbraidSession.refresh_token

"""
# pylint: skip-file

from .config_user import update_config
from .device_api import get_devices, refresh_devices
from .exceptions import ApiError, AuthError, ConfigError, RequestsApiError
from .least_busy import ibmq_least_busy_qpu
from .session import QbraidSession
