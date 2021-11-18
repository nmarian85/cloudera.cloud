import click
import json
from utils import show_progress, poll_for_status
from cdpv1sign import generate_headers
import requests_ops


def dump_install_json(cdp_env_name, json_skel, cml_cluster_name, cml_cluster_info):
    cml_json = dict(json_skel)

    cml_json["environmentName"] = cdp_env_name
    cml_json["workspaceName"] = cml_cluster_name
    cml_json["usePublicLoadBalancer"] = False
    cml_json["disableTLS"] = False
    cml_json["enableMonitoring"] = True
    cml_json["enableGovernance"] = cml_cluster_info["enable_governance"]
    cml_json["loadBalancerIPWhitelists"] = []
    cml_json["provisionK8sRequest"]["environmentName"] = cdp_env_name
    cml_json["provisionK8sRequest"]["network"] = {}
    cml_json["provisionK8sRequest"]["tags"] = [
        {"key": f"{k}", "value": f"{v}"} for k, v in cml_cluster_info["tags"].items()
    ]
    cml_json_ig = list(cml_json["provisionK8sRequest"]["instanceGroups"])

    # mlinfra
    cml_json_ig[0]["instanceType"] = cml_cluster_info["ml_infra_info"]["instance_type"]
    cml_json_ig[0]["instanceCount"] = cml_cluster_info["ml_infra_info"][
        "instance_count"
    ]
    cml_json_ig[0]["name"] = cml_cluster_info["ml_infra_info"]["name"]
    cml_json_ig[0]["rootVolume"]["size"] = cml_cluster_info["ml_infra_info"][
        "root_volume"
    ]
    cml_json_ig[0]["autoscaling"]["minInstances"] = cml_cluster_info["ml_infra_info"][
        "min_instances"
    ]
    cml_json_ig[0]["autoscaling"]["maxInstances"] = cml_cluster_info["ml_infra_info"][
        "max_instances"
    ]

    # mlworker
    cml_json_ig.append(dict(cml_json_ig[0]))
    cml_json_ig[1]["instanceType"] = cml_cluster_info["ml_worker_info"]["instance_type"]
    cml_json_ig[1]["instanceCount"] = cml_cluster_info["ml_worker_info"][
        "instance_count"
    ]
    cml_json_ig[1]["name"] = cml_cluster_info["ml_worker_info"]["name"]
    cml_json_ig[1]["rootVolume"]["size"] = cml_cluster_info["ml_worker_info"][
        "root_volume"
    ]
    cml_json_ig[1]["autoscaling"]["minInstances"] = cml_cluster_info["ml_worker_info"][
        "min_instances"
    ]
    cml_json_ig[1]["autoscaling"]["maxInstances"] = cml_cluster_info["ml_worker_info"][
        "max_instances"
    ]

    cml_json["provisionK8sRequest"]["instanceGroups"] = list(cml_json_ig)
    return cml_json


def dump_delete_json(json_skel):
    cml_json = dict(json_skel)
    cml_json["removeStorage"] = True
    return cml_json


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
    help="Please see {env}.json file where you defined the CDP env name",
    required=True,
)
@click.option(
    "--cml-cluster-name",
    help="Please see cde.json for details regarding the CML cluster",
    required=True,
)
@click.option(
    "--json-skel",
    help="JSON skeleton for command to be run (generate it with cdpcli generate skel option)",
    required=True,
)
def main(dryrun, env, cdp_env_name, cml_cluster_name, action, json_skel):
    if dryrun:
        show_progress("This is a dryrun")

    requests_ops.dryrun = dryrun

    with open(json_skel) as json_file:
        json_skel = json.load(json_file)

    with open(f"conf/{env}/{cdp_env_name}/cml.json") as json_file:
        cml_clusters = json.load(json_file)

    cml_cluster_info = cml_clusters[cml_cluster_name]
    cml_url = f"{requests_ops.CDP_SERVICES_ENDPOINT}/ml"

    if action == "install":
        click.echo(f"===Creating CML cluster {cml_cluster_name}===")
        cml_json = dump_install_json(
            cdp_env_name, json_skel, cml_cluster_name, cml_cluster_info
        )
        action_url = f"{cml_url}/createWorkspace"
    elif action == "delete":
        click.echo(f"===Deleting CML cluster {cml_cluster_name}===")
        cml_json = dump_delete_json(json_skel)
        action_url = f"{cml_url}/deleteWorkspace"

    click.echo("-------------------Generated JSON-----------------------------")
    print(json.dumps(cml_json, indent=4, sort_keys=True))
    click.echo("--------------------------------------------------------------")

    if not dryrun:
        requests_ops.send_http_request(
            srv_url=action_url,
            req_type="post",
            data=cml_json,
            headers=generate_headers("POST", action_url),
        )

        click.echo(f"Waiting for {action} on cluster {cml_cluster_name}")

        poll_url = f"{cml_url}/listWorkspaces"

        if action == "install":
            elem_search_info = {
                "root_index": "workspaces",
                "expected_key_val": {
                    "instanceName": cml_cluster_name,
                    "instanceStatus": "installation:finished",
                },
                "present": True,
            }
        elif action == "delete":
            elem_search_info = {
                "root_index": "workspaces",
                "expected_key_val": {"instanceName": cml_cluster_name},
                "present": False,
            }
        poll_for_status(poll_url=poll_url, elem_search_info=elem_search_info)

        click.echo(f"Action {action} on cluster {cml_cluster_name} DONE")

        # dumping file so that Gitlab will back it up
        with open(f"{cml_cluster_name}.json", "w", encoding="utf-8") as f:
            json.dump(cml_json, f, ensure_ascii=False, indent=4)
    click.echo(f"===============")
    click.echo()


if __name__ == "__main__":
    main()
