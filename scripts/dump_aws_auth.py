import sys
import yaml
import os

# multiline yaml entries
def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# yaml.add_representer(str, str_presenter)
yaml.representer.SafeRepresenter.add_representer(str, str_presenter)

# Load configmap
aws_auth_yaml = yaml.safe_load(sys.stdin.read())
del aws_auth_yaml["metadata"]

# Load multistring value for mapRoles
# map_roles_yaml = yaml.safe_load(
#     yaml.safe_dump(
#         aws_auth_yaml["data"]["mapRoles"], default_flow_style=False, allow_unicode=True
#     )
# )
map_roles_yaml = yaml.safe_load(aws_auth_yaml["data"]["mapRoles"])
print(yaml.safe_dump(map_roles_yaml, default_flow_style=False, allow_unicode=True))

# devo_env_name = os.environ["DEVO_ENV_NAME"]
# eks_cluster_type = os.environ["EKS_CLUSTER_TYPE"]
# account_id = os.environ["ACCOUNT_ID"]

# jumprole_arn = f"arn:aws:iam::{account_id}:role/jumpserver-role"
# jumprole_entry = dict(
#     {
#         "rolearn": jumprole_arn,
#         "username": "kubernetes-admin-jumpserver-role",
#         "groups": dict({"system": "masters"}),
#     }
# )
# y["data"]["mapRoles"] = y["data"]["mapRoles"] + yaml.safe_dump(
#     jumprole_entry, default_flow_style=False, allow_unicode=True
# )
# print(yaml.safe_dump(y, default_flow_style=False, allow_unicode=True))
