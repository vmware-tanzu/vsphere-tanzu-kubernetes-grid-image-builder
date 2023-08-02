# Tutorial for Using the vSphere Tanzu Kubernetes Grid Image Builder

This tutorial describes how to use the vSphere Tanzu Kubernetes Grid Image Builder to build a custom TKR for use with TKG 2 on Supervisor in the vSphere with Tanzu environment.

The vSphere Tanzu Kubernetes Grid Image Builder uses Hashicorp Packer to generate images. Packer invokes vCenter APIs to create a VM from a TKR.

## Requirements

- Check the [prerequisites](tkg#prerequisites)
- vCenter Server 8, which can be any vCenter 8 instance, it does not have to be the same vCenter managing your vSphere with Tanzu environment
- Packer requires the vSphere environment to have DHCP configured; you cannot use static IP address management
- Tutorial uses Ubuntu v1.22 to generate the image

## Clone the Repository

Clone the vSphere Tanzu Kubernetes Grid Image Builder repository on the Linux VM where you are building the image.

```bash
git clone https://github.com/vmware-tanzu/vsphere-tanzu-kubernetes-grid-image-builder.git
```

## Install Docker

The vSphere Tanzu Kubernetes Grid Image Builder runs components as Docker images to generate VMs.

Docker requires a 64-bit system with a Linux kernel having version 3.10 or newer.

Use the `uname` command to check the version of your kernel:

```bash
uname -r
```

Docker provides a convenience script to install the latest version of Docker for testing, dev and lab purposes.

```bash
wget -qO- https://get.docker.com/ | sh
```

Remove the need for sudo execution of docker commands.  

```bash
sudo usermod -aG docker $(whoami)
```

Log out of the shell and log back in.

```bash
exit
```

Check if you can invoke the Docker client without sudo.

```bash
docker --version
```

Verify that the Docker daemon (dockerd engine) is running using the system service interface system.

```bash
systemctl status --full docker
```

## Install JQ

Install:

```bash
sudo apt install -y jq
```

Verify:

```bash
jq --version
```

## Install Make

Install:

```bash
sudo apt install make
```

Verify:

```bash
make --version
```

## Update vsphere.j2 with vSphere Environment Details

The `vsphere.j2` file is a packer configuration file with vSphere environment details.

CD to the `vsphere-tanzu-kubernetes-grid-image-builder/packer-variables/` directory.

Update the vsphere.j2 environment variables with details for your vCenter 8 instance.

```bash
vi vsphere.j2
```

For example:

```bash
{
    {# vCenter server IP or FQDN #}
    "vcenter_server":"192.2.2.2",
    {# vCenter username #}
    "username":"user@vsphere.local",
    {# vCenter user password #}
    "password":"ADMIN-PASSWORD",
    {# Datacenter name where packer creates the VM for customization #}
    "datacenter":"Datacenter",
    {# Datastore name for the VM #}
    "datastore":"datastore22",
    {# [Optional] Folder name #}
    "folder":"",
    {# Cluster name where packer creates the VM for customization #}
    "cluster": "Management-Cluster",
    {# Packer VM network #}
    "network": "PG-MGMT-VLAN-1050",
    {# To use insecure connection with vCenter  #}
    "insecure_connection": "true",
    {# TO create a clone of the Packer VM after customization#}
    "linked_clone": "true",
    {# To create a snapshot of the Packer VM after customization #}
    "create_snapshot": "true"
}
```

## Select Kubernetes version

From the `vsphere-tanzu-kubernetes-grid-image-builder` directory where the Makefile is located run:

```bash
make list-versions
```

## Run the Artifacts Container for the Selected Kubernetes Version

Usage:

```bash
make run-artifacts-container KUBERNETES_VERSION=<version>
```

Example:

```bash
make run-artifacts-container KUBERNETES_VERSION=v1.24.9+vmware.1
```

## Run the Image Builder Application

Usage:

```bash
make build-node-image OS_TARGET=<os_target> KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=<tkr_suffix> HOST_IP=<host_ip> IMAGE_ARTIFACTS_PATH=<image_artifacts_path> ARTIFACTS_CONTAINER_PORT=8081
```

NOTE: The HOST_IP must be reachable from the vCenter.

Example:

```bash
make build-node-image OS_TARGET=ubuntu-2004-efi KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=byoi HOST_IP=192.2.2.3 IMAGE_ARTIFACTS_PATH=/home/ubuntu/image ARTIFACTS_CONTAINER_PORT=8081
```

## Verify the Custom Image

Locally the image is stored in the `/image/ovas` directory. For example, `/home/ubuntu/image/ovas`.

The `/image/logs` directory contains the `packer-xxxx.log` file that you can use to troubleshoot image building errors.

To verify that image is built successfully, check vCenter Server.

You should see the image being built in the datacenter, cluster, folder that you specified in the vsphere.j2 file.

## Customize the image

Refer to the customization examples.

## Upload the Image to the TKG 2 with Supervisor Environment

Download the custom image from local storage or from the vCenter Server.

In your vSphere with Tanzu environment, create a local content library and upload the custom image there.

Refer to the documentation for [creating a local content library](https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-with-tanzu-tkg/GUID-19E8E034-5256-4EFC-BEBF-D4F17A8ED021.html) for use with TKG with Supervisor.

To use the custom TKR, configure the vSphere Namespace to use the local content library.
