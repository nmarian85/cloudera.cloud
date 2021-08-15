import sys
import json
import os
import argparse
import env_info
# import cde_helper

def get_vc_id(all_vcs, vc_name):
    for vc in all_vcs["vcs"]:
        if vc["vcName"] == vc_name:
            return vc["vcId"]

my_parser = argparse.ArgumentParser(description="Install or delete CDE virtual clusters")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["install", "delete"], help="Install or delete CDE cluster",
)
args = my_parser.parse_args()

with open("skel.json") as json_file:
    cde_vc_json_skel = json.load(json_file)

cluster_name = os.getenv("CDE_CLUSTER_NAME")
cluster_id = os.getenv("CLUSTER_ID")

cde_cluster = env_info.cdp_env_info["cde_clusters"][cluster_name]

if cde_cluster is None:
    raise ValueError(f"Unable to find {cluster_name} in env.json")

# if we did not specify a list of CDE VCS then we will install/delete all the VCS belonging to that CDE cluster
vcs_list = os.getenv("CDE_VC_CLUSTERS").split()
if not vcs_list:
    vcs = cde_cluster["vcs"]
else:
    vcs = {vc_name: cde_cluster["vcs"][vc_name] for vc_name in vcs_list}

if args.action == "delete":
    with open("vcs.json") as json_vcs_file:
        all_vcs = json.load(json_vcs_file)

for vc_name, vc_info in vcs.items():
    cde_vc_json = dict(cde_vc_json_skel)
    cde_vc_json["clusterId"] = cluster_id

    if args.action == "install":
        cde_vc_json["name"] = vc_name
        cde_vc_json["cpuRequests"] = vc_info["cpu_requests"]
        cde_vc_json["memoryRequests"] = vc_info["memory_requests"]
        cde_vc_json["chartValueOverrides"] = vc_info["chart_value_overrides"]
        rsc = vc_info["runtime_spot_component"]
        if rsc == "DEFAULT":
            del cde_vc_json["runtimeSpotComponent"]
    if args.action == "delete":
        vc_id = get_vc_id(all_vcs, vc_name)
        cde_vc_json["vcId"] = vc_id
    with open(f"{vc_name}_vc.json", "w", encoding="utf-8") as f:
        json.dump(cde_vc_json, f, ensure_ascii=False, indent=4)
