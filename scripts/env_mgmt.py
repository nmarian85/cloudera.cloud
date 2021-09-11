import click
import sys
import json
import os
from utils import show_progress, get_env_info, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops
import requests
from time import sleep


def dump_env_install_json(cdp_env_name, cdp_env_info, env_json_skel):
    cdp_env_json = dict(env_json_skel)
    del cdp_env_json["networkCidr"]
    del cdp_env_json["image"]

    cdp_env_json["environmentName"] = cdp_env_name
    cdp_env_json["credentialName"] = cdp_env_info["credentials"]["cross_account_all_perm"][
        "credential_name"
    ]
    cdp_env_json["region"] = "eu-central-1"
    cdp_env_json["subnetIds"] = cdp_env_info["subnets"]
    cdp_env_json["vpcId"] = cdp_env_info["vpc_id"]
    cdp_env_json["enableTunnel"] = True
    cdp_env_json["tags"] = cdp_env_info["tags"]
    cdp_env_json["securityAccess"] = {
        "securityGroupIdForKnox": cdp_env_info["sg"],
        "defaultSecurityGroupId": cdp_env_info["sg"],
    }
    cdp_env_json["logStorage"]["storageLocationBase"] = f'{cdp_env_info["log_bucket"]}'
    log_instance_profile = f'{cdp_env_info["log_role"]}-instance-profile'
    role_iam_arn = f'arn:aws:iam::{cdp_env_info["account_id"]}'
    cdp_env_json["logStorage"][
        "instanceProfile"
    ] = f"{role_iam_arn}:instance-profile/{log_instance_profile}"
    cdp_env_json["freeIpa"]["instanceCountByGroup"] = 1
    cdp_env_json["endpointAccessGatewayScheme"] = "PRIVATE"
    cdp_env_json["authentication"]["publicKey"] = cdp_env_info["public_key"]
    return cdp_env_json


def dump_env_delete_json(cdp_env_name, cdp_env_info, env_json_skel):
    cdp_env_json = dict(env_json_skel)
    cdp_env_json["environmentName"] = cdp_env_name
    return cdp_env_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["install-env", "delete-env"]), required=True)
@click.option(
    "--env",
    type=click.Choice(["lab", "test", "dev", "acc", "prod"]),
    help="ECB environment: lab, test, etc.",
    required=True,
)
@click.option(
    "--cdp-env-name",
    help="Please see the env.json for details regarding the CDP env",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        env_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"

    if action == "install-env":
        click.echo(f"==============Creating environment {cdp_env_name}==============")
        env_json = dump_env_install_json(cdp_env_name, cdp_env_info, env_json_skel)
        action_url = f"{env_url}/createAWSEnvironment"
    elif action == "delete-env":
        click.echo(f"==============Deleting environment {cdp_env_name}==============")
        env_json = dump_env_delete_json(cdp_env_name, cdp_env_info, env_json_skel)
        action_url = f"{env_url}/deleteEnvironment"

    dump_json_dict(env_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=env_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on environments {cdp_env_name}")

        poll_url = f"{env_url}/listEnvironments"

        if action == "install-env":
            elem_search_info = {
                "root_index": "environments",
                "expected_key_val": {"environmentName": cdp_env_name, "status": "AVAILABLE"},
                "present": True,
            }
        elif action == "delete-env":
            elem_search_info = {
                "root_index": "environments",
                "expected_key_val": {"environmentName": cdp_env_name},
                "present": False,
            }
        poll_for_status(poll_url=poll_url, elem_search_info=elem_search_info)

        click.echo(f"Action {action} on environment {cdp_env_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{cdp_env_name}.json", "w", encoding="utf-8") as f:
            json.dump(env_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


if __name__ == "__main__":
    main()
