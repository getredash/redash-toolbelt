#!/usr/bin/env bash
# @(#) checks the logs of a redash orchestration until startup is finished

set -euo pipefail; export FS=$'\n\t'

function redash_is_ready {
    logcheck=$(docker-compose logs | grep celery | grep -c ready)
    if [[ "${logcheck}" == "3" ]];
    then
        echo 0 # = true
    else
        echo 1 # = false
    fi
}

function wait_until_redash_is_ready {
    GREEN="\033[0;32m"
    RED="\033[0;31m"
    NC="\033[0m" # No Color

    MAX_CHECKS=20
    SLEEP_BETWEEN_CHECKS=2
    COUNT_CHECKS=1

    echo -n "Waiting for healthy orchestration "
    until [[ "$(redash_is_ready)" == "0" ]] || [[ "${COUNT_CHECKS}" -gt "${MAX_CHECKS}" ]] ; do
        printf '.'
        sleep ${SLEEP_BETWEEN_CHECKS}
        COUNT_CHECKS=$((COUNT_CHECKS+1))
    done
    if [[ "$(redash_is_ready)" == "0" ]];
    then
        echo -e " ${GREEN}done${NC}"
    else
        echo -e " ${RED}timeout or failed (please check logs and/or check container state with 'docker ps')${NC}"
        exit 1
    fi
}

wait_until_redash_is_ready

