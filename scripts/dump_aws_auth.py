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

devo_env_name = os.environ["DEVO_ENV_NAME"]
eks_cluster_type = os.environ["EKS_CLUSTER_TYPE"]
account_id = os.environ["ACCOUNT_ID"]
jumprole_arn = f"arn:aws:iam::{account_id}:role/jumpserver-role"
jumprole_entry = {
    "rolearn": jumprole_arn,
    "username": "kubernetes-admin-jumpserver-role",
    "groups": ["system:masters"],
}

# Load configmap
aws_auth_yaml = yaml.safe_load(sys.stdin.read())

# Removing metadata since we do not need it at apply time
for field in ["annotations", "creationTimestamp", "resourceVersion", "uid"]:
    del aws_auth_yaml["metadata"][field]

# Load multistring value for mapRoles
map_roles_yaml = yaml.safe_load(aws_auth_yaml["data"]["mapRoles"])

# Adding the jumprole as a k8s admin
map_roles_yaml.append(jumprole_entry)

aws_auth_yaml["data"]["mapRoles"] = yaml.safe_dump(
    map_roles_yaml, default_flow_style=False, allow_unicode=True
)
print(yaml.safe_dump(aws_auth_yaml, default_flow_style=False, allow_unicode=True))

# y["data"]["mapRoles"] = y["data"]["mapRoles"] + yaml.safe_dump(
#     jumprole_entry, default_flow_style=False, allow_unicode=True
# )
# print(yaml.safe_dump(y, default_flow_style=False, allow_unicode=True))
