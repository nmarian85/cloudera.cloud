#!/bin/bash

set -eo pipefail
set -o errexit
set -o nounset

while true; 
do
    OUT=$(cdp environments describe-environment --environment-name $ENV_NAME)
    # echo $OUT
    STATUS=$(echo $OUT | python -c 'import json,sys; print(json.load(sys.stdin)["environment"]["status"])')
    [ $STATUS == 'AVAILABLE' ] && exit 0
done