#!/bin/bash
# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: MPL-2.0

set -e
source $(dirname "${BASH_SOURCE[0]}")/utils.sh
enable_debugging

is_argument_set "IMAGE_ARTIFACTS_PATH argument is required" $IMAGE_ARTIFACTS_PATH

log_folder=$IMAGE_ARTIFACTS_PATH/logs
ovas_folder=$IMAGE_ARTIFACTS_PATH/ovas

rm -r -f $log_folder
rm -r -f $ovas_folder