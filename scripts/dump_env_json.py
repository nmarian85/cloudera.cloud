import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CML cluster")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["install", "delete"], help="install or delete CDP environment",
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
cdp_env_json = dict(env_json_skel)

del cdp_env_json["networkCidr"]
del cdp_env_json["image"]

cdp_env_json["environmentName"] = cdp_env_name
cdp_env_json["credentialName"] = cdp_env_info["credentials"]["cross_account_all_perm"]["credential_name"]
cdp_env_json["region"] = "eu-central-1"
cdp_env_json["subnetIds"] = cdp_env_info["subnets"]
cdp_env_json["vpcId"] = cdp_env_info["vpc_id"]
cdp_env_json["enableTunnel"] = True
cdp_env_json["tags"] = cdp_env_info["tags"]
cdp_env_json["securityAccess"] = {
    "securityGroupIdForKnox": cdp_env_info["sg"],
    "defaultSecurityGroupId": cdp_env_info["sg"]
}
cdp_env_json["logStorage"]["storageLocationBase"] = f'{cdp_env_info["log_bucket"]}'
log_instance_profile = f'{cdp_env_info["log_role"]}-instance-profile'
role_iam_arn = f'arn:aws:iam::{cdp_env_info["account_id"]}'
cdp_env_json["logStorage"]["instanceProfile"] = (
    f'{role_iam_arn}:instance-profile/{log_instance_profile}')
cdp_env_json["freeIpa"]["instanceCountByGroup"] = 1
cdp_env_json["endpointAccessGatewayScheme"] = "PRIVATE"
cdp_env_json["authentication"]["publicKey"] = cdp_env_info["public_key"]

with open(f'{cdp_env_name}.json', "w", encoding="utf-8") as f:
    json.dump(cdp_env_json, f, ensure_ascii=False, indent=4)
