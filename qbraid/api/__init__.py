"""
==========================
 API (:mod:`qbraid.api`)
==========================

.. currentmodule:: qbraid.api

.. autosummary::
   :toctree: ../stubs/

   ibmq_least_busy_qpu
   update_config
   get_config
   set_config
   verify_config
   init_job
   get_job_data
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

from .config_user import get_config, set_config, update_config, verify_config
from .exceptions import ApiError, AuthError, ConfigError, RequestsApiError
from .job_api import get_job_data, init_job
from .least_busy import ibmq_least_busy_qpu
from .session import QbraidSession
