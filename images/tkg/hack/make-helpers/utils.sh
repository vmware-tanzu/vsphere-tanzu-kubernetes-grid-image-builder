#!/bin/bash

# Terminal colors
red='\033[0;31m'
green='\033[0;32m'
clear='\033[0m'

function enable_debugging() {
    if [ ! -z ${DEBUGGING+x} ]; then
        set -x
    fi
}

function print_error() {
    printf "${red}${1}\n${clear}"
}

function is_argument_set() {
    variable=$2
    error_msg=$1
    if [ -z "$variable" ]; then
        printf "${red}${error_msg}\n${clear}"
        exit 1
    fi
}

function next_hint_msg() {
    printf "${green} Hint: ${1}\n${clear}"
}

function get_artifacts_container_name() {
    kubernetes_version=$1
    echo "$(echo $kubernetes_version | sed -e 's/+/---/' )-artifacts-server"
}

function get_artifacts_container_labels() {
    kubernetes_version=$1
    echo "-l byoi -l byoi_artifacts -l $kubernetes_version"
}

function get_node_image_builder_container_name() {
    kubernetes_version=$1
    os_target=$2
    echo $(echo $kubernetes_version | sed -e 's/+/---/' )-$os_target-image-builder
}

function get_node_image_builder_container_labels() {
    kubernetes_version=$1
    os_target=$2
    echo "-l byoi -l byoi_image_builder -l $kubernetes_version -l $os_target"
}