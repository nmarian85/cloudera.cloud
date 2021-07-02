import sys
import json
import os

with open("envs.json", "r") as read_file:
    envs = json.load(read_file)

with open("skel.json") as json_file:
    cml_json_skel = json.load(json_file)

for env, env_info in envs.items():
    cml_clusters = env_info["cml_clusters"]
    for cml_cluster, cml_cluster_info in cml_clusters.items():
        cml_json = dict(cml_json_skel)
        cml_json["environmentName"] = env
        cml_json["workspaceName"] = cml_cluster
        cml_json["removeStorage"] = True
        cml_json["force"] = False
        if cml_cluster_info["delete"] is True:
            with open(f"delete_cml_{cml_cluster}.json", "w", encoding="utf-8") as f:
                json.dump(cml_json, f, ensure_ascii=False, indent=4)
