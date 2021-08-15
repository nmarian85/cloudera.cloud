#!/bin/bash

set -eo pipefail
set -o errexit
set -o nounset

COMPONENT=$1

# if [ "$COMPONENT" = "CDE" ]; then
#     cat << EOF > get_cluster_id.py
# import json,sys,os
# services=json.load(sys.stdin).get("services")
# for service in services:
#     if service.get("name") == os.getenv("CDE_CLUSTER_NAME"):
#         print(service.get("clusterId"))
# EOF
#     CLUSTER_ID=$(cdp de list-services | python get_cluster_id.py)
#     [ ! -z "$CLUSTER_ID" ] && cdp de disable-service --cluster-id $CLUSTER_ID
# fi

while true; 
do
    case $COMPONENT in
        CML)
            cdp ml describe-workspace --workspace-name $CML_CLUSTER_NAME --environment-name $CDP_ENV_NAME  > /dev/null 2>&1 || exit 0 
        ;;
        
        CDE)
            cdp de list-services | egrep ".*?name.*$CDE_CLUSTER_NAME.*" > /dev/null 2>&1 || exit 0
        ;;
        
        # CDE_VC)
        #     cdp de list-vcs --cluster-id $CLUSTER_ID | egrep ".*?cdp-devo-lab-env01-cde02-vc01.*" | egrep ".*?name.*$CDE_CLUSTER_NAME.*" > /dev/null 2>&1 || exit 0
        # ;;

        ENV)
            cdp environments describe-environment --environment-name $CDP_ENV_NAME > /dev/null 2>&1 || exit 0
        ;;

        DL)
            cdp datalake describe-datalake --datalake-name $DLAKE_NAME > /dev/null 2>&1 || exit 0
        ;;
    esac
done