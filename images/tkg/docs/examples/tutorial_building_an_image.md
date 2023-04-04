# Tutorial for Using the VMware Image Builder

The VMware Image Builder uses Hashcorp Packer to generate images. Packer invokes vCenter APIs to create a VM from a TKR. 

## Requirements

- Check the [prerequisites](tkg#prerequisites)
- vCenter 8 (can be any vCenter 8 instance, does not have to be the vCenter managing vSphere with Tanzu)
- Packer requires the vSphere environment to have DHCP configured; you cannot use static IP address management
- Tutorial uses Ubuntu v1.22 to generate the image

## Install Docker

The VMware Image Builder runs components as Docker images to generate VMs.

Docker requires a 64-bit system with a Linux kernel having version 3.10 or newer. 

Use the `uname` command to check the version of your kernel:

```
~$ uname -r
```

Docker provides a convenience script to install the latest version of Docker for testing, dev and lab purposes. 

```
~$ wget -qO- https://get.docker.com/ | sh
```

Remove the need for sudo execution of docker commands.  

```
sudo usermod -aG docker $(whoami)
```

Log out of the shell and log back in.

```
exit
```

Check if you can invoke the Docker client without sudo.

```
docker –-version || docker -v
```

Verify that the Docker daemon (dockerd engine) is running using the system service interface system.

```
systemctl status --full docker
```

## Install JQ

```
sudo apt install -y jq
```

```
jq --version
```

## Install Make

```
sudo apt install make
```

```
make --version
```

## Update vsphere.j2 with vSphere environment details

CD to /tkg/packer-variables/.

Create a copy of the original variables file.

```
cp vsphere.j2 vsphere.j2-orig

```

Update the vsphere.j2 environment variables.

```
vi vsphere.j2
```

---
{
    {# vCenter server IP or FQDN #}
    "vcenter_server":"xx.xxx.xx.xxx",
    {# vCenter username #}
    "username":"user@vsphere.local",
    {# vCenter user password #}
    "password":"PASSWORD",
    {# Datacenter name where packer creates the VM for customization #}
    "datacenter":"Datacenter",
    {# Datastore name for the VM #}
    "datastore":"datastoreName",
    {# [Optional] Folder name #}
    "folder":"",
    {# Cluster name where packer creates the VM for customization #}
    "cluster": "Management Cluster",
    {# Packer VM network #}
    "network": "PG-MGMT-VLAN-1050",
    {# To use insecure connection with vCenter  #}
    "insecure_connection": "true",
    {# TO create a clone of the Packer VM after customization#}
    "linked_clone": "true",
    {# To create a snapshot of the Packer VM after customization #}
    "create_snapshot": "true"
}
---

## Select Kubernetes version

```
make list-versions
```

## Run the artifacts container for the selected Kubernetes version

```
make run-artifacts-container KUBERNETES_VERSION=<version>
```

For example:

```
~/work/image-builder/images/tkg$  make run-artifacts-container KUBERNETES_VERSION=v1.24.9+vmware.1
```

## Run the image-builder


```
make build-node-image OS_TARGET=<os_target> KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=<tkr_suffix> ARTIFACTS_CONTAINER_IP=<artifacts_container_ip> IMAGE_ARTIFACTS_PATH=<image_artifacts_path> ARTIFACTS_CONTAINER_PORT=8081" to build node image
```

For example:

```
make build-node-image OS_TARGET=ubuntu-2004-efi KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=byoi ARTIFACTS_CONTAINER_IP=xx.xxx.xx.xxx IMAGE_ARTIFACTS_PATH=/home/ubuntu/image ARTIFACTS_CONTAINER_PORT=8081
```

## Verify the image

Check vCenter. You should see the image being built.

## Customize the image

Refer to the customization examples.

## Upload the image to vSphere with Tanzu

Create a local content library and upload the custom image there.