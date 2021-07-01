import sys
import json
import os

cde_infra_info = json.loads(os.getenv("CDE_INFRA_INFO"))

# set in the gitlab pipeline as env variables
env_name = os.getenv("ENV_NAME")
cde_name = os.getenv("CDE_NAME")

# read skeleton from --generate-cli-skeleton option
cde_json = json.load(sys.stdin)

cde_json["name"] = cde_name
cde_json["env"] = env_name
cde_json["instanceType"] = cde_infra_info["instance_type"]
cde_json["minimumInstances"] = cde_infra_info["min_instances"]
cde_json["maximumInstances"] = cde_infra_info["max_instances"]
cde_json["initialInstances"] = cde_infra_info["initial_instances"]
cde_json["minimumSpotInstances"] = cde_infra_info["min_spot_instances"]
cde_json["maximumSpotInstances"] = cde_infra_info["max_spot_instances"]
cde_json["initialSpotInstances"] = cde_infra_info["initial_spot_instances"]
cde_json["useSsd"] = cde_infra_info["use_ssd"]
cde_json["chartValueOverrides"] = []
cde_json["rootVolumeSize"] = cde_infra_info["root_vol_size"]
cde_json["enablePublicEndpoint"] = False
cde_json["enableWorkloadAnalytics"] = True
# we are using an internal load balancer
cde_json["whitelistIps"] = []
cde_json["tags"] = [{f"{k}": f"{v}"} for k, v in cde_infra_info["tags"].items()]

print(json.dumps(cde_json, indent=4, sort_keys=True))
