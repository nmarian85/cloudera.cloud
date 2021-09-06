from click import echo
import json
from time import sleep, time
from functools import wraps
import requests
import requests_ops
from cdpv1sign import generate_headers


# polling interval when checking the status of a submitted command
DEFAULT_WAIT_PERIOD = 60  # seconds
DEFAULT_WAIT_PERIOD_INCREMENT = 60  # seconds
# how much to wait until timing out when checking
# for the success status of a submitted command to the management console
DEFAULT_TIMEOUT_COMMAND = 7200  # seconds
# CDP_TENANT_ID = "0e62c9c8-e9cd-483b-81b3-651fe7a22deb"


def show_progress(msg):
    sep = "=" * 10
    echo("\n" + sep + "> " + msg.upper() + " <" + sep)


def get_cdp_env_crn(cdp_env_name):
    action_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2/describeEnvironment"
    response = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        data={"environmentName": cdp_env_name},
        headers=generate_headers("POST", action_url),
    )
    return response["environment"]["crn"]


def get_user_attr(user_name, attr, next_token=""):
    action_url = f"{requests_ops.CDP_IAM_ENDPOINT}/listUsers"
    response = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        headers=generate_headers("POST", action_url),
        data={"startingToken": next_token},
    )
    for user_info in response["users"]:
        if user_info["workloadUsername"] == user_name:
            return user_info[attr]
    if "nextToken" in response:
        return get_user_attr(user_name, attr, response["nextToken"])


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
                echo(f"Checking again in {new_period}s")
                sleep(new_period)
                # increasing the wait time
                # new_period = new_period + DEFAULT_WAIT_PERIOD_INCREMENT
        raise TimeoutError("Timeout reached while checking for expected value")

    return wrapper


@sleep_wait
def poll_for_status(poll_url, elem_search_info, data={}):
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
        srv_url=poll_url, req_type="post", data=data, headers=generate_headers("POST", poll_url),
    )

    root_index = elem_search_info["root_index"]
    if isinstance(json_response, dict):
        if len(root_index) > 0:
            response = json_response[root_index]
        else:
            response = json_response
        # e.g. for listCredentials: the response is a list and
        # we are going to loop through all the credentials and check if they were created
        if isinstance(response, list):
            # finding the element we were looking for has different meanings
            # based on the action that we submitted: if the action was create then
            # we are done and we can stop polling; if the action was delete and the element
            # is still there, then we need to wait more. This is why we need the
            # elem_search_info["present"]
            for dict_elem in response:
                found = True
                for expected_k, expected_v in elem_search_info["expected_key_val"].items():
                    if dict_elem[expected_k] != expected_v:
                        found = False
                if found:
                    return elem_search_info["present"]
            return not elem_search_info["present"]
        elif isinstance(response, dict):
            found = True
            for expected_k, expected_v in elem_search_info["expected_key_val"].items():
                if response[expected_k] != expected_v:
                    found = False
            if found:
                return elem_search_info["present"]
        else:
            raise ValueError(f"Response {response} is not a dict or list")
