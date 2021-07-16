import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CDE cluster")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["provision", "delete"], help="provision or delete CDE cluster",
)
my_parser.add_argument("-c", "--cluster", help="CDE cluster name")
my_parser.add_argument("-e", "--env", help="CDP env name")
args = my_parser.parse_args()

cluster_name = args.cluster
env_name = args.env

with open("envs.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(env_name) is None:
    raise ValueError(f"Unable to find {env_name} in env.json")

if envs[env_name]["cde_clusters"].get(cluster_name) is None:
    raise ValueError(f"Unable to find {cluster_name} in env.json")

# read skeleton from command cdp ml create-workspace --generate-cli-skeleton
with open("skel.json") as json_file:
    cde_json_skel = json.load(json_file)

cde_cluster = envs[env_name]["cde_clusters"][cluster_name]
cde_json = dict(cde_json_skel)

if args.action == "provision":
    cde_json["name"] = cluster_name
    cde_json["env"] = env_name
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

    if cde_cluster["provision"] is True:
        with open(f"{cluster_name}.json", "w", encoding="utf-8") as f:
            json.dump(cde_json, f, ensure_ascii=False, indent=4)

# elif args.action == "delete":
#     cde_json["clusterId"] = True
#     cde_json["force"] = False
#     if cde_cluster["delete"] is True:
#         with open(f"{cluster_name}.json", "w", encoding="utf-8") as f:
#             json.dump(cde_json, f, ensure_ascii=False, indent=4)
