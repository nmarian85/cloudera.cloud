import click
import sys
import json
import os
from utils import show_progress, get_env_info, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops
import requests


def dump_create_cred_json(cred_info, json_skel):
    """[summary]

    Args:
        cred_info ([type]): [description]
        json_skel ([type]): [description]

    Returns:
        [type]: [description]
    """
    cred_json = dict(json_skel)
    cred_json["credentialName"] = cred_info["credential_name"]
    cred_json["roleArn"] = cred_info["role_arn"]
    cred_json["description"] = cred_info["description"]
    return cred_json


def dump_delete_cred_json(cred_info, json_skel):
    """[summary]

    Args:
        cred_info ([type]): [description]
        json_skel ([type]): [description]

    Returns:
        [type]: [description]
    """
    cred_json = dict(json_skel)
    cred_json["credentialName"] = cred_info["credential_name"]
    return cred_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["create-cred", "delete-cred"]), required=True)
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
    "--cred-name", help="Please see the env.json for details regarding the CDP env", required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, action, cred_name, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        cred_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"

    cred_info = None
    for cred, cred_details in cdp_env_info["credentials"].items():
        if cred_details["credential_name"] == cred_name:
            cred_info = cred_details
    if cred_info is None:
        raise ValueError(f"Unable to find credential with name {cred_name}")

    if action == "create-cred":
        click.echo(f"==============Creating credential {cred_name}==============")
        cdp_cred_json = dump_create_cred_json(cred_info, cred_json_skel)
        action_url = f"{env_url}/createAWSCredential"
    elif action == "delete-cred":
        click.echo(f"==============Deleting credential {cred_name}==============")
        cdp_cred_json = dump_delete_cred_json(cred_info, cred_json_skel)
        action_url = f"{env_url}/deleteCredential"

    dump_json_dict(cdp_cred_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_cred_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on credential {cred_name}")
        if action == "create-cred":
            elem_present = True
        elif action == "delete-cred":
            elem_present = False

        elem_search_info = {
            "root_index": "credentials",
            "expected_key_val": {"credentialName": cred_name},
            "present": elem_present,
        }

        poll_for_status(poll_url=f"{env_url}/listCredentials", elem_search_info=elem_search_info)
        click.echo(f"Action {action} on credential {cred_name} DONE")
        # dumping file so that Gitlab will back it up
        with open(f"{cred_name}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_cred_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


if __name__ == "__main__":
    main()
