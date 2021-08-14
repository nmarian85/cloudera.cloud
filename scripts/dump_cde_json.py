import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CDE cluster")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["install", "delete"], help="Install or delete CDE cluster",
)
my_parser.add_argument("-e", "--env", help="Environment (e.g. lab)")
my_parser.add_argument("-c", "--cdp-env-name", help="CDP env name")
my_parser.add_argument("-m", "--cdecluster", help="CDE cluster name")
args = my_parser.parse_args()

cdp_env_name = args.cdp_env_name
env = args.env
cluster_name = args.cdecluster

with open(f"{env}.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(cdp_env_name) is None:
    raise ValueError(f"Unable to find {cdp_env_name} in env.json")

with open("skel.json") as json_file:
    env_json_skel = json.load(json_file)

cdp_env_info = envs.get(cdp_env_name)
cde_cluster = cdp_env_info.get("cde_clusters").get(cluster_name)

if cde_cluster is None:
    raise ValueError(f"Unable to find {cluster_name} in env.json")

with open("skel.json") as json_file:
    cde_json_skel = json.load(json_file)

cde_json = dict(cde_json_skel)

if args.action == "install":
    cde_json["name"] = cluster_name
    cde_json["env"] = cdp_env_name
    cde_json["instanceType"] = cde_cluster["instance_type"]
    cde_json["minimumInstances"] = cde_cluster["min_instances"]
    cde_json["maximumInstances"] = cde_cluster["max_instances"]
    cde_json["initialInstances"] = cde_cluster["initial_instances"]
    cde_json["minimumSpotInstances"] = cde_cluster["min_spot_instances"]
    cde_json["maximumSpotInstances"] = cde_cluster["max_spot_instances"]
    cde_json["initialSpotInstances"] = cde_cluster["initial_spot_instances"]
    cde_json["useSsd"] = cde_cluster["use_ssd"]
    cde_json["chartValueOverrides"] = []
    cde_json["rootVolumeSize"] = cde_cluster["root_vol_size"]
    cde_json["enablePublicEndpoint"] = False
    cde_json["enableWorkloadAnalytics"] = True
    # we are using an internal load balancer
    cde_json["whitelistIps"] = []
    cde_json["tags"] = [{f"{k}": f"{v}"} for k, v in cde_cluster["tags"].items()]

    with open(f"{cluster_name}.json", "w", encoding="utf-8") as f:
        json.dump(cde_json, f, ensure_ascii=False, indent=4)


