import sys
import json
import os
import argparse

env = os.getenv("ENV")
cdp_env_name = os.getenv("CDP_ENV_NAME")

with open(f"{env}.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(cdp_env_name) is None:
    raise ValueError(f"Unable to find {cdp_env_name} in env.json")

with open("skel.json") as json_file:
    env_json_skel = json.load(json_file)

cdp_env_info = envs.get(cdp_env_name)

if cdp_env_info is None:
    raise ValueError(f"Unable to find {cdp_env_name} in env.json")