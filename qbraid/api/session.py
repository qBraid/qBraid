"""Module for making requests to the qbraid api"""

import logging
from typing import Any, Dict, Optional

from requests import RequestException, Response, Session

from qbraid.api.config_user import get_config, qbraid_config_path, qbraidrc_path
from qbraid.api.exceptions import AuthError, ConfigError, RequestsApiError

logger = logging.getLogger(__name__)


class QbraidSession(Session):
    """Custom session with handling of request urls and authentication.

    This is a child class of ``requests.Session``. It handles qbraid
    authentication with custom headers, has SSL verification disabled
    for compatibility with lab, and returns all responses as jsons for
    convenience in the sdk.

    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        user_email: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        """QbraidSession constructor.

        Args:
            base_url: Base URL for the session's requests.
            user_email: JupyterHub User.
            auth_token: qBraid authentication token.

        """
        super().__init__()

        self.base_url = base_url
        self.user_email = user_email
        self.auth_token = auth_token
        self.verify = False

    def _get_config(self, field: str, section: str, path: str) -> Optional[str]:
        config = get_config(field, section, filepath=path)
        if config == -1 or config == "None":
            if field == "url":
                raise ConfigError(f"qBraid API URL {config} invalid or not found")
            else:
                msg = "user email" if field == "user" else field
                raise AuthError(f"qBraid {msg} invalid or not found")
        return config

    @property
    def base_url(self) -> Optional[str]:
        """Return the qbraid api url."""
        return self._base_url

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        """Set the qbraid api url."""
        url = value if value else self._get_config("url", "QBRAID", qbraid_config_path)
        self._base_url = url

    @property
    def user_email(self) -> Optional[str]:
        """Return the session user email."""
        return self._user_email

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set the session user email."""
        user = value if value else self._get_config("user", "sdk", qbraidrc_path)
        self._user_email = user
        self.headers.update({"email": user})  # type: ignore[attr-defined]

    @property
    def auth_token(self) -> Optional[str]:
        """Return the session refresh token."""
        return self._auth_token

    @auth_token.setter
    def auth_token(self, value: Optional[str]) -> None:
        """Set the session refresh token."""
        token = value if value else self._get_config("token", "sdk", qbraidrc_path)
        self._auth_token = token
        self.headers.update({"refresh-token": token})  # type: ignore[attr-defined]

    def request(self, method: str, url: str, **kwargs: Any) -> Response:  # type: ignore[override]
        """Construct, prepare, and send a ``Request``.
        Args:
            method: Method for the new request (e.g. ``POST``).
            url: URL for the new request.
            **kwargs: Additional arguments for the request.
        Returns:
            Response object.
        Raises:
            RequestsApiError: If the request failed.
        """
        # pylint: disable=arguments-differ
        final_url = self.base_url + url

        headers = self.headers.copy()
        headers.update(kwargs.pop("headers", {}))

        try:
            response = super().request(method, final_url, headers=headers, **kwargs)
            response.raise_for_status()
        except RequestException as ex:
            # Wrap requests exceptions for compatibility.
            message = str(ex)
            if ex.response is not None:
                try:
                    error_json = ex.response.json()["error"]
                    message += ". {}, Error code: {}.".format(
                        error_json["message"], error_json["code"]
                    )
                    logger.debug("Response uber-trace-id: %s", ex.response.headers["uber-trace-id"])
                except Exception:  # pylint: disable=broad-except
                    # the response did not contain the expected json.
                    message += f". {ex.response.text}"

            if self.auth_token:
                message = message.replace(self.auth_token, "...")

            raise RequestsApiError(message) from ex

        return response
