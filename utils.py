from click import echo
import json
from time import sleep, time
from functools import wraps

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
            echo(f"Waiting for command to finish")
            if value_found:
                return
            else:
                sleep(new_period)
                # increasing the wait time
                new_period = new_period + DEFAULT_WAIT_PERIOD_INCREMENT
                echo(f"Checking again in {new_period}s")
        raise TimeoutError("Timeout reached while checking for expected value")

    return wrapper
