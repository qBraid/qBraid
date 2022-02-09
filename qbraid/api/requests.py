"""Module for making requests to the qbraid api"""

import os

import requests

s = requests.Session()

# authentication for testing
# comment out for production deploy
_email = os.getenv("JUPYTERHUB_USER")
_refresh = os.getenv("REFRESH")
s.headers.update({"email": _email, "refresh-token": _refresh})


def _api_url(route):
    # url = "http://localhost:3001/api"
    # url = "https://api-staging.qbraid.com/api"
    url = "https://api.qbraid.com/api"
    return url + route


def post(route, **kwargs):
    url = _api_url(route)
    res = s.post(url, verify=False, **kwargs)
    return res.json()


def put(route, kwargs):
    url = _api_url(route)
    res = s.put(url, verify=False, **kwargs)
    return res.json()
