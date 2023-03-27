# Tutorial for Using the VMware Image Builder

The VMware Image Builder uses Hashcorp Packer to generate images. Packer invokes vCenter APIs to create a VM from a TKR. 

## Requirements

- Check the [prerequisites](tkg#prerequisites)
- vCenter 8
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

CD to /tkg/packer-variables/

```
cp vsphere.j2 vsphere.j2-orig

```

Update the vsphere.j2 environment variables.

```
vi /tkg/packer-variables/vsphere.j2
```

---
{
    {# vCenter server IP or FQDN #}
    "vcenter_server":"10.197.79.141",
    {# vCenter username #}
    "username":"lparis@vsphere.local",
    {# vCenter user password #}
    "password":"wcp_9w1P^csS",
    {# Datacenter name where packer creates the VM for customization #}
    "datacenter":"Datacenter",
    {# Datastore name for the VM #}
    "datastore":"datastore51",
    {# [Optional] Folder name #}
    "folder":"",
    {# Cluster name where packer creates the VM for customization #}
    "cluster": "Management Cluster",
    {# Packer VM network #}
    "network": "PG-MGMT-VLAN-1060",
    {# To use insecure connection with vCenter  #}
    "insecure_connection": "true",
    {# TO create a clone of the Packer VM after customization#}
    "linked_clone": "true",
    {# To create a snapshot of the Packer VM after customization #}
    "create_snapshot": "true"
}
---

## Select Kuberentes version

```
make list-versions
```

## Run the artifacts container for the selected Kubernetes version

```
make run-artifacts-container KUBERNETES_VERSION=<version>
```

```
~/work/image-builder/images/tkg$  make run-artifacts-container KUBERNETES_VERSION=v1.24.9+vmware.1
```

## Run the image-builder


```
make build-node-image OS_TARGET=<os_target> KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=<tkr_suffix> ARTIFACTS_CONTAINER_IP=<artifacts_container_ip> IMAGE_ARTIFACTS_PATH=<image_artifacts_path> ARTIFACTS_CONTAINER_PORT=8081" to build node image
```

```
make build-node-image OS_TARGET=photon-3 KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=byoi ARTIFACTS_CONTAINER_IP=1.2.3.4 IMAGE_ARTIFACTS_PATH=/home/ubuntu/image ARTIFACTS_CONTAINER_PORT=8081
```

```
make build-node-image OS_TARGET=ubuntu-2004-efi KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=byoi ARTIFACTS_CONTAINER_IP=1.2.3.4 IMAGE_ARTIFACTS_PATH=/home/ubuntu/image ARTIFACTS_CONTAINER_PORT=8081
```

```
make build-node-image OS_TARGET=ubuntu-2004-efi KUBERNETES_VERSION=v1.24.9+vmware.1 TKR_SUFFIX=byoi ARTIFACTS_CONTAINER_IP=10.197.79.151 IMAGE_ARTIFACTS_PATH=/home/ubuntu/image ARTIFACTS_CONTAINER_PORT=8081
```