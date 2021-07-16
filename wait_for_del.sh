#!/bin/bash

set -eo pipefail
set -o errexit
set -o nounset

COMPONENT=$1
while true; 
do
    case $COMPONENT in
        CML)
            cdp ml describe-workspace --workspace-name $CML_CLUSTER_NAME --environment-name $ENV_NAME  > /dev/null 2>&1 || exit 0 
        ;;
        CDE)
            cdp de list-services | egrep ".*?name.*$CDE_CLUSTER_NAME.*"  > /dev/null 2>&1 || exit 0
        ;;
        ENV)
            cdp environments describe-environment --environment-name $ENV_NAME > /dev/null 2>&1 || exit 0
        ;;
    esac
done