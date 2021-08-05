import sys
import json
import os
import argparse

my_parser = argparse.ArgumentParser(description="Manage CML cluster")

# Add the arguments
my_parser.add_argument(
    "--action", choices=["install", "delete"], help="install or delete CDP environment",
)
my_parser.add_argument("-e", "--env", help="CDP env name")
my_parser.add_argument("-c", "--cdp-env-name", help="CDP env name")

args = my_parser.parse_args()

cdp_env_name = args.cdp_env_name
env = args.env

with open(f"{env}.json", "r") as read_file:
    envs = json.load(read_file)

if envs.get(cdp_env_name) is None:
    raise ValueError(f"Unable to find {cdp_env_name} in env.json")

with open("skel.json") as json_file:
    env_json_skel = json.load(json_file)

cdp_env_info = envs.get(cdp_env_name)
cdp_env_json = dict(env_json_skel)

cdp_env_json["environmentName"] = cdp_env_name
cdp_env_json["credentialName"] = cdp_env_info["credentials"]["cross_account_all_perm"]["credential_name"]
cdp_env_json["region"] = "eu-central-1"
cdp_env_json["vpcId"] = cdp_env_info["vpc_id"]
cdp_env_json["enableTunnel"] = True
cdp_env_json["securityAccess"]["securityGroupIdForKnox"] = cdp_env_info["sg"]
cdp_env_json["logStorage"]["storageLocationBase"] = f'{cdp_env_info["log_bucket"]}/{cdp_env_name}'
log_instance_profile = f'{cdp_env_info["log_role"]}-instance-profile'
role_iam_arn = f'arn:aws:iam::{cdp_env_info["account_id"]}'
cdp_env_json["logStorage"]["instanceProfile"] = (
    f'{role_iam_arn}:instance-profile/${log_instance_profile}')
cdp_env_json["freeIpa"]["instanceCountByGroup"] = 1
cdp_env_json["endpointAccessGatewayScheme"] = "PRIVATE"
# cdp_env_json["authentication"]["publicKey"]
cdp_env_json["authentication"]["publicKeyId"] = cdp_env_info["public_key_id"]

with open(f'{cdp_env_name}.json', "w", encoding="utf-8") as f:
    json.dump(cdp_env_json, f, ensure_ascii=False, indent=4)

# {
#     "environmentName": "",
#     "credentialName": "",
#     "region": "",
#     "securityAccess": {
#         "cidr": "",
#         "securityGroupIdForKnox": "",
#         "defaultSecurityGroupId": ""
#     },
#     "authentication": {
#         "publicKey": "",
#         "publicKeyId": ""
#     },
#     "logStorage": {
#         "storageLocationBase": "",
#         "instanceProfile": ""
#     },
#     "networkCidr": "",
#     "vpcId": "",
#     "subnetIds": [
#         ""
#     ],
#     "endpointAccessGatewayScheme": "",
#     "endpointAccessGatewaySubnetIds": [
#         ""
#     ],
#     "s3GuardTableName": "",
#     "description": "",
#     "enableTunnel": true,
#     "workloadAnalytics": true,
#     "reportDeploymentLogs": true,
#     "freeIpa": {
#         "instanceCountByGroup": 0
#     },
#     "image": {
#         "catalog": "",
#         "id": ""
#     },
#     "tags": [
#         {
#             "key": "",
#             "value": ""
#         }
#     ],
#     "proxyConfigName": ""
# # }

