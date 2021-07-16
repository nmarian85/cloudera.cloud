#!/bin/bash
# Waiting for a component to reach a certain status in order to know if the action was succesful

set -eo pipefail
set -o errexit
set -o nounset

COMPONENT=$1
EXPECTED_STATUS=$2
STATUS=""
while true; 
do
    case $COMPONENT in
        CML)
            OUT=$(cdp ml describe-workspace --workspace-name $CML_CLUSTER_NAME --environment-name $ENV_NAME > /dev/null 2>&1)
            STATUS=$(echo $OUT | python -c 'import json,sys; print(json.load(sys.stdin)["workspace"]["instanceStatus"])')
        ;;
        CDE)
            cat << EOF > get_cluster_id.py
import json,sys,os
services=json.load(sys.stdin).get("services")
for service in services:
    if service.get("name") == os.getenv("CDE_CLUSTER_NAME"):
        print(service.get("status"))
EOF
            STATUS=$(cdp de list-services | python get_cluster_id.py)
            echo $STATUS
        ;;
        ENV)
            OUT=$(cdp environments describe-environment --environment-name $ENV_NAME > /dev/null 2>&1)
            STATUS=$(echo $OUT | python -c 'import json,sys; print(json.load(sys.stdin)["environment"]["status"])')
        ;;
    esac

    [ $STATUS == $EXPECTED_STATUS ] && exit 0
done