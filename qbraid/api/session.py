"""Module for making requests to the qbraid api"""

import logging
from typing import Any, Optional

from requests import RequestException, Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config_user import get_config
from .exceptions import RequestsApiError

STATUS_FORCELIST = (
    500,  # General server error
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
    520,  # Cloudflare general error
    522,  # Cloudflare connection timeout
    524,  # Cloudflare Timeout
)

logger = logging.getLogger(__name__)


def _get_config(field: str) -> Optional[str]:
    config = get_config(field, "default")
    if config == -1 or config in ["", "None"]:
        return None
    return config


class PostForcelistRetry(Retry):
    """Custom :py:class:`urllib3.Retry` class that performs retry on ``POST`` errors in the
    force list. Retrying of ``POST`` requests are allowed *only* when the status code returned
    is on the :py:const:`~qbraid.api.session.STATUS_FORCELIST`. While ``POST`` requests are
    recommended not to be retried due to not being idempotent, retrying on specific 5xx errors
    through the qBraid API is safe.
    """

    def increment(  # type: ignore[no-untyped-def]
        self,
        method=None,
        url=None,
        response=None,
        error=None,
        _pool=None,
        _stacktrace=None,
    ):
        """Overwrites parent class increment method for logging."""
        if logger.getEffectiveLevel() is logging.DEBUG:
            status = data = headers = None
            if response:
                status = response.status
                data = response.data
                headers = response.headers
            logger.debug(
                "Retrying method=%s, url=%s, status=%s, error=%s, data=%s, headers=%s",
                method,
                url,
                status,
                error,
                data,
                headers,
            )
        return super().increment(
            method=method,
            url=url,
            response=response,
            error=error,
            _pool=_pool,
            _stacktrace=_stacktrace,
        )

    def is_retry(self, method: str, status_code: int, has_retry_after: bool = False) -> bool:
        """Indicate whether the request should be retried.

        Args:
            method: Request method.
            status_code: Status code.
            has_retry_after: Whether retry has been done before.

        Returns:
            ``True`` if the request should be retried, ``False`` otherwise.
        """
        if method.upper() == "POST" and status_code in self.status_forcelist:
            return True

        return super().is_retry(method, status_code, has_retry_after)


class QbraidSession(Session):
    """Custom session with handling of request urls and authentication.

    This is a child class of :py:class:`requests.Session`. It handles qbraid
    authentication with custom headers, has SSL verification disabled
    for compatibility with lab, and returns all responses as jsons for
    convenience in the sdk.

    Args:
        base_url: Base URL for the session's requests.
        user_email: JupyterHub User.
        id_token: Authenticated qBraid id-token.
        refresh_token: Authenticated qBraid refresh-token.
        retries_total: Number of total retries for the requests.
        retries_connect: Number of connect retries for the requests.
        backoff_factor: Backoff factor between retry attempts.

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        base_url: Optional[str] = None,
        user_email: Optional[str] = None,
        id_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        retries_total: int = 5,
        retries_connect: int = 3,
        backoff_factor: float = 0.5,
    ) -> None:

        super().__init__()

        self.base_url = base_url
        self.user_email = user_email
        self.id_token = id_token
        self.refresh_token = refresh_token
        self.verify = False

        self._initialize_retry(retries_total, retries_connect, backoff_factor)

    def __del__(self) -> None:
        """qbraid session destructor. Closes the session."""
        self.close()

    @property
    def base_url(self) -> Optional[str]:
        """Return the qbraid api url."""
        return self._base_url

    @base_url.setter
    def base_url(self, value: Optional[str]) -> None:
        """Set the qbraid api url."""
        url = value if value else _get_config("url")
        self._base_url = url if url else ""

    @property
    def user_email(self) -> Optional[str]:
        """Return the session user email."""
        return self._user_email

    @user_email.setter
    def user_email(self, value: Optional[str]) -> None:
        """Set the session user email."""
        user_email = value if value else _get_config("email")
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
        id_token = value if value else _get_config("id-token")
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
        refresh_token = value if value else _get_config("refresh-token")
        self._refresh_token = refresh_token
        if refresh_token:
            self.headers.update({"refresh-token": refresh_token})  # type: ignore[attr-defined]

    def _initialize_retry(
        self, retries_total: int, retries_connect: int, backoff_factor: float
    ) -> None:
        """Set the session retry policy.
        Args:
            retries_total: Number of total retries for the requests.
            retries_connect: Number of connect retries for the requests.
            backoff_factor: Backoff factor between retry attempts.
        """
        retry = PostForcelistRetry(
            total=retries_total,
            connect=retries_connect,
            backoff_factor=backoff_factor,
            status_forcelist=STATUS_FORCELIST,
        )

        retry_adapter = HTTPAdapter(max_retries=retry)
        self.mount("http://", retry_adapter)
        self.mount("https://", retry_adapter)

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
                    msg = error_json["message"]
                    code = error_json["code"]
                    message += f". {msg}, Error code: {code}."
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
