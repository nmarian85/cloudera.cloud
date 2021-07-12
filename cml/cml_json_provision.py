import sys
import json
import os

with open("envs.json", "r") as read_file:
    envs = json.load(read_file)

# read skeleton from command cdp ml create-workspace --generate-cli-skeleton
with open("skel.json") as json_file:
    cml_json_skel = json.load(json_file)

cluster_name = os.getenv("CML_CLUSTER_NAME")
if cluster_name is None:
    raise ValueError("Please provide cluster name as env variable CML_CLUSTER_NAME")

for env, env_info in envs.items():
    cml_clusters = env_info["cml_clusters"]
    for cml_cluster, cml_cluster_info in cml_clusters.items():
        if cluster_name == cml_cluster:
            cml_json = dict(cml_json_skel)
            cml_json["environmentName"] = env
            cml_json["workspaceName"] = cml_cluster
            cml_json["usePublicLoadBalancer"] = False
            cml_json["disableTLS"] = False
            cml_json["enableMonitoring"] = True
            cml_json["enableGovernance"] = True
            cml_json["loadBalancerIPWhitelists"] = []
            cml_json["provisionK8sRequest"]["environmentName"] = env
            cml_json["provisionK8sRequest"]["network"] = {}
            cml_json["provisionK8sRequest"]["tags"] = [
                {"key": f"{k}", "value": f"{v}"} for k, v in cml_cluster_info["tags"].items()
            ]
            cml_json_ig = list(cml_json["provisionK8sRequest"]["instanceGroups"])

            # mlinfra
            cml_json_ig[0]["instanceType"] = cml_cluster_info["ml_infra_info"]["instance_type"]
            cml_json_ig[0]["instanceCount"] = cml_cluster_info["ml_infra_info"]["instance_count"]
            cml_json_ig[0]["name"] = cml_cluster_info["ml_infra_info"]["name"]
            cml_json_ig[0]["rootVolume"]["size"] = cml_cluster_info["ml_infra_info"]["root_volume"]
            cml_json_ig[0]["autoscaling"]["minInstances"] = cml_cluster_info["ml_infra_info"][
                "min_instances"
            ]
            cml_json_ig[0]["autoscaling"]["maxInstances"] = cml_cluster_info["ml_infra_info"][
                "max_instances"
            ]

            # mlworker
            cml_json_ig.append(dict(cml_json_ig[0]))
            cml_json_ig[1]["instanceType"] = cml_cluster_info["ml_worker_info"]["instance_type"]
            cml_json_ig[1]["instanceCount"] = cml_cluster_info["ml_worker_info"]["instance_count"]
            cml_json_ig[1]["name"] = cml_cluster_info["ml_worker_info"]["name"]
            cml_json_ig[1]["rootVolume"]["size"] = cml_cluster_info["ml_worker_info"]["root_volume"]
            cml_json_ig[1]["autoscaling"]["minInstances"] = cml_cluster_info["ml_worker_info"][
                "min_instances"
            ]
            cml_json_ig[1]["autoscaling"]["maxInstances"] = cml_cluster_info["ml_worker_info"][
                "max_instances"
            ]

            cml_json["provisionK8sRequest"]["instanceGroups"] = list(cml_json_ig)
            if cml_cluster_info["provision"] is True:
                with open(f"{cml_cluster}.json", "w", encoding="utf-8") as f:
                    json.dump(cml_json, f, ensure_ascii=False, indent=4)
