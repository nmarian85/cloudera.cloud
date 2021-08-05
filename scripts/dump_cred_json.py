import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CDP credentials")

# Add the arguments
# my_parser.add_argument(
#     "--action", choices=["provision", "delete"], help="provision or delete CML cluster",
# )
my_parser.add_argument("-e", "--env", help="Environment (lab, dev, etc.)")
my_parser.add_argument("-c", "--cdp-env-name", help="CDP env name")

args = my_parser.parse_args()

cdp_env_name = args.cdp_env_name
env = args.env

with open(f"{env}.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(cdp_env_name) is None:
    raise ValueError(f"Unable to find {cdp_env_name} in env.json")

with open("skel.json") as json_file:
    cred_json_skel = json.load(json_file)

credentials = envs.get(cdp_env_name).get("credentials")

for cred, cred_info in credentials.items():
    cred_json = dict(cred_json_skel)
    cred_json["credentialName"] = cred_info["credential_name"]
    cred_json["roleArn"] = cred_info["role_arn"]
    cred_json["description"] = cred_info["description"]
    with open(f'{cred_info["credential_name"]}_cred.json', "w", encoding="utf-8") as f:
        json.dump(cred_json, f, ensure_ascii=False, indent=4)
