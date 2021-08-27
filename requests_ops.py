"""
The purpose of this module is to provide an abstraction for interacting with
the REST API using the python requests module.
"""

import requests
import json
from click import echo
from os import getenv
from abc import ABC, abstractmethod
from time import strftime, gmtime, sleep
from collections import namedtuple
from collections import abc

# from pprint import pprint
from functools import wraps

dry_run = True

if getenv("REQUESTS_CA_BUNDLE") is None:
    raise ValueError(
        """Please set the env variable REQUESTS_CA_BUNDLE \
to /etc/ssl/certs/ca-certificates.crt in your CDSW project. \
If working on Red Hat the location is \
/etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt"""
    )

DEFAULT_TIMEOUT = 120  # seconds


# @lru_cache()
def send_http_request(
    srv_url, req_type="get", params=None, data=None, auth=None, headers=None
):
    """
    Wrapper for requests (HTTP POST, PUT, GET, DELETE) with some error checking
    """
    if req_type not in "post put get delete".split():
        raise ValueError("Unknown request type")

    res = getattr(requests, req_type)(
        url=srv_url,
        json=data,
        timeout=DEFAULT_TIMEOUT,
        auth=auth,
        params=params,
        headers=headers,
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


def sleep_wait(timeout, retry=100):
    """
    Wait for the CM command finish during a predefined period.
    If the command did not finish during that period we will timeout
    and exit. Normally in a decorator we don't need 3 layers of
    functions but here we want to pass parameters to the
    decorator not to the function
    """

    def wait_for_cm_command(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < retry:
                try:
                    cmd_json = func(*args, **kwargs)
                except json.decoder.JSONDecodeError:
                    echo("Retrying request")
                else:
                    if isinstance(cmd_json, dict) and cmd_json.get("active") is False:
                        return cmd_json
                # we invalidate the lru cache if we did not get the expected result
                # func.cache_clear()
                echo(f"Waiting for CM command to finish, checking again in {timeout}s")
                sleep(timeout)
                retries += 1

            raise TimeoutError("Timeout reached while waiting for a JSON response")

        return wrapper

    return wait_for_cm_command


@sleep_wait(2)
def fetch_cm_cmd_info(cm_url, cmd_id):
    """
    Each HTTP request sent to CM is fulfilled via a CM job. We will
    priodically poll the result of the job to check its success
    """
    if not dry_run:
        return send_http_request(srv_url=f"{cm_url}/commands/{cmd_id}")


def check_cm_command_result(error_msg, status="success", value=True):
    """checks if a command sent to CM which has finished
    was succesful or not. Normally in a decorator we don't need 3 layers of
    functions but here we want to pass parameters to the
    decorator not to the function.
    """

    def check_exit_code(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not dry_run:
                cmd_json = func(*args, **kwargs)
                if cmd_json.get(status) == value:
                    return True
                else:
                    raise ValueError(f'{error_msg}: {cmd_json.get("resultMessage")}')
            else:
                func(*args, **kwargs)

        return wrapper

    return check_exit_code


class FrozenJSON:
    """Class for navigating a JSON-like object
       using attribute notation
    """

    """Build a dict from the mapping argument. This serves two purposes:
    ensures we got a dict (or something that can be converted to one)
    and makes a copy for safety."""

    def __init__(self, mapping):
        self.__data = dict(mapping)

    """__getattr__ is called only when there’s no attribute with that name."""

    def __getattr__(self, name):
        if hasattr(self.__data, name):
            """If name matches an attribute of the instance __data,
            return that. This is how calls to methods like keys are handled."""
            return getattr(self.__data, name)
        else:
            """Otherwise, fetch the item with the key name from self.__data,
            and return the result of calling FrozenJSON.build() on that."""
            return FrozenJSON.build(self.__data[name])

    """This is an alternate constructor"""

    @classmethod
    def build(cls, obj):
        """If obj is a mapping, build a FrozenJSON with it."""
        if isinstance(obj, abc.Mapping):
            return cls(obj)
        elif isinstance(obj, abc.MutableSequence):
            """If it is a MutableSequence, it must be a list,
            so we build a list by passing every item in obj recursively to .build()."""
            return [cls.build(item) for item in obj]
        else:
            """If it’s not a dict or a list, return the item as it is."""
            return obj

    def __repr__(self):
        return json.dumps(self.__data, indent=4, sort_keys=True)
