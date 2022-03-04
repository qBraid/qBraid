"""Module for making requests to the qbraid api"""

import logging
from typing import Any, Dict, Optional

from requests import RequestException, Response, Session

from qbraid.api.config_prompts import qbraidrc_path
from qbraid.api.config_user import get_config
from qbraid.api.exceptions import AuthError, RequestsApiError

logger = logging.getLogger(__name__)

# API_URL = "http://localhost:3001/api"
# API_URL = "https://api-staging.qbraid.com/api"
# API_URL = "https://api.qbraid.com/api"
API_URL = "https://api-staging-1.qbraid.com/api"


class QbraidSession(Session):
    """Custom session with handling of request urls and authentication.

    This is a child class of ``requests.Session``. It handles qbraid
    authentication with custom headers, has SSL verification disabled
    for compatibility with lab, and returns all responses as jsons for
    convenience in the sdk.

    """

    def __init__(
        self,
        base_url: str = API_URL,
        user_email: Optional[str] = None,
        auth_token: Optional[str] = None,
        verify: bool = False,
    ) -> None:
        """QbraidSession constructor.

        Args:
            base_url: Base URL for the session's requests.
            user_email: JupyterHub User.
            auth_token: qBraid authentication token.
            verify: Whether to enable SSL verification.

        """
        super().__init__()

        self.base_url = base_url
        self.user_email = user_email
        self.auth_token = auth_token
        self.verify = verify

    def _qbraidrc(self, field: str) -> Optional[str]:
        config = get_config(field, "sdk", filepath=qbraidrc_path)
        if config == -1:
            return None
        return config

    @property
    def user_email(self) -> Optional[str]:
        """Return the session user email."""
        return self._user_email

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set the session user email."""
        user = value or self._qbraidrc("user")
        if user:
            self._user_email = user
            self.headers.update({"email": user})  # type: ignore[attr-defined]
        else:
            raise AuthError("qBraid user email invalid or not found")

    @property
    def auth_token(self) -> Optional[str]:
        """Return the session refresh token."""
        return self._auth_token

    @auth_token.setter
    def auth_token(self, value: Optional[str]) -> None:
        """Set the session refresh token."""
        token = value or self._qbraidrc("token")
        if token:
            self._auth_token = token
            self.headers.update({"refresh-token": token})  # type: ignore[attr-defined]
        else:
            raise AuthError("qBraid authentication token invalid or not found")

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

    def __getstate__(self) -> Dict:
        """Overwrite Session's getstate to include all attributes."""
        state = super().__getstate__()  # type: ignore
        state.update(self.__dict__)
        return state
