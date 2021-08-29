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

# from pprint import pprint
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

# how much to wait until timing out when checking
# for the success status of a submitted command to the management console
DEFAULT_TIMEOUT_COMMAND = 3600  # seconds


# polling interval when checking the status of a submitted command
DEFAULT_WAIT_PERIOD = 60  # seconds
DEFAULT_WAIT_PERIOD_INCREMENT = 120  # seconds

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

    # Check if the response HTTP status code is not a 4xx or a 5xx
    if not res.ok:
        if res.text:
            echo(res.text)
    res.raise_for_status()
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


def sleep_wait(func):
    """    HTTP requests are async hence we will priodically poll the
    result of the job to check its success

    Args:
        func ([type]): [description]

    Raises:
        TimeoutError: [description]

    Returns:
        [type]: [description]
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        mustend = time() + DEFAULT_TIMEOUT_COMMAND
        new_period = DEFAULT_WAIT_PERIOD

        while time() < mustend:
            current_status = func(*args, **kwargs)
            echo(f"Waiting for command to finish")
            if current_status == kwargs["expected_status"]:
                return
            else:
                sleep(new_period)
                # increasing the wait time
                new_period = new_period + DEFAULT_WAIT_PERIOD_INCREMENT
                echo(f"Checking again in {new_period}s")
        raise TimeoutError("Timeout reached while checking for status")

    return wrapper


# class FrozenJSON:
#     """Class for navigating a JSON-like object
#        using attribute notation
#     """

#     """Build a dict from the mapping argument. This serves two purposes:
#     ensures we got a dict (or something that can be converted to one)
#     and makes a copy for safety."""

#     def __init__(self, mapping):
#         self.__data = dict(mapping)

#     """__getattr__ is called only when there’s no attribute with that name."""

#     def __getattr__(self, name):
#         if hasattr(self.__data, name):
#             """If name matches an attribute of the instance __data,
#             return that. This is how calls to methods like keys are handled."""
#             return getattr(self.__data, name)
#         else:
#             """Otherwise, fetch the item with the key name from self.__data,
#             and return the result of calling FrozenJSON.build() on that."""
#             return FrozenJSON.build(self.__data[name])

#     """This is an alternate constructor"""

#     @classmethod
#     def build(cls, obj):
#         """If obj is a mapping, build a FrozenJSON with it."""
#         if isinstance(obj, abc.Mapping):
#             return cls(obj)
#         elif isinstance(obj, abc.MutableSequence):
#             """If it is a MutableSequence, it must be a list,
#             so we build a list by passing every item in obj recursively to .build()."""
#             return [cls.build(item) for item in obj]
#         else:
#             """If it’s not a dict or a list, return the item as it is."""
#             return obj

#     def __repr__(self):
#         return json.dumps(self.__data, indent=4, sort_keys=True)
