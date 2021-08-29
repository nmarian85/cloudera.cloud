import click
import sys
import json
import os
from utils import show_progress, get_env_info, sleep_wait
from cdpv1sign import generate_headers
import requests_ops
import requests


def dump_create_cred_json(cred_info, json_skel):
    cred_json = dict(json_skel)
    cred_json["credentialName"] = cred_info["credential_name"]
    cred_json["roleArn"] = cred_info["role_arn"]
    cred_json["description"] = cred_info["description"]
    return cred_json


def dump_delete_cred_json(cred_info, json_skel):
    cred_json = dict(json_skel)
    cred_json["credentialName"] = cred_info["credential_name"]
    return cred_json


@sleep_wait
def poll_for_status(poll_url, action, expected_value):
    """[summary]

    Args:
        poll_url ([type]): [url to check the status of our command (e.g. creating a credential)]
        expected_value ([type]): [expected value in case of success]

    Returns:
        [type]: [description]
    """
    json_response = requests_ops.send_http_request(
        srv_url=poll_url, req_type="post", data={}, headers=generate_headers("POST", poll_url),
    )
    if action == "create-cred":
        found = False
    elif action == "delete-cred":
        found = True

    creds = json_response.get("credentials")
    if isinstance(creds, list):
        for cred in creds:
            if cred["credentialName"] == expected_value:
                # if we want to create the credential and we found it,
                # the return value will be True since the creation was successful
                # if we wanted to delete the credential and we found it,
                # the return value will be False since it was not deleted yet
                return not found
    return found


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
    help="Please see {env}.json file where you defined the CDP env name",
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
        cred_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"

    credentials = cdp_env_info["credentials"]
    for cred, cred_info in credentials.items():
        cred_name = cred_info["credential_name"]

        if action == "create-cred":
            click.echo(f"==============Creating credential {cred_name}==============")
            cdp_cred_json = dump_create_cred_json(cred_info, cred_json_skel)
            action_url = f"{env_url}/createAWSCredential"
        elif action == "delete-cred":
            click.echo(f"==============Deleting credential {cred_name}==============")
            cdp_cred_json = dump_delete_cred_json(cred_info, cred_json_skel)
            action_url = f"{env_url}/deleteCredential"

        click.echo("-------------------Generated JSON-----------------------------")
        click.echo(json.dumps(cdp_cred_json, indent=4, sort_keys=True))
        click.echo("--------------------------------------------------------------")

        if not dryrun:
            try:
                response = requests_ops.send_http_request(
                    srv_url=action_url,
                    req_type="post",
                    data=cdp_cred_json,
                    headers=generate_headers("POST", action_url),
                )
            except requests.exceptions.HTTPError:
                if action == "create-cred":
                    check_str = "Credential already exists"
                # we want to ensure an idempotent execution hence
                # we will not raise errors if the credentials already exist
                # or where already deleted
                if check_str not in json.dumps(response, indent=4, sort_keys=True):
                    raise
            else:
                click.echo(f"Waiting for {action} on credential {cred_name}")
                poll_for_status(
                    poll_url=f"{env_url}/listCredentials", action=action, expected_value=cred_name,
                )
                # dumping file so that Gitlab will back it up
                with open(f"{cred_name}.json", "w", encoding="utf-8") as f:
                    json.dump(cdp_cred_json, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
