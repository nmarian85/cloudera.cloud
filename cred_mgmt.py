import click
import sys
import json
import os
from utils import show_progress, get_env_info
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


# @requests_ops.check_cm_command_result(error_msg=f"Unable to take action on credential")
def run_command(action_url, check_url, cdp_cred_json):
    json_reponse = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        data=cdp_cred_json,
        headers=generate_headers("POST", action_url),
    )
    # print(json_reponse["credentialName"])
    # return requests_ops.fetch_cm_cmd_info(action_url, "{env_url}/deleteCredential"

    #         return fetch_cm_cmd_info(self.cm_url, json_response.get("id"))
    if "credential" in json_reponse:
        click.echo(json_reponse["credential"]["credentialName"])
    else:
        print(json_response)


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

        if not dryrun:
            with open(f'{cred_info["credential_name"]}_cred.json', "w", encoding="utf-8") as f:
                json.dump(cdp_cred_json, f, ensure_ascii=False, indent=4)
            check_url = f"{env_url}/listCredentials"
            run_command(action_url, check_url, cdp_cred_json)


if __name__ == "__main__":
    main()
