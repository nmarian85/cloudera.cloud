"""
The purpose of this module is to provide an abstraction for interacting with
the REST API using the python requests module.
"""

import requests
import json
from os import getenv
from abc import ABC, abstractmethod
from time import strftime, gmtime, sleep, time
from functools import wraps

dryrun = True

if getenv("REQUESTS_CA_BUNDLE") is None:
    raise ValueError(
        """Please set the env variable REQUESTS_CA_BUNDLE \
to /etc/ssl/certs/ca-certificates.crt in your CDSW project. \
If working on Red Hat the location is \
/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt"""
    )

# how much to wait until timing out a HTTP request
DEFAULT_TIMEOUT = 120  # seconds


DEFAULT_REGION = "us-west-1"
DEFAULT_IAM_CRN = f"crn:altus:iam:{DEFAULT_REGION}:altus"
CDP_API_VERSION = "1"
CDP_IAM_ENDPOINT = f"https://iamapi.{DEFAULT_REGION}.altus.cloudera.com/iam"
CDP_SERVICES_ENDPOINT = (
    f"https://api.{DEFAULT_REGION}.cdp.cloudera.com/api/v{CDP_API_VERSION}"
)

# @lru_cache()
def send_http_request(
    srv_url, req_type="get", params=None, data=None, auth=None, headers=None
):
    """
    Wrapper for requests (HTTP POST, PUT, GET, DELETE) with some error checking
    """
    if req_type not in "post put get delete".split():
        raise ValueError("Unknown request type")

    try:
        res = getattr(requests, req_type)(
            url=srv_url,
            json=data,
            timeout=DEFAULT_TIMEOUT,
            auth=auth,
            params=params,
            headers=headers,
        )
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise
    except requests.exceptions.HTTPError:
        if res.text:
            print(res.text)
        # if res.status_code == 400:
        #         return res.text
        raise

    try:
        out = res.json()
    except json.decoder.JSONDecodeError:
        print("Response received is not in JSON format.")
        if "text" in res:
            print(res.text)
        raise
    else:
        res.data = out
        return res.data
