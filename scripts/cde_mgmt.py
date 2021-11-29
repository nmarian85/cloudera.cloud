import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops


def dump_install_json(cdp_env_name, cde_cluster_name, cde_cluster_info, json_skel):
    cde_json = dict(json_skel)
    cde_json["name"] = cde_cluster_name
    cde_json["env"] = cdp_env_name
    cde_json["instanceType"] = cde_cluster_info["instance_type"]
    cde_json["minimumInstances"] = cde_cluster_info["min_instances"]
    cde_json["maximumInstances"] = cde_cluster_info["max_instances"]
    cde_json["initialInstances"] = cde_cluster_info["initial_instances"]
    cde_json["minimumSpotInstances"] = cde_cluster_info["min_spot_instances"]
    cde_json["maximumSpotInstances"] = cde_cluster_info["max_spot_instances"]
    cde_json["initialSpotInstances"] = cde_cluster_info["initial_spot_instances"]
    cde_json["useSsd"] = cde_cluster_info["use_ssd"]
    cde_json["chartValueOverrides"] = []
    cde_json["rootVolumeSize"] = cde_cluster_info["root_vol_size"]
    cde_json["enablePublicEndpoint"] = False
    cde_json["enableWorkloadAnalytics"] = False
    # we are using an internal load balancer
    cde_json["whitelistIps"] = []
    cde_json["tags"] = cde_cluster_info["tags"]
    return cde_json


def dump_delete_json(cluster_id, json_skel):
    cdp_cde_cluster_json = dict(json_skel)
    cdp_cde_cluster_json["clusterId"] = cluster_id
    return cdp_cde_cluster_json


def get_cde_cluster_id(cluster_name):
    action_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/de/listServices"
    response = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        headers=generate_headers("POST", action_url),
        data={},
    )
    for cde_cluster_info in response["services"]:
        if cde_cluster_info["name"] == cluster_name and (
            cde_cluster_info["status"] == "ClusterCreationCompleted"
            or cde_cluster_info["status"] == "ClusterProvisioningFailed"
        ):
            return cde_cluster_info["clusterId"]


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["install", "delete"]), required=True)
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
    "--cde-cluster-name",
    help="Please see cde.json for details regarding the CDE cluster",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, cde_cluster_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        json_skel = json.load(json_file)

    with open(f"conf/{env}/{cdp_env_name}/cde.json") as json_file:
        cde_clusters = json.load(json_file)

    cde_cluster_info = cde_clusters[cde_cluster_name]

    cde_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/de"

    if action == "install":
        click.echo(f"===Installing CDE cluster {cde_cluster_name}===")
        cde_cluster_json = dump_install_json(
            cdp_env_name, cde_cluster_name, cde_cluster_info, json_skel
        )
        action_url = f"{cde_url}/enableService"
    elif action == "delete":
        click.echo(f"===Deleting CDE cluster {cde_cluster_name}===")
        cde_cluster_json = dump_delete_json(
            get_cde_cluster_id(cde_cluster_name), json_skel
        )
        action_url = f"{cde_url}/disableService"

    dump_json_dict(cde_cluster_json)

    if not dryrun:
        response = requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cde_cluster_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on cluster {cde_cluster_name}")

        poll_url = f"{cde_url}/listServices"

        if action == "install":
            elem_search_info = {
                "root_index": "services",
                "expected_key_val": {
                    "name": cde_cluster_name,
                    "status": "ClusterCreationCompleted",
                },
                "present": True,
            }
        elif action == "delete":
            elem_search_info = {
                "root_index": "services",
                "expected_key_val": {"name": cde_cluster_name},
                "present": False,
            }
        poll_for_status(
            poll_url=poll_url,
            elem_search_info=elem_search_info,
            data={"removeDeleted": True},
        )

        click.echo(f"Action {action} on cluster {cde_cluster_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{cde_cluster_name}.json", "w", encoding="utf-8") as f:
            json.dump(cde_cluster_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()


if __name__ == "__main__":
    main()
