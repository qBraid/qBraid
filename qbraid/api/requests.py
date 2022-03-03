"""Module for making requests to the qbraid api"""

from requests import Session
from requests.exceptions import InvalidHeader

from qbraid.api.config_prompts import qbraidrc_path
from qbraid.api.config_user import get_config

s = Session()

# authentication for testing
# comment out for production deploy
_email = get_config("user", "sdk", filepath=qbraidrc_path)
_refresh = get_config("token", "sdk", filepath=qbraidrc_path)
s.headers.update({"email": _email, "refresh-token": _refresh})


def _api_url(route):
    # url = "http://localhost:3001/api"
    # url = "https://api-staging.qbraid.com/api"
    # url = "https://api.qbraid.com/api"
    url = "https://api-staging-1.qbraid.com/api"
    return url + route


def get(route, **kwargs):
    url = _api_url(route)
    res = s.get(url, verify=False, **kwargs)
    return res.json()


def put(route, **kwargs):
    url = _api_url(route)
    res = s.put(url, verify=False, **kwargs)
    return res.json()


def post(route, **kwargs):
    url = _api_url(route)
    res = s.post(url, verify=False, **kwargs)
    return res.json()
