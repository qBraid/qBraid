"""Module for making requests to the qbraid api"""

import logging
from email.mime import base
from typing import Any, Optional

from requests import RequestException, Response, Session

from .config_user import get_config
from .exceptions import RequestsApiError

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
        id_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> None:
        """QbraidSession constructor.

        Args:
            base_url: Base URL for the session's requests.
            user_email: JupyterHub User.
            id_token: Authenticated qBraid id-token.
            refresh_token: Authenticated qBraid refresh-token.

        """
        super().__init__()

        self.base_url = base_url
        self.user_email = user_email
        self.id_token = id_token
        self.refresh_token = refresh_token
        self.verify = False

    def __del__(self) -> None:
        """QbraidSession destructor. Closes the session."""
        self.close()

    def _get_config(self, field: str) -> Optional[str]:
        config = get_config(field, "default")
        if config == -1 or config in ["", "None", None]:
            return None
        return config

    @property
    def base_url(self) -> Optional[str]:
        """Return the qbraid api url."""
        return self._base_url

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        """Set the qbraid api url."""
        url = value if value else self._get_config("url")
        self._base_url = url if url else ""

    @property
    def user_email(self) -> Optional[str]:
        """Return the session user email."""
        return self._user_email

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set the session user email."""
        user_email = value if value else self._get_config("email")
        self._user_email = user_email
        if user_email:
            self.headers.update({"email": user_email})  # type: ignore[attr-defined]

    @property
    def id_token(self) -> Optional[str]:
        """Return the session id token."""
        return self._id_token

    @id_token.setter
    def id_token(self, value: Optional[str]) -> None:
        """Set the session id token."""
        id_token = value if value else self._get_config("id-token")
        self._id_token = id_token
        if id_token:
            self.headers.update({"id-token": id_token})  # type: ignore[attr-defined]

    @property
    def refresh_token(self) -> Optional[str]:
        """Return the session refresh token."""
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: Optional[str]) -> None:
        """Set the session refresh token."""
        refresh_token = value if value else self._get_config("refresh-token")
        self._refresh_token = refresh_token
        if refresh_token:
            self.headers.update({"refresh-token": refresh_token})  # type: ignore[attr-defined]

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

            if self.id_token:
                message = message.replace(self.id_token, "...")

            if self.refresh_token:
                message = message.replace(self.refresh_token, "...")

            raise RequestsApiError(message) from ex

        return response
