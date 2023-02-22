#!/bin/bash

set -e
source $(dirname "${BASH_SOURCE[0]}")/utils.sh

enable_debugging

is_argument_set "KUBERNETES_VERSION argument is required" $KUBERNETES_VERSION

if [ -z "$ARTIFACTS_CONTAINER_PORT" ]; then
    # Makefile creates this environment variables
    ARTIFACTS_CONTAINER_PORT=$DEFAULT_ARTIFACTS_CONTAINER_PORT
    echo "Using default port for artifacts container $DEFAULT_ARTIFACTS_CONTAINER_PORT"
fi

artifacts_container_image_url=$(jq -r '."'$KUBERNETES_VERSION'".artifacts_image' $SUPPORTED_VERSIONS_JSON)
if [ "$artifacts_container_image_url" == "null" ]; then
    print_error 'Use Supported kubernetes version, to list supported kubernetes versions run "make list-versions"'
    exit 1
fi

container_name=$(get_artifacts_container_name "$KUBERNETES_VERSION")
docker run -d --name $container_name $(get_artifacts_container_labels $KUBERNETES_VERSION) -p $ARTIFACTS_CONTAINER_PORT:80 $artifacts_container_image_url

next_hint_msg "Use \"make build-node-image OS_TARGET=<os_target> KUBERNETES_VERSION=${KUBERNETES_VERSION} TKR_SUFFIX=<tkr_suffix> ARTIFACTS_CONTAINER_IP=<artifacts_container_ip> IMAGE_ARTIFACTS_PATH=<image_artifacts_path> ARTIFACTS_CONTAINER_PORT=${ARTIFACTS_CONTAINER_PORT}\" to build node image"