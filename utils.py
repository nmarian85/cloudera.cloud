from click import echo
import json


def show_progress(msg):
    sep = "=" * 10
    echo("\n" + sep + "> " + msg.upper() + " <" + sep)


def get_env_info(env, cdp_env_name):
    with open("skel.json") as json_file:
        env_json_skel = json.load(json_file)

    with open(f"{env}.json", "r") as read_file:
        envs = json.load(read_file)

    cdp_env_info = envs.get(cdp_env_name)
    if cdp_env_info is None:
        raise ValueError(f"Unable to find {cdp_env_name} in env.json")
    else:
        return cdp_env_info
