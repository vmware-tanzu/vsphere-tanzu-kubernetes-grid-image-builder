# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: MPL-2.0

import argparse
import json
import os
import shutil
import semver

import yaml
from jinja2 import Environment, BaseLoader

# Dictionary to store the Jinja Variables that stores data
# about kubernetes version and URLs
jinja_args_map = {}
packer_vars = {}

tkr_api_kind = "TanzuKubernetesRelease"
osimage_api_kind = "OSImage"
cbt_api_kind = "ClusterBootstrapTemplate"
package_api_kind = "Package"

osimage_name_format = "{}-{}-{}-{}-{}"
tkr_name_format = "{}-{}"
max_k8s_object_name_length = 63
max_tkr_suffix_length = 8


def parse_args():
    parser = argparse.ArgumentParser(
        description='Script to setup the Packer Variables for TKG BYOI')
    sub_parsers = parser.add_subparsers(help="Helper functions", dest='subparser_name')
    setup_group = sub_parsers.add_parser('setup')
    setup_group.add_argument('--kubernetes_config', required=True,
                             help='Kubernetes related configuration JSON')
    setup_group.add_argument('--os_type', required=True,
                             help='OS type')
    setup_group.add_argument('--artifacts_container_ip', required=True,
                             help='Artifacts container IP')
    setup_group.add_argument('--artifacts_container_port', required=False,
                             help='Artifacts container port, default value is 8081', default="8081")
    setup_group.add_argument('--default_config_folder', required=True,
                             help='Path to default packer variable configuration folder')
    setup_group.add_argument('--tkr_metadata_folder', required=True,
                             help='Path to TKR metadata')
    setup_group.add_argument('--tkr_suffix', required=True,
                             help='Suffix to be added to the TKR, OVA and OSImage')
    setup_group.add_argument('--dest_config', required=True,
                             help='Path to the final packer destination config file')
    setup_group.add_argument('--ova_destination_folder', required=True,
                             help='Destination folder to copy the OVA after changing the name')

    ova_copy_group = sub_parsers.add_parser("copy_ova")
    ova_copy_group.add_argument('--kubernetes_config', required=True,
                                help='Kubernetes related configuration JSON')
    ova_copy_group.add_argument('--os_type', required=True,
                                help='OS type')
    ova_copy_group.add_argument('--tkr_metadata_folder', required=True,
                                help='Path to TKR metadata')
    ova_copy_group.add_argument('--tkr_suffix', required=True,
                                help='Suffix to be added to the TKR, OVA and OSImage')
    ova_copy_group.add_argument('--ova_destination_folder', required=True,
                                help='Destination folder to copy the OVA after changing the name')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    if args.subparser_name == "setup":
        setup(args)
    elif args.subparser_name == "copy_ova":
        copy_ova(args)


def setup(args):
    """
    Parse and template the Jinja files present in the packer-variables folder.
    """
    global jinja_args_map

    populate_jinja_args(args)

    render_default_config(args)
    json.dump(packer_vars, open(os.path.join(args.dest_config, 'packer-variables.json'), 'w'), indent=4)

    update_tkr_metadata(args)


def populate_jinja_args(args):
    """
    Populate the key value pairs for Jinja templates based on the kubernetes configuration
    file downloaded from the artifacts container.
    """
    global jinja_args_map

    jinja_args_map = vars(args)
    kubernetes_args = {}
    with open(args.kubernetes_config, 'r') as fp:
        kubernetes_args = json.loads(fp.read())
    jinja_args_map.update(kubernetes_args)
    jinja_args_map["kubernetes_version"] = jinja_args_map["kubernetes"]
    jinja_args_map["kubernetes_series"] = jinja_args_map["kubernetes"].split('+')[0]

    # Set STIG compliant value
    jinja_args_map["photon3_stig_compliance"] = "false"
    if args.os_type == "photon-3":
        check_photon3_stig_compliance()

    images_local_host_paths = get_images_local_host_path(args)
    jinja_args_map.update(images_local_host_paths)
    print("Jinja Args:", jinja_args_map)


def get_images_local_host_path(args):
    """
    Get the localhost paths based on the Package objects from the
    TKR metadata that will be used for by imgpkg to upload the 
    thick tar files to local docker registry during the image build.
    """
    packages_folder = os.path.join(args.tkr_metadata_folder, "packages")
    localhost_paths = {}
    kapp_key_name = ''
    kapp_file = ''
    for subdir, dirs, files in os.walk(packages_folder):
        for file in files:
            with open(os.path.join(subdir, file), 'r') as fp:
                yaml_doc = yaml.safe_load(fp)
                if yaml_doc["kind"] == package_api_kind:
                    key_name = yaml_doc["spec"]["refName"].split('.')[0].replace('-', '_')
                    if 'kapp' not in key_name:
                        key_name = key_name + '_package_localhost_path'
                        path = ":".join(
                            yaml_doc["spec"]["template"]["spec"]["fetch"][0]["imgpkgBundle"]["image"].split(':')[0:-1])
                        localhost_paths[key_name] = path
                        continue
                    kapp_file = os.path.join(subdir, file)
                    kapp_key_name = key_name + '_localhost_path'
    with open(kapp_file, 'r') as fp:
        for line in fp:
            if "- image:" in line:
                path = ':'.join(line.strip().split('@')[0].split(':')[1:]).strip()
                localhost_paths[kapp_key_name] = path
                print(line)
    return localhost_paths


