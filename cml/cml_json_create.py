import sys
import json
import os

ml_infra_info = {
    "instance_type": "m5.2xlarge",
    "instance_count": 2,
    "name": "mlinfra",
    "min_instances": 2,
    "max_instances": 3,
    "tags": [{"key": "role.node.kubernetes.io/infra", "value": "true"}],
    "root_volume": 100,
}

ml_worker_info = {
    "instance_type": "c4.4xlarge",
    "instance_count": 1,
    "name": "mlcpu0",
    "min_instances": 1,
    "max_instances": 3,
    "tags": [{"key": "role.node.kubernetes.io/cpu", "value": "true"}],
    "root_volume": 100,
}

# set in the gitlab pipeline as env variables
env_name = os.getenv("ENV_NAME")
workspace_name = os.getenv("WORKSPACE_NAME")

# aws ec2 describe-subnets --region eu-central-1  --query 'Subnets[*][SubnetArn]' --output text | cut -d/ -f2 | tr -s '\n' ','
all_subnets = [i for i in os.getenv("ALL_SUBNETS").split(" ")]

# read skeleton from command cdp ml create-workspace --generate-cli-skeleton
cml_json = json.load(sys.stdin)
cml_json["environmentName"] = env_name
cml_json["workspaceName"] = workspace_name
cml_json["usePublicLoadBalancer"] = False
cml_json["disableTLS"] = False
cml_json["enableMonitoring"] = True
cml_json["enableGovernance"] = True
cml_json["provisionK8sRequest"]["network"]["plugin"]["topology"]["subnets"] = all_subnets

cml_json_ig = cml_json["provisionK8sRequest"]["instanceGroups"]

# mlinfra
cml_json_ig[0]["instanceType"] = ml_infra_info["instance_type"]
cml_json_ig[0]["instanceCount"] = ml_infra_info["instance_count"]
cml_json_ig[0]["name"] = ml_infra_info["name"]
cml_json_ig[0]["rootVolume"] = ml_infra_info["root_volume"]
cml_json_ig[0]["autoscaling"]["minInstances"] = ml_infra_info["min_instances"]
cml_json_ig[0]["autoscaling"]["maxInstances"] = ml_infra_info["max_instances"]
cml_json_ig[0]["tags"] = ml_infra_info["tags"]

# mlworker
cml_json_ig.append(cml_json_ig[0])
cml_json_ig[1]["instanceType"] = ml_worker_info["instance_type"]
cml_json_ig[1]["instanceCount"] = ml_worker_info["instance_count"]
cml_json_ig[1]["name"] = ml_worker_info["name"]
cml_json_ig[1]["rootVolume"] = ml_worker_info["root_volume"]
cml_json_ig[1]["autoscaling"]["minInstances"] = ml_worker_info["min_instances"]
cml_json_ig[1]["autoscaling"]["maxInstances"] = ml_worker_info["max_instances"]
cml_json_ig[1]["tags"] = ml_worker_info["tags"]
cml_json["provisionK8sRequest"]["instanceGroups"] = cml_json_ig

print(json.dumps(cml_json, indent=4, sort_keys=True))

# bash-4.4# cdp ml create-workspace --cli-input-json $(cdp ml create-workspace --generate-cli-skeleton | python3 helpers/cml_json_create.py)
