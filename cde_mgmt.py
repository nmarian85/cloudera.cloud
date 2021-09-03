import click
import sys
import json
import os
from utils import show_progress, get_env_info, poll_for_status
from cdpv1sign import generate_headers
import requests_ops
import requests
from time import sleep


# TODO: add code to add jump server role access to EKS control plane


def dump_cde_install_json(cdp_env_name, cde_cluster_name, cde_cluster_info, cde_json_skel):
    cde_json = dict(cde_json_skel)
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


def dump_cde_delete_json(cdp_env_name, cdp_env_info, cde_json_skel):
    cdp_env_json = dict(cde_json_skel)
    cdp_env_json["environmentName"] = cdp_env_name
    return cdp_env_json


@click.command()
@click.option("--dryrun/--no-dryrun", default=True)
@click.option("--action", type=click.Choice(["install-cde", "delete-cde"]), required=True)
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
    "--cde-cluster-name",
    help="Please see {env}.json file where you defined the CDE cluster name",
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
        cde_json_skel = json.load(json_file)

    cdp_env_info = get_env_info(env, cdp_env_name)

    cde_cluster_info = cdp_env_info["cde_clusters"][cde_cluster_name]

    env_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/de"

    if action == "install-cde":
        click.echo(f"==============Creating environment {cdp_env_name}==============")
        env_json = dump_cde_install_json(
            cdp_env_name, cde_cluster_name, cde_cluster_info, cde_json_skel
        )
        action_url = f"{env_url}/enableService"
    elif action == "delete-cde":
        click.echo(f"==============Deleting environment {cdp_env_name}==============")
        env_json = dump_cde_delete_json(
            cdp_env_name, cde_cluster_name, cde_cluster_info, cde_json_skel
        )
        action_url = f"{env_url}/disableService"

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

        click.echo(f"Waiting for {action} on cluster {cde_cluster_name}")

        poll_url = f"{env_url}/listServices"

        if action == "install-cde":
            elem_search_info = {
                "root_index": "services",
                "expected_key_val": {
                    "name": cde_cluster_name,
                    "status": "ClusterCreationCompleted",
                },
                "present": True,
            }
        elif action == "delete-cde":
            elem_search_info = {
                "root_index": "services",
                "expected_key_val": {"name": cde_cluster_name},
                "present": False,
            }
        poll_for_status(poll_url=poll_url, elem_search_info=elem_search_info)

        click.echo(f"Action {action} on cluster {cde_cluster_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{cde_cluster_name}.json", "w", encoding="utf-8") as f:
            json.dump(env_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===========================================================")
    click.echo()


if __name__ == "__main__":
    main()