def copy_ova(args):
    """
    Copy the OVA from output folder to destination folder after changing the OVA name.
    """
    default_ova_destination_folder = '/image-builder/images/capi/output/{}-kube-{}/'
    config_folder = os.path.join(args.tkr_metadata_folder, "config")
    new_ova_name = ''
    for filename in os.listdir(config_folder):
        file = os.path.join(config_folder, filename)
        with open(file, 'r') as fp:
            yaml_docs = yaml.safe_load_all(fp)
            for yaml_doc in yaml_docs:
                if yaml_doc["kind"] == osimage_api_kind and yaml_doc["spec"]["os"]["name"] in args.os_type:
                    new_ova_name = "{}.ova".format(yaml_doc["spec"]["image"]["ref"]["name"])

    old_ova_name = ''
    with open(args.kubernetes_config, 'r') as fp:
        kubernetes_args = json.loads(fp.read())
        default_ova_destination_folder = \
            default_ova_destination_folder.format(args.os_type, kubernetes_args["kubernetes"].split('+')[0])
        old_ova_name = "{}-{}.ova".format(args.os_type, kubernetes_args["kubernetes"].replace('+', '---'))

    new_path = os.path.join(args.ova_destination_folder, new_ova_name)
    old_path = os.path.join(default_ova_destination_folder, old_ova_name)
    print("Copying OVA from {} to {}".format(old_path, new_path))
    shutil.copyfile(old_path, new_path)
    print("Copying completed")


def update_tkr_metadata(args):
    """
    Reads the TKR metadata like Addon Config, TKR, CBT and Package objects
    that are downloaded from the artifacts containers and updates the TKR,
    CBT and Addon config objects name based on the <kubernetes_version>-<tkr_suffix>
    """
    config_folder = os.path.join(args.tkr_metadata_folder, "config")
    kubernetes_version = None
    old_tkr_name = None
    tkr_file = None
    cbt_file = None
    osimage_files = []
    addons_files = []
    for filename in os.listdir(config_folder):
        file = os.path.join(config_folder, filename)
        with open(file, 'r') as fp:
            yaml_docs = yaml.safe_load_all(fp)
            for yaml_doc in yaml_docs:
                if yaml_doc["kind"] == tkr_api_kind:
                    # kubernetes version contains + which is not a supported character
                    # so replace + with ---
                    kubernetes_version = yaml_doc["spec"]["kubernetes"]["version"].replace('+', '---')
                    tkr_file = file
                    old_tkr_name = yaml_doc["metadata"]["name"]
                elif yaml_doc["kind"] == osimage_api_kind:
                    osimage_files.append(file)
                elif yaml_doc["kind"] == cbt_api_kind:
                    cbt_file = file
                else:
                    if file not in addons_files:
                        addons_files.append(file)

    new_osimages = []
    for osimage_file in osimage_files:
        new_osimage_name = ''
        with open(osimage_file, 'r') as fp:
            yaml_doc = yaml.safe_load(fp)
            # Create new OSImage name based on the OS Name, version and architecture.
            new_osimage_name = format_name(osimage_name_format, args.tkr_suffix, yaml_doc["spec"]["os"]["name"],
                                           yaml_doc["spec"]["os"]["version"].replace('.', ''),
                                           yaml_doc["spec"]["os"]["arch"],
                                           kubernetes_version)
            new_osimages.append({"name": new_osimage_name})
            if yaml_doc["spec"]["os"]["name"].lower() in args.os_type.lower():
                check_ova_file(new_osimage_name, args.ova_destination_folder)
        update_osimage(osimage_file, new_osimage_name)

    new_tkr_name = format_name(tkr_name_format, args.tkr_suffix, kubernetes_version)
    update_tkr(tkr_file, new_tkr_name, new_osimages)
    update_cbt(cbt_file, new_tkr_name, old_tkr_name, new_tkr_name)

    for addon_file in addons_files:
        update_addon_config(addon_file, old_tkr_name, new_tkr_name)


def check_ova_file(new_osimage_name, ova_destination_folder):
    """
    Verifies if a OVA file with a same TKR version and TKR suffix
    exists in the image artifacts folder.
    """
    for filename in os.listdir(ova_destination_folder):
        if filename == "{}.ova".format(new_osimage_name):
            raise Exception("OVA {}.ova already exists in the OVA folder".format(new_osimage_name))


