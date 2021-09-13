import click
import sys
import json
import os
from utils import show_progress, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops
import requests
from env_mgmt import get_cdp_env_crn


def dump_cdw_install_json(cdp_env_name, cdw_cluster_name, cdw_cluster_info, cdw_json_skel):
    cdw_json = dict(cdw_json_skel)
    cdw_json["environmentCrn"] = get_cdp_env_crn(cdp_env_name)
    cdw_json["useOverlayNetwork"] = True
    cdw_json["awsOptions"]["privateSubnetIds"] = cdw_cluster_info["subnets"]
    cdw_json["tags"] = cdw_cluster_info["tags"]
    return cdw_json


def dump_cdw_delete_json(cluster_id, cdw_json_skel):
    cdp_cdw_cluster_json = dict(cdw_json_skel)
    cdp_cdw_cluster_json["clusterId"] = cluster_id
    return cdp_cdw_cluster_json


def get_cdw_cluster_id(env_crn):
    action_url = f"{requests_ops.CDP_clusters_ENDPOINT}/dw/listClusters"
    response = requests_ops.send_http_request(
        srv_url=action_url, req_type="post", headers=generate_headers("POST", action_url), data={},
    )
    for cdw_cluster_info in response["clusters"]:
        if cdw_cluster_info["environmentCrn"] == env_crn:
            return cdw_cluster_info["id"]


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["install-cdw", "delete-cdw"]), required=True)
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
    "--cdw-cluster-name",
    help="Please see cdw.json for details regarding the cdw cluster",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, cdw_cluster_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        cdw_json_skel = json.load(json_file)

    with open(f"conf/{env}/{cdp_env_name}/cdw.json") as json_file:
        cdw_clusters = json.load(json_file)

    cdw_cluster_info = cdw_clusters[cdw_cluster_name]

    cdw_url = f"{requests_ops.CDP_clusters_ENDPOINT}/dw"

    env_crn = get_cdp_env_crn(cdp_env_name)

    if action == "install-cdw":
        click.echo(f"==============Installing cdw cluster {cdw_cluster_name}==============")
        cdw_cluster_json = dump_cdw_install_json(
            cdp_env_name, cdw_cluster_name, cdw_cluster_info, cdw_json_skel
        )
        action_url = f"{cdw_url}/createCluster"
    elif action == "delete-cdw":
        click.echo(f"==============Deleting cdw cluster {cdw_cluster_name}==============")
        cdw_cluster_json = dump_cdw_delete_json(get_cdw_cluster_id(env_crn), cdw_json_skel)
        action_url = f"{cdw_url}/deleteCluster"

    dump_json_dict(cdw_cluster_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cdw_cluster_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on cluster {cdw_cluster_name}")

        poll_url = f"{cdw_url}/listClusters"

        if action == "install-cdw":
            elem_search_info = {
                "root_index": "clusters",
                "expected_key_val": {"id": cdw_cluster_name, "status": "Running"},
                "present": True,
            }
        elif action == "delete-cdw":
            elem_search_info = {
                "root_index": "clusters",
                "expected_key_val": {"environmentCrn": env_crn},
                "present": False,
            }
        poll_for_status(poll_url=poll_url, elem_search_info=elem_search_info)

        click.echo(f"Action {action} on cluster {cdw_cluster_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{cdw_cluster_name}.json", "w", encoding="utf-8") as f:
            json.dump(cdw_cluster_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


if __name__ == "__main__":
    main()
