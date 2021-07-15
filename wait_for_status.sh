#!/bin/bash

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
            OUT=$(cdp ml describe-workspace --workspace-name $CML_CLUSTER_NAME --environment-name $ENV_NAME 2>/dev/null)
            # this check is to be used to verify if the workspace was already deleted
            [ -z $OUT ] && exit 0
            STATUS=$(echo $OUT | python -c 'import json,sys; print(json.load(sys.stdin)["workspace"]["instanceStatus"])')
        ;;
        CDE)
        ;;
        ENV)
            OUT=$(cdp environments describe-environment --environment-name $ENV_NAME)
            # this check is to be used to verify if the environment was already deleted as part of the delete workflow
            [ -z $OUT ] && exit 0
            STATUS=$(echo $OUT | python -c 'import json,sys; print(json.load(sys.stdin)["environment"]["status"])')
        ;;
    esac

    [ $STATUS == $EXPECTED_STATUS ] && exit 0
done