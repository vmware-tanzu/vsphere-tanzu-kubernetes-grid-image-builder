#!/bin/bash
# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: MPL-2.0

set -e
set -x

# Default variables
image_builder_root=/image-builder/images/capi
default_packer_variables=${image_builder_root}/image/packer-variables/
packer_configuration_folder=${image_builder_root}
tkr_metadata_folder=${image_builder_root}/tkr-metadata/
custom_ovf_properties_file=${image_builder_root}/custom_ovf_properties.json
artifacts_output_folder=${image_builder_root}/artifacts
ova_destination_folder=${artifacts_output_folder}/ovas
photon3_stig_compliance="false"

function checkout_image_builder_branch() {
    # Check out image builder with specific commit for the
    # corresponding k8s version
    cd ${image_builder_root}
    git pull
    git checkout ${IMAGE_BUILDER_COMMIT_ID}
}

function copy_custom_image_builder_files() {
    cp image/hack/tkgs-image-build-ova.py hack/image-build-ova.py
    cp image/hack/tkgs_ovf_template.xml hack/ovf_template.xml
}

function download_configuration_files() {
    # Download kubernetes configuration file
    wget -q http://${HOST_IP}:${ARTIFACTS_CONTAINER_PORT}/artifacts/metadata/kubernetes_config.json

    # Download tkr-bom and tkr metadata files
    wget -q http://${HOST_IP}:${ARTIFACTS_CONTAINER_PORT}/artifacts/tkr-bom/tkr-bom.yaml
    wget -q http://${HOST_IP}:${ARTIFACTS_CONTAINER_PORT}/artifacts/metadata/unified-tkr-vsphere.tar.gz
    mkdir ${tkr_metadata_folder}
    tar xzf unified-tkr-vsphere.tar.gz -C ./tkr-metadata

    # Download compatibility files
    wget -q http://${HOST_IP}:${ARTIFACTS_CONTAINER_PORT}/artifacts/metadata/compatibility/vmware-system.compatibilityoffering.json
    wget -q http://${HOST_IP}:${ARTIFACTS_CONTAINER_PORT}/artifacts/metadata/compatibility/vmware-system.guest.kubernetes.distribution.image.version.json
}

# Generate packaer input variables based on packer-variables folder
function generate_packager_configuration() {
    mkdir -p $ova_destination_folder
    python3 image/scripts/tkg_byoi.py setup \
    --host_ip ${HOST_IP} \
    --artifacts_container_port ${ARTIFACTS_CONTAINER_PORT} \
    --packer_http_port ${PACKER_HTTP_PORT} \
    --default_config_folder ${default_packer_variables} \
    --dest_config ${packer_configuration_folder} \
    --tkr_metadata_folder ${tkr_metadata_folder} \
    --tkr_suffix ${TKR_SUFFIX} \
    --kubernetes_config ${image_builder_root}/kubernetes_config.json \
    --ova_destination_folder ${ova_destination_folder} \
    --os_type ${OS_TARGET}

    echo "Image Builder Packer Variables"
    cat ${packer_configuration_folder}/packer-variables.json
}

function generate_custom_ovf_properties() {
    python3 image/scripts/utkg_custom_ovf_properties.py \
    --kubernetes_config ${image_builder_root}/kubernetes_config.json \
    --outfile ${custom_ovf_properties_file}
}

function check_photon3_stig_compliance() {
    readarray -d + -t kubernetes_series_arr <<< "$KUBERNETES_VERSION"
    kubernetes_series=$(echo "${kubernetes_series_arr[0]//v}")
    printf -v versions '%s\n%s' "1.25.0" "$kubernetes_series"
    if [[ $versions = "$(sort -V <<< "$versions")" ]]
    then
      photon3_stig_compliance="true"
    fi
}

function download_photon3_stig_files() {
    check_photon3_stig_compliance
    if [ ${OS_TARGET} == "photon-3" ] && [ ${photon3_stig_compliance} == "true" ]
    then
      tanzu_compliance_dir="${image_builder_root}/image/ansible/tanzu-compliance"
      if [ -d "$tanzu_compliance_dir" ]
      then
        rm -rf ${tanzu_compliance_dir}
      fi
      wget -q http://${HOST_IP}:${ARTIFACTS_CONTAINER_PORT}/artifacts/photon-3-stig-hardening.tar.gz
      tar -xvf photon-3-stig-hardening.tar.gz -C ${image_builder_root}/image/ansible/
      mv ${image_builder_root}/image/ansible/photon-3-stig-hardening-* ${tanzu_compliance_dir}
      rm -rf photon-3-stig-hardening.tar.gz
    fi
}

# Enable packer debug logging to the log file
function packer_logging() {
    mkdir /image-builder/packer_cache
    mkdir -p $artifacts_output_folder/logs
    export PACKER_LOG=10
    export PACKER_LOG_PATH="${artifacts_output_folder}/logs/packer-$RANDOM.log"
    echo "Generating packer logs to $PACKER_LOG_PATH"
}

# Invokes kubernetes image builder for the corresponding OS target
function trigger_image_builder() {
    PATH=$PATH:/home/imgbuilder-ova/.local/bin PACKER_CACHE_DIR=/image-builder/packer_cache \
    PACKER_VAR_FILES="${image_builder_root}/packer-variables.json"  \
    OVF_CUSTOM_PROPERTIES=${custom_ovf_properties_file} \
    IB_OVFTOOL=1 ANSIBLE_TIMEOUT=180 IB_OVFTOOL_ARGS="--allowExtraConfig" \
    make build-node-ova-vsphere-${OS_TARGET}
}

# Packer generates OVA with a different name so change the OVA name to OSImage/VMI and
# copy to the destination folder.
function copy_ova() {
    python3 image/scripts/tkg_byoi.py copy_ova \
    --kubernetes_config ${image_builder_root}/kubernetes_config.json \
    --tkr_metadata_folder ${tkr_metadata_folder} \
    --tkr_suffix ${TKR_SUFFIX} --os_type ${OS_TARGET} \
    --ova_destination_folder ${ova_destination_folder}
}

function main() {
    checkout_image_builder_branch
    copy_custom_image_builder_files
    download_configuration_files
    generate_packager_configuration
    generate_custom_ovf_properties
    download_photon3_stig_files
    packer_logging
    trigger_image_builder
    copy_ova
}

main
