import sys
import json
import os
import argparse
import env_info
import cde_helper

my_parser = argparse.ArgumentParser(description="Install or delete CDE virtual clusters")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["install", "delete"], help="Install or delete CDE cluster",
)
my_parser.add_argument("-v", "--cdevccluster", action='store_true', help="VC CDE cluster name")

args = my_parser.parse_args()

with open("skel.json") as json_file:
    cde_vc_json_skel = json.load(json_file)

for cluster_name in os.getenv("CDE_CLUSTERS").split():
    cde_cluster = env_info.cdp_env_info["cde_clusters"][cluster_name]

    if cde_cluster is None:
        raise ValueError(f"Unable to find {cluster_name} in env.json")

    if args.cdevccluster:
        vcs = {args.cdevccluster: cde_cluster["vcs"][args.cdevccluster]}
    else:
        vcs = cde_cluster["vcs"]

    if args.action == "install":
        for vc_name, vc_info in vcs.items():
            cde_vc_json = dict(cde_vc_json_skel)
            cde_vc_json["clusterId"] = cde_helper.get_cluster_id(cluster_name)
            cde_vc_json["name"] = vc_name
            cde_vc_json["cpuRequests"] = vc_info["cpu_requests"]
            cde_vc_json["memoryRequests"] = vc_info["memory_requests"]
            cde_vc_json["chartValueOverrides"] = vc_info["chart_value_overrides"]
            rsc = vc_info["runtime_spot_component"]
            if rsc == "DEFAULT":
                del cde_vc_json["runtimeSpotComponent"]
            with open(f"{vc_name}_vc.json", "w", encoding="utf-8") as f:
                json.dump(cde_vc_json, f, ensure_ascii=False, indent=4)


# my_parser.add_argument("-e", "--env", help="Environment (e.g. lab)")
# my_parser.add_argument("-c", "--cdp-env-name", help="CDP env name")
# my_parser.add_argument("-m", "--cdecluster", help="CDE cluster name")
# my_parser.add_argument("-i", "--cdeclusterid", help="CDE cluster id")

# # if defined, only this VC will be installed/deleted, otherwise all VCs belonging
# # to the CDE cluster will be
# my_parser.add_argument("-v", "--cdevccluster", action='store_true', help="VC CDE cluster name")

# args = my_parser.parse_args()

# cdp_env_name = args.cdp_env_name
# env = args.env
# cluster_name = args.cdecluster
# cluster_id = args.cdeclusterid

# with open(f"{env}.json", "r") as read_file:
#     envs = json.load(read_file)

# if envs.get(cdp_env_name) is None:
#     raise ValueError(f"Unable to find {cdp_env_name} in env.json")

# with open("skel.json") as json_file:
#     env_json_skel = json.load(json_file)

# cdp_env_info = envs.get(cdp_env_name)
# cde_cluster = cdp_env_info.get("cde_clusters").get(cluster_name)

# if cde_cluster is None:
#     raise ValueError(f"Unable to find {cluster_name} in env.json")

# with open("skel.json") as json_file:
#     cde_vc_json_skel = json.load(json_file)

# # we target only a specific vcs if the vc was specified in the CLI
# if args.cdevccluster:
#     vcs = {args.cdevccluster: cde_cluster["vcs"][args.cdevccluster]}
# else:
#     vcs = cde_cluster["vcs"]

# if args.action == "delete":
#     with open("vcs.json") as json_vcs_file:
#         all_vcs = json.load(json_vcs_file)
#     # we need this list to know which virtual clusters to delete
#     all_vcid = []

# for vc_name, vc_info in vcs.items():
#     cde_vc_json = dict(cde_vc_json_skel)
#     cde_vc_json["clusterId"] = cluster_id
#     if args.action == "install":
#         cde_vc_json["name"] = vc_name
#         cde_vc_json["cpuRequests"] = vc_info["cpu_requests"]
#         cde_vc_json["memoryRequests"] = vc_info["memory_requests"]
#         cde_vc_json["chartValueOverrides"] = vc_info["chart_value_overrides"]
#         rsc = vc_info["runtime_spot_component"]
#         if rsc == "DEFAULT":
#             del cde_vc_json["runtimeSpotComponent"]
#         else:
#             cde_vc_json["runtimeSpotComponent"] = rsc
#     elif args.action == "delete":
#         vc_id = get_vc_id(all_vcs, vc_name)
#         cde_vc_json["vcId"] = vc_id
#         all_vcid.append(vc_id)
#     with open(f"{vc_name}_vc.json", "w", encoding="utf-8") as f:
#         json.dump(cde_vc_json, f, ensure_ascii=False, indent=4)

# # writing the vcids to a csv file in order to be able to wait for their deletion to finish outside the script
# if args.action == "delete":
#     with open(f"{cluster_name}.csv", "w", encoding="utf-8") as f:
#         for vcid in all_vcid:
#             f.write(f"{vcid},")
