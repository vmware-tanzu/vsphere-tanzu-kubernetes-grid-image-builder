# VMware Base Image Builder

VMware Base Image Builder leverages the existing Packer builder plug-ins for Fusion/vSphere and popular distro ISOs to build VM Service-compatible base images. It provides examples for building Ubuntu and Photon images that are compatible with VM Service.

Right now, VM service requires all VM images to include the VMware Tools (or [open source equivalent](https://docs.vmware.com/en/VMware-Tools/12.0.0/com.vmware.vsphere.vmwaretools.doc/GUID-8B6EA5B7-453B-48AA-92E5-DB7F061341D1.html)) package and uses `one` of the following to bootstrap the guest and its networking stack: 
1. Linux with [Cloud-Init](https://cloud-init.io/) v17.9-v21.2 with [DataSourceVMwareGuestInfo](https://github.com/vmware-archive/cloud-init-vmware-guestinfo)
2. Linux with [Cloud-Init](https://cloud-init.io/) v21.3+
3. Windows with [Cloudbase-Init](https://cloudbase.it/cloudbase-init/) v1.1.0+
4. OVF properties.

In this repository, we will provide examples to install Cloud-init and open-vm-tools on Ubuntu and Photon3. Note that Photon OS 4.0 Rev2 is already compatible with VM Service.

## Content
* [Requirements](#requirements)
* [Build](#build)
    * [Builder](#builder)
    * [Provisioner](#provisioner)
* [Deployment](#deployment)
* [Documentations](#documentations)


## Requirements
Building ova requires:
- [Packer](https://www.packer.io/downloads) >= 1.7.0
- [Ansible](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) >= 2.8
using `vmware-iso`: It currently supports building virtual machines on hosts running [VMware Fusion](https://www.vmware.com/products/fusion.html) for OS X, [VMware Workstation](https://www.vmware.com/products/workstation-pro.html) for Linux and Windows, and [VMware Player](https://www.vmware.com/products/workstation-player.html) on Linux.

```
# Make sure to include ovftool in PATH.
export PATH=$PATH:/Applications/VMware\ Fusion.app/Contents/Library/VMware\ OVF\ Tool
```

## Build
- Find your preferred image ISO url (supporting Local files, Git, Mercurial, HTTP, Amazon S3)
- Navigate to the directory according to your choice of image and builder (eg. [/packer/ova/](packer/ova/))
- Fill in necessary variables in json file
- Run `packer build <file-name>.json`
### Builder 
- [vmware-iso](https://www.packer.io/plugins/builders/vmware): Starts from an ISO file, creates a brand new VMware VM, installs an OS, provisions software within the OS, then exports that machine to create an image. This is best for people who want to start from scratch.
### Provisioner
- [Ansible](https://docs.ansible.com/ansible/latest/user_guide/index.html#getting-started)  can be used to provision the underlying infrastructure of your environment, virtualized hosts and hypervisors, network devices, and bare metal servers. It can also install services, add compute hosts, and provision resources, services, and applications inside of your cloud.

## ISO files
There are 2 ways of utilizing ISO files
### method 1: Passing in `iso_url` and `iso_checksum` directly
- `iso_url` (string) - A URL to the ISO containing the installation image or virtual hard drive (VHD or VHDX) file to clone.
- `iso_checksum` (string) - The checksum for the ISO file or virtual hard drive file. 

### method2: Download the Guest Operating Systems ISOs and upload it to ISO datastore in vCenter
- Step1: Download the x64 guest operating system `.iso` images. Details in [Ubuntu README.md](ubuntu/README.md).
- Step2:
Obtain the checksum type (e.g. sha256, md5, etc.) and checksum value for each guest operating system .iso image from the vendor. This will be used in the build input variables.
- Step3:
[Upload](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.storage.doc/GUID-58D77EA5-50D9-4A8E-A15A-D7B3ABA11B87.html) your guest operating system `.iso` images to the ISO datastore and paths that will be used in your variables.

`iso_paths` ([]string) - List of Datastore or Content Library paths to ISO files that will be mounted to the VM.
- example
```json
"variable":{
  "iso_path": "ISO/photon-4.0-1526e30ba.iso"
},
"builder":{
"iso_paths": [
        "[{{ user `datastore` }}] {{ user `iso_path` }}"
      ]
}
```
## Deployment
After building base images, you need to first upload the image to vCenter content library. 

Then you can attach the content library with your namespace and configure VM Class and storage policy.

Now you are ready to deploy a virtual machine using VM Service. Examples are as follows:
 
```yaml
apiVersion: vmoperator.vmware.com/v1alpha1
kind: VirtualMachine
metadata:
  name: <vm-name>
  namespace: <your namespace name>
spec:
  networkInterfaces:
  - networkName: ""
    networkType: nsx-t
  className: <VM Class name>
  imageName: <image name>
  powerState: poweredOn
  storageClass: <storage police>
  vmMetadata:
    configMapName: user-data-1
    transport: CloudInit
---
apiVersion: v1
kind: ConfigMap
metadata:
    name: user-data-1
    namespace: test-ns
data:
  user-data: |
    #cloud-config
    ssh_pwauth: true
    users:
      - name: vmware
        sudo: ALL=(ALL) NOPASSWD:ALL
        lock_passwd: false
        # Password set to Admin!23
        passwd: '$1$salt$SOC33fVbA/ZxeIwD5yw1u1'
        shell: /bin/bash
    write_files:
      - content: |
          VM Service Says Hello World
        path: /helloworld
```
## Documentations
For more Packer configuration reference:
- vmware-iso [VMware Builder (from ISO)](https://www.packer.io/plugins/builders/vmware/iso)
- vsphere-iso [Packer Builder for VMware vSphere](https://www.packer.io/plugins/builders/vsphere/vsphere-iso)



