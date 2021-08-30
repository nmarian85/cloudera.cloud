"""
The purpose of this module is to provide an abstraction for interacting with
the REST API using the python requests module.
"""

import requests
import json
from click import echo
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

CDP_API_VERSION = "1"
CDP_IAM_ENDPOINT = "iamapi.us-west-1.altus.cloudera.com"
CDP_SERVICES_ENDPOINT = f"https://api.us-west-1.cdp.cloudera.com/api/v{CDP_API_VERSION}"

# @lru_cache()
def send_http_request(srv_url, req_type="get", params=None, data=None, auth=None, headers=None):
    """
    Wrapper for requests (HTTP POST, PUT, GET, DELETE) with some error checking
    """
    if req_type not in "post put get delete".split():
        raise ValueError("Unknown request type")
    res = getattr(requests, req_type)(
        url=srv_url, json=data, timeout=DEFAULT_TIMEOUT, auth=auth, params=params, headers=headers,
    )
    res.raise_for_status()

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
        if res.status_code == 400:
            if res.text:
                return res.text
        raise

    try:
        out = res.json()
    except json.decoder.JSONDecodeError:
        echo("Response received is not in JSON format.")
        if "text" in res:
            echo(res.text)
        raise
    else:
        res.data = out
        return res.data
