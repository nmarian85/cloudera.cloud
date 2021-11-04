import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from env_mgmt import get_env_info
from cdpv1sign import generate_headers
import requests_ops


def dump_install_json(
    cdp_env_name, cdl_cluster_name, cdl_cluster_info, account_id, json_skel
):
    cdp_dl_json = dict(json_skel)

    del cdp_dl_json["runtime"]
    del cdp_dl_json["image"]

    cdp_dl_json["environmentName"] = cdp_env_name
    cdp_dl_json["tags"] = cdl_cluster_info["tags"]
    cdp_dl_json["scale"] = cdl_cluster_info["scale"]

    cdl_cluster_name = cdl_cluster_info["name"]
    cdp_dl_json["datalakeName"] = cdl_cluster_name

    cdp_dl_json["cloudProviderConfiguration"][
        "storageBucketLocation"
    ] = f's3a://{cdl_cluster_info["data_bucket"]}'
    role_iam_arn = f"arn:aws:iam::{account_id}"
    cdp_dl_json["cloudProviderConfiguration"][
        "instanceProfile"
    ] = f'{role_iam_arn}:instance-profile/{cdl_cluster_info["idbroker_role_instance_profile"]}'

    return cdp_dl_json


def dump_delete_json(cdl_cluster_name, json_skel):
    cdp_dl_json = dict(json_skel)
    cdp_dl_json["datalakeName"] = cdl_cluster_name
    return cdp_dl_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option(
    "--action", type=click.Choice(["install-cdl", "delete-cdl"]), required=True
)
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
        json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)

    with open(f"conf/{env}/{cdp_env_name}/cdl.json") as json_file:
        cdl_cluster_info = json.load(json_file)

    cdl_cluster_name = cdl_cluster_info["name"]
    cdl_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/datalake"

    if action == "install-cdl":
        click.echo(f"===Creating environment {cdp_env_name}===")
        cdl_json = dump_install_json(
            cdp_env_name,
            cdl_cluster_name,
            cdl_cluster_info,
            cdp_env_info["account_id"],
            json_skel,
        )
        action_url = f"{cdl_url}/createAWSDatalake"
    elif action == "delete-cdl":
        click.echo(f"===Deleting environment {cdp_env_name}===")
        cdl_json = dump_delete_json(cdl_cluster_name, json_skel)
        action_url = f"{cdl_url}/deleteDatalake"

    dump_json_dict(cdl_json)

    if not dryrun:
        requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdl_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on cluster {cdl_cluster_name}")

        poll_url = f"{cdl_url}/listDatalakes"

        if action == "install-cdl":
            elem_search_info = {
                "root_index": "datalakes",
                "expected_key_val": {
                    "datalakeName": cdl_cluster_name,
                    "status": "RUNNING",
                },
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
            json.dump(cdl_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()


if __name__ == "__main__":
    main()
