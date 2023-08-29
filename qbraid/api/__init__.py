# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: skip-file

"""
==========================
 API (:mod:`qbraid.api`)
==========================

.. currentmodule:: qbraid.api

.. autosummary::
   :toctree: ../stubs/

   ApiError
   AuthError
   ConfigError
   RequestsApiError
   PostForcelistRetry

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
      ~QbraidSession.api_key
      ~QbraidSession.refresh_token

"""
from .exceptions import ApiError, AuthError, ConfigError, RequestsApiError
from .retry import PostForcelistRetry
from .session import QbraidSession
