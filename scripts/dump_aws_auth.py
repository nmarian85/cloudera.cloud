import sys
import yaml
import os

y = yaml.safe_load(sys.stdin.read())
del y["metadata"]

devo_env_name = os.environ["DEVO_ENV_NAME"]
eks_cluster_type = os.environ["EKS_CLUSTER_TYPE"]
account_id = os.environ["ACCOUNT_ID"]
print(yaml.safe_dump(y, default_flow_style=False, allow_unicode=True))
# yaml.safe_dump(y["data"]["mapRoles"]

# - rolearn: arn:aws:iam::303413094647:role/jumpserver-role
#   username: kubernetes-admin-jumpserver-role
#   groups:
#     - system:masters

# out_file = f"aws_auth_{devo_env_name}-{eks_cluster_type}.yaml"
# with open(f"{out_file}", "w", encoding="utf-8") as f:
#     yaml.safe_dump(y, out_file, default_flow_style=False, allow_unicode=True)

