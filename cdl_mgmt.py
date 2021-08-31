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
from utils import show_progress, get_env_info, poll_for_status
from cdpv1sign import generate_headers
import requests_ops
import requests
from time import sleep

""" Dependencies
Python: pip3 install --upgrade --user click cdpcli
Env variables: 
    - REQUESTS_CA_BUNDLE=
        - /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt for RHEL/Amazon Linux
        - /etc/ssl/certs/ca-certificates.crt for Ubuntu/Alpine
    - CDP_ACCESS_KEY_ID
    - CDP_PRIVATE_KEY
"""


def dump_cdl_install_json(cdp_env_name, cdl_cluster_name, cdp_dl_info, account_id, cdl_json_skel):
    cdp_dl_json = dict(cdl_json_skel)

    del cdp_dl_json["runtime"]
    del cdp_dl_json["image"]

    cdp_dl_json["environmentName"] = cdp_env_name
    cdp_dl_json["tags"] = cdp_dl_info["tags"]
    cdp_dl_json["scale"] = cdp_dl_info["scale"]

    cdl_cluster_name = cdp_dl_info["name"]
    cdp_dl_json["datalakeName"] = cdl_cluster_name

    cdp_dl_json["cloudProviderConfiguration"][
        "storageBucketLocation"
    ] = f's3a://{cdp_dl_info["data_bucket"]}/{cdp_env_name}'
    role_iam_arn = f"arn:aws:iam::{account_id}"
    cdp_dl_json["cloudProviderConfiguration"][
        "instanceProfile"
    ] = f'{role_iam_arn}:instance-profile/{cdp_dl_info["idbroker_role_instance_profile"]}'

    return cdp_dl_json


def dump_cdl_delete_json(cdl_cluster_name, cdl_json_skel):
    cdp_dl_json = dict(cdl_json_skel)
    cdp_dl_json["datalakeName"] = cdl_cluster_name
    return cdp_dl_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["install-cdl", "delete-cdl"]), required=True)
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
    "--cdl-cluster-name",
    help="Please see {env}.json file where you defined the CDE cluster name",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, cdl_cluster_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        cdl_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)
    cdp_dl_info = cdp_env_info["datalake"]

    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/datalake"

    if action == "install-cdl":
        click.echo(f"==============Creating environment {cdp_env_name}==============")
        env_json = dump_cdl_install_json(
            cdp_env_name, cdl_cluster_name, cdp_dl_info, cdp_env_info["account_id"], cdl_json_skel
        )
        action_url = f"{env_url}/createAWSDatalake"
    elif action == "delete-cdl":
        click.echo(f"==============Deleting environment {cdp_env_name}==============")
        env_json = dump_cdl_delete_json(cdl_cluster_name, cdl_json_skel)
        action_url = f"{env_url}/deleteDatalake"

    click.echo("-------------------Generated JSON-----------------------------")
    print(json.dumps(env_json, indent=4, sort_keys=True))
    click.echo("--------------------------------------------------------------")

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=env_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on cluster {cdl_cluster_name}")

        poll_url = f"{env_url}/listDatalakes"

        if action == "install-cdl":
            elem_search_info = {
                "root_index": "datalakes",
                "expected_key_val": {"datalakeName": cdl_cluster_name, "status": "RUNNING"},
                "present": True,
            }
        elif action == "delete-cdl":
            elem_search_info = {
                "root_index": "datalakes",
                "expected_key_val": {"datalakeName": cdl_cluster_name},
                "present": False,
            }
        poll_for_status(poll_url=poll_url, elem_search_info=elem_search_info)

        click.echo(f"Action {action} on cluster {cdl_cluster_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{cdl_cluster_name}.json", "w", encoding="utf-8") as f:
            json.dump(env_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()

    # TODO: add code to add jumpserver role access to EKS control plane


if __name__ == "__main__":
    main()
