"""Module for emitting and disabling warnings"""
import warnings

import urllib3

from ._version import __version__
from .api.session import QbraidSession


def _check_version():

    session = QbraidSession()
    version_api = session.get("/public/lab/get-sdk-version", params={}).json()

    if version_api != __version__:
        warnings.warn(
            f"You are using qbraid version {__version__}; however, version {version_api} is available. "
            f"To avoid compatibility issues, consider upgrading by uninstalling and reinstalling the qBraid-SDK environment.",
            UserWarning,
        )


warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=UserWarning, message="Setuptools is replacing distutils")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_check_version()