def update_addon_config(addon_file, old_tkr_name, new_tkr_name):
    """
    Update the Addon Config object name. (For updating the data on CBT refer to update_cbt function)
    """
    addon_data = []
    with open(addon_file, 'r') as os_fp:
        temp_addon_data = yaml.safe_load_all(os_fp)
        for yaml_doc in temp_addon_data:
            old_name = yaml_doc["metadata"]["name"]
            new_name = old_name.replace(old_tkr_name, new_tkr_name)
            yaml_doc["metadata"]["name"] = new_name
            print("{} name changed from {} to {}".format(yaml_doc["kind"], old_name, new_name))
            addon_data.append(yaml_doc)

    with open(addon_file, 'w') as os_fp:
        yaml.dump_all(addon_data, os_fp)


def update_osimage(osimage_file, osimage_name):
    """
    Update OSImage object with the new name
    """
    osimage_data = ''
    with open(osimage_file, 'r') as os_fp:
        osimage_data = yaml.safe_load(os_fp)
    osimage_data["metadata"]["name"] = osimage_name
    osimage_data["spec"]["image"]["ref"]["name"] = osimage_name
    print("New OSImage Name for {} is {}".format(osimage_data["spec"]["os"]["name"], osimage_name))
    with open(osimage_file, 'w') as os_fp:
        yaml.dump(osimage_data, os_fp)


def update_tkr(tkr_file, tkr_name, osimages):
    """
    Update the TKR object with the new name based on kubernetes and suffix.
    New name format is <kuberneter_version>-<tkr_suffix>
    """
    tkr_data = ''
    with open(tkr_file, 'r') as fp:
        tkr_data = yaml.safe_load(fp)
    tkr_data["metadata"]["name"] = tkr_name
    tkr_data["spec"]["osImages"] = osimages
    tkr_data["spec"]["version"] = tkr_name.replace('---', '+')
    with open(tkr_file, 'w') as fp:
        yaml.dump(tkr_data, fp)
    print("New TKR Name:", tkr_name)


def update_cbt(cbt_file, cbt_name, old_tkr_name, new_tkr_name):
    """
    Updates the CBT with new data like
    - Name of CBT.
    - Updates all the addons object names like calico,antrea,kapp,csi,cpi configs
      from old TKR reference to new TKR name reference.
    - Updates the Package secret names like capabilites, guest cluster auth service
      from old TKR reference to new TKR name reference.
    """
    cbt_data = ''
    with open(cbt_file, 'r') as fp:
        cbt_data = yaml.safe_load(fp)
    cbt_data["metadata"]["name"] = cbt_name
    for addon in ["cni", "cpi", "csi", "kapp"]:
        cbt_data["spec"][addon]["valuesFrom"]["providerRef"]["name"] = \
            cbt_data["spec"][addon]["valuesFrom"]["providerRef"]["name"].replace(old_tkr_name, new_tkr_name)
    for index in range(len(cbt_data["spec"]["additionalPackages"])):
        if "valuesFrom" in cbt_data["spec"]["additionalPackages"][index]:
            if "secretRef" in cbt_data["spec"]["additionalPackages"][index]["valuesFrom"]:
                cbt_data["spec"]["additionalPackages"][index]["valuesFrom"]["secretRef"] = \
                    cbt_data["spec"]["additionalPackages"][index]["valuesFrom"]["secretRef"].replace(old_tkr_name,
                                                                                                    new_tkr_name)
    with open(cbt_file, 'w') as fp:
        yaml.dump(cbt_data, fp)
    print("New CBT Name:", cbt_name)


def format_name(template, suffix, *default_values):
    """
    Creates a kubernetes object name with max name length(63) after
    appending the suffix string.
    """
    max_k8s_object_name_length = 63
    max_tkr_suffix_length = 8
    suffix = suffix[0:max_tkr_suffix_length]
    default_template_length = len(template.replace('{}', ''))
    total_length = default_template_length
    for string in default_values:
        total_length = total_length + len(string)
    max_tkr_suffix_length = max_k8s_object_name_length - total_length
    if max_tkr_suffix_length > len(suffix):
        max_tkr_suffix_length = len(suffix)
    suffix = suffix[0:max_tkr_suffix_length]
    return template.format(*default_values, suffix)


def render_folder_and_append(folder):
    """
    Creates a single JSON object after parses all files on a folder then
    applies the Jinja2 templating using jinja_args_map dictionary.
    """
    output = {}
    for filename in os.listdir(folder):
        if "versionManifest" in filename:
            continue
        file = os.path.join(folder, filename)
        with open(file, 'r') as fp:
            temp = Environment(loader=BaseLoader).from_string(fp.read())
            output.update(json.loads(temp.render(jinja_args_map)))
    return output


def render_default_config(args):
    packer_vars.update(render_folder_and_append(args.default_config_folder))

def check_photon3_stig_compliance():
    current_kubernetes_version = jinja_args_map["kubernetes_series"].replace('v', "")
    if semver.compare(current_kubernetes_version, "1.25.0") >= 0:
        jinja_args_map["photon3_stig_compliance"] = "true"

if __name__ == "__main__":
    main()
