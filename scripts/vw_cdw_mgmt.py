import click
import json
from utils import show_progress, poll_for_status, dump_json_dict
from cdpv1sign import generate_headers
import requests_ops
from cdw_mgmt import get_cdw_cluster_id, get_cdw_dbc_id
from env_mgmt import get_cdp_env_crn


def get_vw_id(cdw_cluster_id, vw_name):
    action_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/dw/listVws"
    response = requests_ops.send_http_request(
        srv_url=action_url,
        req_type="post",
        headers=generate_headers("POST", action_url),
        data={"clusterId": cdw_cluster_id},
    )
    for vw_cdw_cluster_info in response["vws"]:
        if vw_cdw_cluster_info["name"] == vw_name:
            return vw_cdw_cluster_info["id"]


def dump_install_json(vw_name, cdw_vw_info, cdw_cluster_id):
    cdw_vw_json = {}

    cdw_vw_json["clusterId"] = cdw_cluster_id
    cdw_vw_json["fengEnabled"] = cdw_vw_info["feng_enabled"]
    cdw_vw_json["enableViz"] = cdw_vw_info["enable_viz"]
    cdw_vw_json["autoscaling"] = {}
    cdw_vw_json["multithreading"] = {}
    cdw_vw_json["config"] = {}

    if "impala" in vw_name:
        cdw_vw_json["impalaName"] = vw_name
        cdw_vw_json["autoscaling"]["minClusters"] = cdw_vw_info["autoscaling"][
            "min_clusters"
        ]
        cdw_vw_json["autoscaling"]["maxClusters"] = cdw_vw_info["autoscaling"][
            "max_clusters"
        ]
        cdw_vw_json["autoscaling"]["autoSuspendTimeoutSeconds"] = cdw_vw_info[
            "autoscaling"
        ]["auto_suspend_timeout_seconds"]

        cdw_vw_json["autoscaling"]["triggerScaleUpDelay"] = cdw_vw_info["autoscaling"][
            "trigger_scale_up_delay"
        ]
        cdw_vw_json["autoscaling"]["triggerScaleDownDelay"] = cdw_vw_info[
            "autoscaling"
        ]["trigger_scale_down_delay"]

        cdw_vw_json["autoscaling"]["impalaAutoscalingVersionNumber"] = cdw_vw_info[
            "autoscaling"
        ]["impala_autoscaling_version_number"]

        cdw_vw_json["autoscaling"]["enableHA"] = cdw_vw_info["autoscaling"]["enableHA"]

        cdw_vw_json["autoscaling"]["autoScaleMode"] = cdw_vw_info["autoscaling"][
            "auto_scale_mode"
        ]

        cdw_vw_json["multithreading"]["useLegacyMultithreading"] = cdw_vw_info[
            "multithreading"
        ]["use_legacy_multithreading"]

        cdw_vw_json["autoscaling"]["multithreadingVersion"] = cdw_vw_info[
            "multithreading"
        ]["multithreading_version"]

        cdw_vw_json["tags"] = cdw_vw_info["tags"]
        cdw_vw_json["warehouseId"] = get_cdw_dbc_id(
            cdw_cluster_id, cdw_vw_info["dbc_name"]
        )

        cdw_vw_json["template"] = cdw_vw_info["template"]
        cdw_vw_json["config"]["enableSSO"] = cdw_vw_info["config"]["enable_sso"]

    elif "hive" in vw_name:
        cdw_vw_json["hiveName"] = vw_name

    return cdw_vw_json


def dump_delete_json(cdw_cluster_id, vw_name, json_skel):
    cdw_vw_json = dict(json_skel)
    vw_id = get_vw_id(cdw_cluster_id, vw_name)
    cdw_vw_json["vwId"] = vw_id
    cdw_vw_json["clusterId"] = cdw_cluster_id
    return cdw_vw_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option(
    "--action", type=click.Choice(["install-vw-cdw", "delete-vw-cdw"]), required=True
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
    "--vw-name",
    help="Please see cdw.json for details regarding the cdw virtual warehouse",
    required=True,
)
@click.option(
    "--json-skel",
    help="NOT USED FOR CREATE-VW - JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, vw_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        json_skel = json.load(json_file)

    with open(f"conf/{env}/{cdp_env_name}/cdw.json") as json_file:
        cdw_cluster_info = json.load(json_file)

    cdw_vw_info = cdw_cluster_info["vws"][vw_name]
    cdp_env_crn = get_cdp_env_crn(cdp_env_name)
    cdw_cluster_id = get_cdw_cluster_id(cdp_env_crn)

    cdw_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/dw"
    cdw_v2_url = (
        f"{requests_ops.CDP_SERVICES_ENDPOINT_V2}/dwx/environments/{cdp_env_name}"
    )
    print(cdw_v2_url)

    if action == "install-vw-cdw":
        click.echo(f"===Installing virtual warehouse {vw_name}===")
        vw_json = dump_install_json(vw_name, cdw_vw_info, cdw_cluster_id)
        if "impala" in vw_name:
            action_url = "f{cdw_v2_url}/impalas"
        elif "hive" in vw_name:
            action_url = "f{cdw_v2_url}/hives"
        if not dryrun:
            requests_ops.send_http_request(
                srv_url=action_url,
                req_type="post",
                data=vw_json,
                headers=generate_headers("POST", action_url),
                params={"q": "start"},
            )
        click.echo(f"Waiting for {action} on virtual warehouse {vw_name}")

    elif action == "delete-vw-cdw":
        click.echo(f"===Deleting virtual warehouse {vw_name}===")
        vw_json = dump_delete_json(cdw_cluster_id, vw_name, json_skel)
        action_url = f"{cdw_url}/deleteVw"
        if not dryrun:
            requests_ops.send_http_request(
                srv_url=action_url,
                req_type="post",
                data=vw_json,
                headers=generate_headers("POST", action_url),
            )
        click.echo(f"Waiting for {action} on virtual warehouse {vw_name}")

    dump_json_dict(vw_json)

    if not dryrun:
        poll_url = f"{cdw_url}/listVws"
        if action == "install-vw-cdw":
            elem_search_info = {
                "root_index": "vws",
                "expected_key_val": {"name": vw_name, "status": "Running"},
                "present": True,
            }
        elif action == "delete-vw-cdw":
            elem_search_info = {
                "root_index": "vws",
                "expected_key_val": {"name": vw_name},
                "present": False,
            }
        poll_for_status(
            poll_url=poll_url,
            elem_search_info=elem_search_info,
            data={"clusterId": cdw_cluster_id},
        )

        click.echo(f"Action {action} on virtual warehouse {vw_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{vw_name}.json", "w", encoding="utf-8") as f:
            json.dump(vw_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()


if __name__ == "__main__":
    main()
