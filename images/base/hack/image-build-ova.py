#!/usr/bin/env python3

# Copyright (c) 2023 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http:#www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

################################################################################
# usage: image-build-ova.py [FLAGS] ARGS
#  This program builds an OVA file from a VMDK and manifest file generated as a
#  result of a Packer build.
################################################################################

import argparse
import hashlib
import json
import os
import io
import subprocess
from string import Template
import tarfile


def main():
    parser = argparse.ArgumentParser(
        description="Builds an OVA using the artifacts from a Packer build")
    parser.add_argument('--stream_vmdk',
                        dest='stream_vmdk',
                        action='store_true',
                        help='Compress vmdk file')
    parser.add_argument('--vmx',
                        dest='vmx_version',
                        default='15',
                        help='The virtual hardware version')
    parser.add_argument('--name',
                        dest='build_name',
                        default='vm-image',
                        help='The VM Name')
    parser.add_argument('--eula_file',
                        nargs='?',
                        metavar='EULA',
                        default='../../hack/ovf_eula.txt',
                        help='Text file containing EULA')
    parser.add_argument('--ovf_template',
                        nargs='?',
                        metavar='OVF_TEMPLATE',
                        default='../../hack/ovf_template.xml',
                        help='XML template to build OVF')
    parser.add_argument(dest='build_dir',
                        nargs='?',
                        metavar='BUILD_DIR',
                        default='.',
                        help='The Packer build directory')
    args = parser.parse_args()

    # Read in the EULA
    eula = ""
    with io.open(args.eula_file, 'r', encoding='utf-8') as f:
        eula = f.read()

    # Read in the OVF template
    ovf_template = ""
    with io.open(args.ovf_template, 'r', encoding='utf-8') as f:
        ovf_template = f.read()

    # Change the working directory if one is specified.
    os.chdir(args.build_dir)
    print("image-build-ova: cd %s" % args.build_dir)

    # Load the packer manifest JSON
    data = None
    with open('packer-manifest.json', 'r') as f:
        data = json.load(f)

    # Get the first build.
    build = data['builds'][0]
    build_data = build['custom_data']
    print("image-build-ova: loaded %s-%s" % (args.build_name,
                                             build_data['version']))

    # Get a list of the VMDK files from the packer manifest.
    vmdk_files = get_vmdk_files(build['files'], args.build_name)

    # Create stream-optimized versions of the VMDK files.
    if args.stream_vmdk is True:
        stream_optimize_vmdk_files(vmdk_files)
    else:
        for f in vmdk_files:
            f['stream_name'] = f['name']
            f['stream_size'] = os.path.getsize(f['name'])

    # Only get the first vmdk file
    vmdk = vmdk_files[0]

    OS_id_map = {"vmware-photon-64": {"id": "36", "version": "", "type": "vmwarePhoton64Guest"},
                 "centos7-64": {"id": "107", "version": "7", "type": "centos7-64"},
                 "centos8-64": {"id": "107", "version": "8", "type": "centos8-64"},
                 "rhel7-64": {"id": "80", "version": "7", "type": "rhel7_64guest"},
                 "rhel8-64": {"id": "80", "version": "8", "type": "rhel8_64guest"},
                 "ubuntu-64": {"id": "94", "version": "", "type": "ubuntu64Guest"},
                 "flatcar-64": {"id": "100", "version": "", "type": "linux-64"},
                 "Windows2019Server-64": {"id": "112", "version": "", "type": "windows9srv-64"},
                 "Windows2004Server-64": {"id": "112", "version": "", "type": "windows9srv-64"}}

    # Create the OVF file.
    ovf = "%s.ovf" % args.build_name
    create_ovf(ovf, {
        'BUILD_DATE': build_data['build_date'],
        'ARTIFACT_ID': build['artifact_id'],
        'BUILD_TIMESTAMP': build_data['build_timestamp'],
        'EULA': eula,
        'OS_NAME': build_data['os_name'],
        'OS_ID': OS_id_map[build_data['guest_os_type']]['id'],
        'OS_TYPE': OS_id_map[build_data['guest_os_type']]['type'],
        'OS_VERSION': OS_id_map[build_data['guest_os_type']]['version'],
        'DISK_NAME': vmdk['stream_name'],
        'DISK_SIZE': build_data['disk_size'],
        'POPULATED_DISK_SIZE': vmdk['size'],
        'PRODUCT': build_data['os_name'],
        'STREAM_DISK_SIZE': vmdk['stream_size'],
        'VMX_VERSION': args.vmx_version,
        'VERSION': build_data['version'],
        'DISTRO_NAME': build_data['distro_name'],
        'DISTRO_VERSION': build_data['distro_version'],
        'DISTRO_ARCH': build_data['distro_arch'],
        'NESTEDHV': "false",
    }, ovf_template)

    # Create the OVA manifest.
    ova_manifest = "%s.mf" % args.build_name
    create_ova_manifest(ova_manifest, [ovf, vmdk['stream_name']])

    # Create the OVA.
    ova = "%s.ova" % args.build_name
    create_ova(ova, [ovf, ova_manifest, vmdk['stream_name']])


def sha256(path):
    m = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            m.update(data)
    return m.hexdigest()


def create_ova(path, infile_paths):
    print("image-build-ova: create ova %s" % path)
    with open(path, 'wb') as f:
        with tarfile.open(fileobj=f, mode='w|') as tar:
            for infile_path in infile_paths:
                tar.add(infile_path)

    chksum_path = "%s.sha256" % path
    print("image-build-ova: create ova checksum %s" % chksum_path)
    with open(chksum_path, 'w') as f:
        f.write(sha256(path))


def create_ovf(path, data, ovf_template):
    print("image-build-ova: create ovf %s" % path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(Template(ovf_template).substitute(data))


def create_ova_manifest(path, infile_paths):
    print("image-build-ova: create ova manifest %s" % path)
    with open(path, 'w') as f:
        for i in infile_paths:
            f.write('SHA256(%s)= %s\n' % (i, sha256(i)))


def get_vmdk_files(inlist, name):
    outlist = []
    for f in inlist:
        if f['name'].endswith('.vmdk') and f['name'].startswith(name):
            outlist.append(f)
    return outlist


def stream_optimize_vmdk_files(inlist):
    for f in inlist:
        infile = f['name']
        infile_wo_suffix = infile.replace('-disk1', '', 1)
        outfile = infile_wo_suffix.replace('.vmdk', '.ova.vmdk', 1)
        if os.path.isfile(outfile):
            os.remove(outfile)
        args = [
            'vmware-vdiskmanager',
            '-r', infile,
            '-t', '5',
            outfile
        ]
        print("image-build-ova: stream optimize %s --> %s (1-2 minutes)" %
              (infile, outfile))
        subprocess.check_call(args)
        f['stream_name'] = outfile
        f['stream_size'] = os.path.getsize(outfile)

if __name__ == "__main__":
    main()