# {
#     "environment": {
#         "environmentName": "cdp-devo-lab-env01",
#         "crn": "crn:cdp:environments:us-west-1:0e62c9c8-e9cd-483b-81b3-651fe7a22deb:environment:f85b8fd2-a7af-4426-9f43-44a6b342658a",
#         "status": "AVAILABLE",
#         "region": "eu-central-1",
#         "cloudPlatform": "AWS",
#         "credentialName": "cdp-devo-policy-lab",
#         "network": {
#             "subnetIds": [
#                 "subnet-0e27b087b7fe35ff6",
#                 "subnet-01243e9afaaf36d3b",
#                 "subnet-012c688e22929b604",
#                 "subnet-029106fec17ba4c79",
#                 "subnet-02cda3e72e4840aef",
#                 "subnet-0c07b692fe1c6f3d7"
#             ],
#             "endpointAccessGatewayScheme": "PRIVATE",
#             "endpointAccessGatewaySubnetIds": [],
#             "aws": {
#                 "vpcId": "vpc-0132344c3ea4aa8e7"
#             },
#             "networkCidr": "10.130.18.0/24",
#             "subnetMetadata": {
#                 "subnet-0e27b087b7fe35ff6": {
#                     "subnetId": "subnet-0e27b087b7fe35ff6",
#                     "subnetName": "EcbAws-DEVO-LAB-FE-AZ3",
#                     "availabilityZone": "eu-central-1c",
#                     "cidr": "10.130.18.128/26"
#                 },
#                 "subnet-01243e9afaaf36d3b": {
#                     "subnetId": "subnet-01243e9afaaf36d3b",
#                     "subnetName": "EcbAws-DEVO-LAB-BE-AZ1",
#                     "availabilityZone": "eu-central-1a",
#                     "cidr": "10.129.48.0/24"
#                 },
#                 "subnet-012c688e22929b604": {
#                     "subnetId": "subnet-012c688e22929b604",
#                     "subnetName": "EcbAws-DEVO-LAB-BE-AZ3",
#                     "availabilityZone": "eu-central-1c",
#                     "cidr": "10.129.50.0/24"
#                 },
#                 "subnet-029106fec17ba4c79": {
#                     "subnetId": "subnet-029106fec17ba4c79",
#                     "subnetName": "EcbAws-DEVO-LAB-BE-AZ2",
#                     "availabilityZone": "eu-central-1b",
#                     "cidr": "10.129.49.0/24"
#                 },
#                 "subnet-02cda3e72e4840aef": {
#                     "subnetId": "subnet-02cda3e72e4840aef",
#                     "subnetName": "EcbAws-DEVO-LAB-FE-AZ2",
#                     "availabilityZone": "eu-central-1b",
#                     "cidr": "10.130.18.64/26"
#                 },
#                 "subnet-0c07b692fe1c6f3d7": {
#                     "subnetId": "subnet-0c07b692fe1c6f3d7",
#                     "subnetName": "EcbAws-DEVO-LAB-FE-AZ1",
#                     "availabilityZone": "eu-central-1a",
#                     "cidr": "10.130.18.0/26"
#                 }
#             }
#         },
#         "logStorage": {
#             "enabled": true,
#             "awsDetails": {
#                 "storageLocationBase": "s3a://cdp-devo-lab-env01-dl01-admin-logs",
#                 "instanceProfile": "arn:aws:iam::405945523162:instance-profile/env01-log-access-instance-profile"
#             }
#         },
#         "authentication": {
#             "publicKeyId": "cdp-devo-key-lab",
#             "loginUserName": "cloudbreak"
#         },
#         "securityAccess": {
#             "securityGroupIdForKnox": "sg-06475680081c165f6",
#             "defaultSecurityGroupId": "sg-06475680081c165f6"
#         },
#         "description": "First CDP environment",
#         "statusReason": "Error message: \"Freeipa should be in Available state but currently is STOPPED\"",
#         "created": "2021-03-16T12:52:16.806000+00:00",
#         "creator": "crn:altus:iam:us-west-1:0e62c9c8-e9cd-483b-81b3-651fe7a22deb:user:c4791741-9f30-40b9-aaf9-72f79c6ce986",
#         "awsDetails": {
#             "s3GuardTableName": "env01-dynamodb-table"
#         },
#         "reportDeploymentLogs": false,
#         "freeipa": {
#             "crn": "crn:cdp:freeipa:us-west-1:0e62c9c8-e9cd-483b-81b3-651fe7a22deb:freeipa:04e239a8-7133-49ba-bbd2-ddbcb65f69fc",
#             "domain": "cdp-devo.ftjq-cdim.cloudera.site",
#             "hostname": "ipaserver",
#             "serverIP": [
#                 "10.129.50.190"
#             ]
#         }
#     }
# }
