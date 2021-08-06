import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CML cluster")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["install", "delete"], help="install or delete CDP data lake",
)
my_parser.add_argument("-e", "--env", help="CDP env name")
my_parser.add_argument("-c", "--cdp-env-name", help="CDP env name")

args = my_parser.parse_args()

cdp_env_name = args.cdp_env_name
env = args.env

with open(f"{env}.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(cdp_env_name) is None:
    raise ValueError(f"Unable to find {cdp_env_name} in env.json")

with open("skel.json") as json_file:
    env_json_skel = json.load(json_file)

cdp_env_info = envs.get(cdp_env_name)
cdp_dl_info = cdp_env_info.get("datalake")
cdp_dl_json = dict(env_json_skel)

del cdp_dl_json["runtime"]
del cdp_dl_json["image"]
del cdp_dl_json["scale"]

cdp_dl_json["environmentName"] = cdp_env_name
cdp_dl_json["tags"] = cdp_dl_info["tags"]
cdp_dl_json["scale"] = cdp_dl_info["scale"]

dlake_name = cdp_dl_info["name"]
cdp_dl_json["datalakeName"] = dlake_name


cdp_dl_json["cloudProviderConfiguration"]["storageBucketLocation"] = (
    f's3a://{cdp_dl_info["data_bucket"]}/{cdp_env_name}'
)
data_instance_profile = f'{cdp_dl_info["data_role"]}-instance-profile'
role_iam_arn = f'arn:aws:iam::{cdp_env_info["account_id"]}'
cdp_dl_json["cloudProviderConfiguration"]["instanceProfile"] = (
    f'{role_iam_arn}:instance-profile/{data_instance_profile}'
)

with open(f'{dlake_name}.json', "w", encoding="utf-8") as f:
    json.dump(cdp_dl_json, f, ensure_ascii=False, indent=4)

print(
    f'''{dlake_name},'''
    f'''{role_iam_arn}:role/{cdp_dl_json["ranger_role"]},'''
    f'''{role_iam_arn}:role/{cdp_dl_json["data_role"]}')'''
)
