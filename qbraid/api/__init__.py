# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: skip-file

"""
==========================
 API (:mod:`qbraid.api`)
==========================

.. currentmodule:: qbraid.api

.. autosummary::
   :toctree: ../stubs/

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
      ~QbraidSession.get_config_variable
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
      ~QbraidSession.save_config
      ~QbraidSession.send
      ~QbraidSession.should_strip_auth

   .. rubric:: Attributes

   .. autosummary::

      ~QbraidSession.base_url
      ~QbraidSession.user_email
      ~QbraidSession.refresh_token

"""
from .exceptions import ApiError, AuthError, ConfigError, RequestsApiError
from .job_api import get_job_data, init_job
from .session import QbraidSession
