#!/bin/bash

set -e
source $(dirname "${BASH_SOURCE[0]}")/utils.sh
enable_debugging

printf "%30s  |  %s\n" "Kubernetes Version" "Supported OS"
jq -r 'to_entries[] | "\(.key) \(.value | .supported_os)"' $SUPPORTED_VERSIONS_JSON | xargs printf "%30s  |  %s\n"

echo ""
next_hint_msg "Use \"make run-artifacts-container KUBERNETES_VERSION=<version>\" to run the artifacts container."