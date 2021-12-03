import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops
from cde_mgmt import get_cde_cluster_id


def get_vc_id(cde_cluster_id, vc_name):
    action_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/de/listVcs"
    response = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        headers=generate_headers("POST", action_url),
        data={"clusterId": cde_cluster_id},
    )
    for vc_cde_cluster_info in response["vcs"]:
        if vc_cde_cluster_info["vcName"] == vc_name:
            return vc_cde_cluster_info["vcId"]


def dump_install_json(vc_name, vc_cde_info, cde_cluster_id, vc_json):
    cde_vc_json = dict(vc_json)
    cde_vc_json["clusterId"] = cde_cluster_id
    cde_vc_json["name"] = vc_name
    cde_vc_json["cpuRequests"] = vc_cde_info["cpu_requests"]
    cde_vc_json["memoryRequests"] = vc_cde_info["memory_requests"]
    cde_vc_json["chartValueOverrides"] = vc_cde_info["chart_value_overrides"]
    cde_vc_json["runtimeSpotComponent"] = vc_cde_info["runtime_spot_component"]
    # rsc = vc_cde_info["runtime_spot_component"]
    # if rsc == "DEFAULT":
    #     del cde_vc_json["runtimeSpotComponent"]
    cde_vc_json["sparkVersion"] = vc_cde_info["spark_version"]
    return cde_vc_json


def dump_delete_json(cde_cluster_id, vc_name, vc_json):
    cde_vc_json = dict(vc_json)
    vc_id = get_vc_id(cde_cluster_id, vc_name)
    cde_vc_json["vcId"] = vc_id
    cde_vc_json["clusterId"] = cde_cluster_id
    return cde_vc_json


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
    "--vc-name",
    help="Please see cde.json for details regarding the CDE virtual cluster",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, cde_cluster_name, vc_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        vc_json = json.load(json_file)

    with open(f"conf/{env}/{cdp_env_name}/cde.json") as json_file:
        cde_clusters = json.load(json_file)

    cde_cluster_info = cde_clusters[cde_cluster_name]

    vc_cde_info = cde_cluster_info["vcs"][vc_name]
    cde_cluster_id = get_cde_cluster_id(cde_cluster_name)

    cde_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/de"

    if action == "install":
        click.echo(f"===Installing virtual CDE cluster {vc_name}===")
        vc_json = dump_install_json(vc_name, vc_cde_info, cde_cluster_id, vc_json)
        action_url = f"{cde_url}/createVc"
    elif action == "delete":
        click.echo(f"===Deleting virtual CDE cluster {vc_name}===")
        vc_json = dump_delete_json(cde_cluster_id, vc_name, vc_json)

        action_url = f"{cde_url}/deleteVc"

    dump_json_dict(vc_json)

    if not dryrun:
        requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=vc_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on virtual cluster {vc_name}")

        poll_url = f"{cde_url}/listVcs"

        if action == "install":
            elem_search_info = {
                "root_index": "vcs",
                "expected_key_val": {"vcName": vc_name, "status": "AppInstalled"},
                "present": True,
            }
        elif action == "delete":
            elem_search_info = {
                "root_index": "vcs",
                "expected_key_val": {"vcName": vc_name},
                "present": False,
            }
        poll_for_status(
            poll_url=poll_url,
            elem_search_info=elem_search_info,
            data={"clusterId": cde_cluster_id},
        )

        click.echo(f"Action {action} on virtual cluster {vc_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{vc_name}.json", "w", encoding="utf-8") as f:
            json.dump(vc_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()


if __name__ == "__main__":
    main()
