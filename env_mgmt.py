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
from utils import show_progress, get_env_info, sleep_wait
from cdpv1sign import generate_headers
import requests_ops
import requests

""" Dependencies
Python: pip3 install --upgrade --user click cdpcli
Env variables: 
    - REQUESTS_CA_BUNDLE=
        - /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt for RHEL/Amazon Linux
        - /etc/ssl/certs/ca-certificates.crt for Ubuntu/Alpine
    - CDP_ACCESS_KEY_ID
    - CDP_PRIVATE_KEY
"""


def dump_install_json(cdp_env_name, cdp_env_info, env_json_skel):
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


@sleep_wait
def poll_for_status(poll_url, action, expected_value):
    """Since the http request we send is async we will need to poll
    to check that the action we submitted in the http request was
    successful

    Args:
        poll_url ([type]): [url to check the status of our command (e.g. creating a credential)]
        action ([type]): []
        expected_value ([type]): [expected value in case of success]

    Returns:
        [type]: [description]
    """
    json_response = requests_ops.send_http_request(
        srv_url=poll_url, req_type="post", data={}, headers=generate_headers("POST", poll_url),
    )
    if action == "install-env":
        found = False
    elif action == "delete-env":
        found = True

    creds = json_response.get("environments")
    if isinstance(creds, list):
        for cred in creds:
            if cred["environmentName"] == expected_value:
                # if we want to create the credential and we found it,
                # the return value will be True since the creation was successful
                # if we wanted to delete the credential and we found it,
                # the return value will be False since it was not deleted yet
                return not found
    return found


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
        env_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"

    if action == "install-env":
        cdp_env_json = dump_install_json(cdp_env_name, cdp_env_info, env_json_skel)
        action_url = f"{env_url}/createAWSEnvironment"

    click.echo("-------------------Generated JSON-----------------------------")
    click.echo(json.dumps(cdp_env_json, indent=4, sort_keys=True))

    if not dryrun:
        # dumping to a file so that we have evidence which will be stored by the Gitlab pipeline
        with open(f"{cdp_env_name}.json", "w", encoding="utf-8") as f:
            json.dump(cdp_env_json, f, ensure_ascii=False, indent=4)

        env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/environments2"
        return requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdp_env_json,
            headers=generate_headers("POST", action_url),
        )

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
        click.echo(f"===========================================================")
        click.echo()


if __name__ == "__main__":
    main()

