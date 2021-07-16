#!/bin/bash

set -eo pipefail
set -o errexit
set -o nounset

COMPONENT=$1
while true; 
do
    case $COMPONENT in
        CML)
            cdp ml describe-workspace --workspace-name $CML_CLUSTER_NAME --environment-name $ENV_NAME || exit 0 
        ;;
        CDE)
        ;;
        ENV)
            cdp environments describe-environment --environment-name $ENV_NAME) || exit 0
        ;;
    esac
done