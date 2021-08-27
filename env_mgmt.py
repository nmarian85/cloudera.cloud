# 1. Create credential for the environment
# 2. Create environment
# 3. Create data lake
# 4. Add user CDP idbroker mappings
# 5. Create CML/CDE/CDW
# 6. Add user CDP idbroker mappings

import click
import sys
import json
import os
from utils import show_progress

def dump_install_json(cdp_env_name, cdp_env_info, env_json_skel):
    cdp_env_json = dict(env_json_skel)
    del cdp_env_json["networkCidr"]
    del cdp_env_json["image"]

    cdp_env_json["environmentName"] = cdp_env_name
    credentials = cdp_env_info["credentials"]
    cdp_env_json["credentialName"] = credentials["cross_account_all_perm"]["credential_name"]
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
    return cdp_env_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(['install-env', 'delete-env']), required=True)
@click.option("--env", help="ECB environment: lab, test, etc.", required=True)
@click.option("--cdp-env-name", help="Please see {env}.json file where you defined the CDP env name", required=True)
def main(
    dryrun,
    env,
    cdp_env_name,
    action
):
    if dryrun:
        show_progress("This is a dryrun")

    with open("skel.json") as json_file:
        env_json_skel = json.load(json_file)

    with open(f"{env}.json", "r") as read_file:
        envs = json.load(read_file)

    if envs.get(cdp_env_name) is None:
        raise ValueError(f"Unable to find {cdp_env_name} in env.json")

    cdp_env_info = envs.get(cdp_env_name)
    if action == "install-env":
        cdp_env_json = dump_install_json(cdp_env_name, cdp_env_info, env_json_skel)

    click.echo("Generated JSON")
    click.echo(json.dumps(cdp_env_json, indent=4, sort_keys=True))

    with open(f'{cdp_env_name}.json', "w", encoding="utf-8") as f:
        json.dump(cdp_env_json, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    main()
