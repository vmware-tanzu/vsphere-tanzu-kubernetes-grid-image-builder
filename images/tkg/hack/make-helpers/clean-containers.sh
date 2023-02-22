#!/bin/bash

set -e
source $(dirname "${BASH_SOURCE[0]}")/utils.sh
enable_debugging

if [ -z "$LABEL" ]; then
    LABEL=byoi
fi

if [ "$(docker ps -a -q -f "label=$LABEL")" != '' ]; then
    docker rm -f $(docker ps -a -q -f "label=$LABEL")
fi