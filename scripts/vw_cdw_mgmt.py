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


def dump_install_json(vw_name, cdw_vw_info, cdw_cluster_id, json_skel):
    cdw_vw_json = dict(json_skel)
    cdw_vw_json["clusterId"] = cdw_cluster_id
    cdw_vw_json["name"] = vw_name
    cdw_vw_json["tags"] = cdw_vw_info["tags"]
    image_version = cdw_vw_info["image_version"]
    if len(image_version) != 0:
        cdw_vw_json["imageVersion"] = image_version

    cdw_vw_json["dbcId"] = get_cdw_dbc_id(cdw_cluster_id, cdw_vw_info["dbc_name"])

    cdw_vw_json["vwType"] = cdw_vw_info["vw_type"]
    cdw_vw_json["config"]["applicationConfigs"] = cdw_vw_info["config"][
        "application_configs"
    ]
    cdw_vw_json["config"]["commonConfigs"] = cdw_vw_info["config"]["common_configs"]
    cdw_vw_json["config"]["enableSSO"] = cdw_vw_info["config"]["enable_sso"]
    ldap_groups = cdw_vw_info["config"]["ldap_groups"]
    if len(ldap_groups) != 0:
        cdw_vw_json["ldapGroups"] = ldap_groups
    cdw_vw_json["autoscaling"]["minClusters"] = cdw_vw_info["autoscaling"][
        "min_clusters"
    ]
    cdw_vw_json["autoscaling"]["maxClusters"] = cdw_vw_info["autoscaling"][
        "max_clusters"
    ]

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
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
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

    if action == "install-vw-cdw":
        click.echo(f"===Installing virtual warehouse {vw_name}===")
        vw_json = dump_install_json(vw_name, cdw_vw_info, cdw_cluster_id, json_skel)
        action_url = f"{cdw_url}/createVw"
    elif action == "delete-vw-cdw":
        click.echo(f"===Deleting virtual warehouse {vw_name}===")
        vw_json = dump_delete_json(cdw_cluster_id, vw_name, json_skel)

        action_url = f"{cdw_url}/deleteVw"

    dump_json_dict(vw_json)

    if not dryrun:
        requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=vw_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on virtual warehouse {vw_name}")

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
