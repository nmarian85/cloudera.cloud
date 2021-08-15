#!/bin/bash

set -eo pipefail
set -o errexit
set -o nounset

COMPONENT=$1

while true; 
do
    case $COMPONENT in
        CML)
            cdp ml describe-workspace --workspace-name $CML_CLUSTER_NAME --environment-name $CDP_ENV_NAME  > /dev/null 2>&1 || exit 0 
        ;;
        
        CDE)
            cdp de list-services | egrep ".*?name.*$CDE_CLUSTER_NAME.*" > /dev/null 2>&1 || exit 0
        ;;
        
        CDE_VC)
            cdp de describe-vc --cli-input-json file://${VC_FILE} > /dev/null 2>&1 || exit 0
        ;;

        ENV)
            cdp environments describe-environment --environment-name $CDP_ENV_NAME > /dev/null 2>&1 || exit 0
        ;;

        DL)
            cdp datalake describe-datalake --datalake-name $DLAKE_NAME > /dev/null 2>&1 || exit 0
        ;;
    esac
done