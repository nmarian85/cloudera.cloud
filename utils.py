from click import echo
import json
from time import sleep, time
from functools import wraps
import requests
import requests_ops
from cdpv1sign import generate_headers


# polling interval when checking the status of a submitted command
DEFAULT_WAIT_PERIOD = 60  # seconds
DEFAULT_WAIT_PERIOD_INCREMENT = 120  # seconds
# how much to wait until timing out when checking
# for the success status of a submitted command to the management console
DEFAULT_TIMEOUT_COMMAND = 3600  # seconds


def show_progress(msg):
    sep = "=" * 10
    echo("\n" + sep + "> " + msg.upper() + " <" + sep)


def get_env_info(env, cdp_env_name):
    """[summary]

    Args:
        env ([type]): [description]
        cdp_env_name ([type]): [description]

    Raises:
        ValueError: [description]

    Returns:
        [type]: [description]
    """
    with open(f"{env}.json", "r") as read_file:
        envs = json.load(read_file)

    cdp_env_info = envs.get(cdp_env_name)
    if cdp_env_info is None:
        raise ValueError(f"Unable to find {cdp_env_name} in env.json")
    else:
        return cdp_env_info


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
            value_found = func(*args, **kwargs)
            if value_found:
                return
            else:
                sleep(new_period)
                # increasing the wait time
                new_period = new_period + DEFAULT_WAIT_PERIOD_INCREMENT
                echo(f"Checking again in {new_period}s")
        raise TimeoutError("Timeout reached while checking for expected value")

    return wrapper


@sleep_wait
def poll_for_status(poll_url, elem_search_info):
    """Since the http request we send is async we will need to poll
    to check that the action we submitted in the http request was
    successful

    Args:
        poll_url ([type]): [url to check the status of our command (e.g. creating a credential)]
        action ([type]): []
        found_state([type]): [whether we expect the expected value to be present or absent]
        expected_value_key ([type]): []
        expected_value ([type]): [expected value in case of success]

    Returns:
        [type]: [description]
    """
    json_response = requests_ops.send_http_request(
        srv_url=poll_url, req_type="post", data={}, headers=generate_headers("POST", poll_url),
    )

    # getting the list of elements from the response json
    response = json_response.get(elem_search_info["root_index"])

    # e.g. for listCredentials: the response is a list and
    # we are going to loop through all the credentials and check if they were created
    if isinstance(response, list):
        for elem in response:
            if elem[elem_search_info["search_elem_index"]] == elem_search_info["expected_value"]:
                # e.g. for credential mgmt:
                # if we want to create the credential and we found it,
                # the return value will be True since the creation was successful
                # if we wanted to delete the credential and we found it,
                # the return value will be False since it was not deleted yet
                return elem_search_info["present"]
    # e.g. for describeEnvironment: the response is a dict and
    # we will check for a specific status, e.g. environment has finished installing
    elif isinstance(response, dict):
        if elem[elem_search_info["search_elem_index"]] == elem_search_info["expected_value"]:
            return elem_search_info["present"]

    return not elem_search_info["present"]
