#!/bin/bash
# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: MPL-2.0

set -e
source $(dirname "${BASH_SOURCE[0]}")/utils.sh
enable_debugging

if [ -z "$LABEL" ]; then
    LABEL=byoi
fi

if [ "$(docker ps -a -q -f "label=$LABEL")" != '' ]; then
    docker rm -f $(docker ps -a -q -f "label=$LABEL")
fi