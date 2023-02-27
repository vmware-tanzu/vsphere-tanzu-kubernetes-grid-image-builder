#!/usr/bin/env bash
# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: MPL-2.0

set -o errexit
set -o nounset
set -o pipefail

set -e
source $(dirname "${BASH_SOURCE[0]}")/utils.sh

enable_debugging

red=$(tput setaf 1)
reset=$(tput sgr0)
readonly red reset

ROOT=$(dirname "${BASH_SOURCE[0]}")/../..
ALL_TARGETS=$(make -C "${ROOT}" PRINT_HELP=y -rpn | sed -n -e '/^$/ { n ; /^[^ .#][^ ]*:/ { s/:.*$// ; p ; } ; }' | sort)

echo "--------------------------------------------------------------------------------"
for tar in ${ALL_TARGETS}; do
	echo -e "${red}${tar}${reset}"
	make -C "${ROOT}" "${tar}" PRINT_HELP=y
	echo "---------------------------------------------------------------------------------"
done