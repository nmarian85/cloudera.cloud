import click
import sys
import json
import os
from utils import show_progress, get_env_info, sleep_wait
from cdpv1sign import generate_headers
import requests_ops


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
def poll_for_status(poll_url, expected_value):
    """[summary]

    Args:
        poll_url ([type]): [url to check the status of our command (e.g. creating a credential)]
        expected_value ([type]): [expected value in case of success]

    Returns:
        [type]: [description]
    """
    json_response = requests_ops.send_http_request(
        srv_url=poll_url, req_type="post", headers=generate_headers("POST", poll_url),
    )
    for cred in json_response.get("credentials"):
        if cred["credentialName"] == expected_value:
            return True
    return False


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
        click.echo("-------------------Generated JSON-----------------------------")
        if action == "create-cred":
            cdp_cred_json = dump_create_cred_json(cred_info, cred_json_skel)
            action_url = f"{env_url}/createAWSCredential"
        elif action == "delete-cred":
            cdp_cred_json = dump_delete_cred_json(cred_info, cred_json_skel)
            action_url = f"{env_url}/deleteCredential"

        click.echo(json.dumps(cdp_cred_json, indent=4, sort_keys=True))
        click.echo("--------------------------------------------------------------")

        if not dryrun:
            cred_name = cred_info["credential_name"]
            requests_ops.send_http_request(
                srv_url=action_url,
                req_type="post",
                data=cdp_cred_json,
                headers=generate_headers("POST", action_url),
            )
            click.echo(f"Waiting for {action} on credential {cred_name}")
            poll_for_status(
                poll_url=f"{env_url}/listCredentials", expected_value=cred_name,
            )
            # dumping file so that Gitlab will back it up
            with open(f"{cred_name}.json", "w", encoding="utf-8") as f:
                json.dump(cdp_cred_json, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
