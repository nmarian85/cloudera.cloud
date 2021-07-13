import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CML cluster")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["provision", "delete"], help="provision or delete CML cluster",
)
my_parser.add_argument("-c", "--cluster", help="CML cluster name")
my_parser.add_argument("-e", "--env", help="CDP env name")
args = my_parser.parse_args()

cluster_name = args.cluster
env_name = args.env

with open("envs.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(env_name) is None:
    raise ValueError(f"Unable to find {env_name} in env.json")

if envs[env_name]["cml_clusters"].get(cluster_name) is None:
    raise ValueError(f"Unable to find {cluster_name} in env.json")

# read skeleton from command cdp ml create-workspace --generate-cli-skeleton
with open("skel.json") as json_file:
    cml_json_skel = json.load(json_file)

cml_cluster = envs[env_name]["cml_clusters"][cluster_name]
cml_json = dict(cml_json_skel)
cml_json["environmentName"] = env_name
cml_json["workspaceName"] = cluster_name

if args.action == "provision":
    cml_json["usePublicLoadBalancer"] = False
    cml_json["disableTLS"] = False
    cml_json["enableMonitoring"] = True
    cml_json["enableGovernance"] = True
    cml_json["loadBalancerIPWhitelists"] = []
    cml_json["provisionK8sRequest"]["environmentName"] = env_name
    cml_json["provisionK8sRequest"]["network"] = {}
    cml_json["provisionK8sRequest"]["tags"] = [
        {"key": f"{k}", "value": f"{v}"} for k, v in cml_cluster["tags"].items()
    ]
    cml_json_ig = list(cml_json["provisionK8sRequest"]["instanceGroups"])

    # mlinfra
    cml_json_ig[0]["instanceType"] = cml_cluster["ml_infra_info"]["instance_type"]
    cml_json_ig[0]["instanceCount"] = cml_cluster["ml_infra_info"]["instance_count"]
    cml_json_ig[0]["name"] = cml_cluster["ml_infra_info"]["name"]
    cml_json_ig[0]["rootVolume"]["size"] = cml_cluster["ml_infra_info"]["root_volume"]
    cml_json_ig[0]["autoscaling"]["minInstances"] = cml_cluster["ml_infra_info"]["min_instances"]
    cml_json_ig[0]["autoscaling"]["maxInstances"] = cml_cluster["ml_infra_info"]["max_instances"]

    # mlworker
    cml_json_ig.append(dict(cml_json_ig[0]))
    cml_json_ig[1]["instanceType"] = cml_cluster["ml_worker_info"]["instance_type"]
    cml_json_ig[1]["instanceCount"] = cml_cluster["ml_worker_info"]["instance_count"]
    cml_json_ig[1]["name"] = cml_cluster["ml_worker_info"]["name"]
    cml_json_ig[1]["rootVolume"]["size"] = cml_cluster["ml_worker_info"]["root_volume"]
    cml_json_ig[1]["autoscaling"]["minInstances"] = cml_cluster["ml_worker_info"]["min_instances"]
    cml_json_ig[1]["autoscaling"]["maxInstances"] = cml_cluster["ml_worker_info"]["max_instances"]

    cml_json["provisionK8sRequest"]["instanceGroups"] = list(cml_json_ig)
    if cml_cluster["provision"] is True:
        with open(f"{cml_cluster}.json", "w", encoding="utf-8") as f:
            json.dump(cml_json, f, ensure_ascii=False, indent=4)

elif args.action == "delete":
    cml_json = dict(cml_json_skel)
    cml_json["removeStorage"] = True
    cml_json["force"] = False
    if cml_cluster["delete"] is True:
        with open(f"{cml_cluster}.json", "w", encoding="utf-8") as f:
            json.dump(cml_json, f, ensure_ascii=False, indent=4)
