# Building Windows Image Using the vSphere Tanzu Kubernetes Grid Image Builder

This tutorial describes how to use the vSphere Tanzu Kubernetes Grid Image Builder to build Windows OVA image for use with [vSphere Kubernetes Service 3.2](https://docs.vmware.com/en/VMware-vSphere/8/rn/vmware-tanzu-kubernetes-grid-service-release-notes/index.html) and above.

## Use case

I want to build a Windows Node Image to deploy a node pool for Windows container workloads in my guest cluster.

## Requirements

- Check the [prerequisites](https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-with-tanzu-installation-configuration/GUID-EE236215-DA4D-4579-8BEB-A693D1882C77.html)
- vCenter Server 8, which can be any vCenter 8 instance, it does not have to be the same vCenter managing your vSphere with Tanzu environment
- Packer requires the vSphere environment to have DHCP configured; you cannot use static IP address management
- A recent Windows Server 22H2 ISO image. Download through your Microsoft Developer Network (MSDN) or Volume Licensing (VL) account. The use of evaluation media is not supported or recommended.
- VMware Tools ISO Image
- A datastore on your vCenter that can accommodate your custom Windows VM template, which can have a starting size greater than 10GB (thin provisioned).

## Prepare for Image Builder

Follow the [standard tutorial](examples/tutorial_building_an_image.md) to prepare the environment for vSphere Tanzu Kubernetes Grid Image Builder.

## Get Windows Server and VMware Tools ISO

Windows Server 22H2 ISO image can be downloaded from Microsoft through your Microsoft Developer Network (MSDN) or Volume Licensing (VL) account.

VMware Tools can be downloaded via the [Broadcom Knowledge Base](https://knowledge.broadcom.com/external/article/315363/how-to-install-vmware-tools.html).

In this tutorial, we use Windows Server 22H2 `en-us_windows_server_2022_x64_dvd_620d7eac.iso` and `VMware-tools-windows-12.5.0-23800621.iso`.

### Install govc (Optional)

You may follow the [govc documentation](https://github.com/vmware/govmomi/blob/main/govc/README.md)
to install govc on the Linux VM you're building the image.

```bash
$ export GOVC_URL=[VC_URL]
$ export GOVC_USERNAME=[VC_USERNAME]
$ export GOVC_PASSWORD=[VC_PASSWORD]
$ export GOVC_INSECURE=1
$ export GOVC_DATACENTER=Datacenter
$ export GOVC_CLUSTER=Management-Cluster
$ export GOVC_DATASTORE=datastore22

$ govc datastore.upload --ds="$GOVC_DATASTORE" --dc="$GOVC_DATACENTER" en-us_windows_server_2022_x64_dvd_620d7eac.iso windows2022.iso
$ govc datastore.upload --ds="$GOVC_DATASTORE" --dc="$GOVC_DATACENTER" VMware-tools-windows-12.5.0-23800621.iso vmtools.iso
```

Alternatively, you may use the vCenter UI to upload the ISOs to the datastore.

## Prepare Windows setup answer file

You may customize the Windows Node Image with a [Windows setup answer file](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/update-windows-settings-and-scripts-create-your-own-answer-file-sxs?view=windows-11)

The upstream Windows setup answer file can be found at [image builder](https://raw.githubusercontent.com/kubernetes-sigs/image-builder/refs/heads/main/images/capi/packer/ova/windows/windows-2022-efi/autounattend.xml).

### Provision Administrative Account for Log Collection

In order for the Windows nodes to work with the [vSphere Kubernetes Service support bundle tool](https://knowledge.broadcom.com/external/article/345464/gathering-logs-for-vsphere-with-tanzu.html), you need to add an administrative account in the answer file.

The following snippet shows how to add an administrative account in the answer file.

```bash
$ curl https://raw.githubusercontent.com/kubernetes-sigs/image-builder/refs/heads/main/images/capi/packer/ova/windows/windows-2022-efi/autounattend.xml -o /home/image-builder/windows_autounattend.xml
$ vi /home/image-builder/windows_autounattend.xml
```

Locate the `LocalAccounts` in the xml and add a new `LocalAccount` to this section.

```xml
<LocalAccounts>
    <LocalAccount wcm:action="add">
        <Description>Administrator</Description>
        <DisplayName>Administrator</DisplayName>
        <Group>Administrators</Group>
        <Name>Administrator</Name>
    </LocalAccount>
    <LocalAccount wcm:action="add">
        <Password>
            <Value>MyAdminPassw0rd</Value>
            <PlainText>true</PlainText>
        </Password>
        <Description>For log collection</Description>
        <DisplayName>Admin Account</DisplayName>
        <Name>WindowsAdmin</Name>
        <Group>Administrators</Group>
    </LocalAccount>
</LocalAccounts>
```

You should alter the user name and password to comform to organizational policies.

## Update vsphere.j2 with vSphere Environment Details

The `vsphere.j2` file is a packer configuration file with vSphere environment details.

CD to the `vsphere-tanzu-kubernetes-grid-image-builder/packer-variables/` directory.

Update the `vsphere.j2` and `packer-variables/windows/vsphere-windows.j2` environment variables with details for your vCenter 8 instance.

```bash
$ vi vsphere.j2

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
    "create_snapshot": "true",
    {# To destroy Packer VM after Image Build is completed #}
    "destroy": "true"
}
```

```bash
vi packer-variables/windows/vsphere-windows.j2

{
    "os_iso_path": "[datastore22] windows2022.iso",
    "vmtools_iso_path": "[datastore22] vmtools.iso"
}
```

NOTE: You need to match the ISO image file names in the datastore.

## Select Kubernetes version

From the `vsphere-tanzu-kubernetes-grid-image-builder` directory where the Makefile is located run:

```bash
$ make list-versions
```

Windows container workload support is only available in Kubernetes release v1.31 and above.

## Run the Artifacts Container for the Selected Kubernetes Version

Usage:

```bash
$ make run-artifacts-container KUBERNETES_VERSION=<version>
```

Example:

```bash
$ make run-artifacts-container KUBERNETES_VERSION=v1.31.1+vmware.2-fips
```

## Run the Image Builder Application

Usage:

```bash
$ make build-node-image OS_TARGET=<os_target> KUBERNETES_VERSION=v1.31.1+vmware.2-fips TKR_SUFFIX=<tkr_suffix> HOST_IP=<host_ip> IMAGE_ARTIFACTS_PATH=<image_artifacts_path> ARTIFACTS_CONTAINER_PORT=8081
```

NOTE:
* The HOST_IP must be reachable from the vCenter.
* You need to use the Kubernetes version which supports Windows. You may check Windows is in the Supported OS from
the result from `make list-versions`.
* You may list the Kubernetes in your Supervisor cluster to get the version suffix.

```bash
$ kubectl get kr

NAME                                                                    VERSION                       READY   COMPATIBLE   CREATED   TYPE
kubernetesrelease.kubernetes.vmware.com/v1.31.1---vmware.2-fips-vkr.2   v1.31.1+vmware.2-fips-vkr.2   True    True         3h8m
```

Example:

```bash
$ make build-node-image OS_TARGET=windows-2022-efi KUBERNETES_VERSION=v1.31.1+vmware.2-fips TKR_SUFFIX=vkr.2 HOST_IP=192.2.2.3 IMAGE_ARTIFACTS_PATH=/home/image-builder/image ARTIFACTS_CONTAINER_PORT=8081 AUTO_UNATTEND_ANSWER_FILE_PATH=/home/image-builder/windows_autounattend.xml
```

## Verify the Custom Image

Locally the image is stored in the `/image/ovas` directory. For example, `/home/image-builder/image/ovas`.

The `/image/logs` directory contains the `packer-xxxx.log` file that you can use to troubleshoot image building errors.

To verify that image is built successfully, check vCenter Server.

You should see the image being built in the datacenter, cluster, folder that you specified in the vsphere.j2 file.

## Upload the Image to the vSphere Kubernetes Service Environment

Download the custom image from local storage or from the vCenter Server.

In your vSphere with Tanzu environment, create a local content library and upload the custom image there.

Refer to the documentation for [creating a local content library](https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-with-tanzu-tkg/GUID-19E8E034-5256-4EFC-BEBF-D4F17A8ED021.html) for use with vSphere Kubernetes Service.

You need to upload both Linux and Windows node images to the local content library as the Linux node image will be
used to deploy VMs for Kubernetes Control Plane and Linux node pools (if any).

Note: You should disable Security Policy for this content library for Windows image.

## Create a cluster with Windows Node Pool

You may refer to [vSphere Kubernetes Service 3.2 documentation]() for more information on how to deploy a cluster with Windows Node Pool with vSphere Kubernetes Service 3.2 and above.

## Known Issues for Windows Container Workload Support

### Kubernetes Release v1.31

* The minimum vmclass should be best-effort-large for Windows Worker Node 

  When a windows worker node is configured with a vm-class which has resource configuration lower than best-effort-large, some of the management pods may not run due to loss of network connectivity.

  Resolution: 
  Switch to a vmclass configured with more resources.

* Some Pods on Window Node's networking don't work correctly

  Some Pods on Window Node's networking don’t work correctly, which makes the Pod is not reachable, or the Pod can’t access other network peers.

  If searching in antrea-agent log from the corresponding antrea-agent Pod which locates on the same Node as the bad Pod, some logs records shall be found with the key words “Failed to execute postInterfaceCreateHook”, e.g.,

  ```bash
  kubectl logs -n kube-system -c antrea-agent antrea-agent-windows-stvgp | grep "Failed to execute postInterfaceCreateHook"

  E0921 04:38:39.289057 4364 interface_configuration_windows.go:488] "Failed to execute postInterfaceCreateHook" err="timed out: \"wait\" timed out after 5012 ms" interface="vEthernet (vsphere--ab7002)"
  ```

  If checking OVS port status, we may observe that a port is configured with error “could not add network device xxxxx to ofproto (Invalid argument)”, e.g.,

  ```bash
  kubectl exec -it -n kube-system antrea-agent-windows-znncw -- cmd.exe /c "C:\openvswitch\usr\bin\ovs-vsctl.exe show"
  3cc1a6d5-adc1-45d3-a336-c3c2b8203e77
      Bridge br-int
          datapath_type: system
          Port vsphere--c546b0
                Interface vsphere--c546b0
                    type: internal
                    error: "could not add network device vsphere--c546b0 to ofproto (Invalid argument)"
      ovs_version: "3.0.1.60555"
   ```

   Workaround:
   Kill the bad Pod using kubectl command to reschedule the Pod so that antrea-agent can re-program the networking for the Pod.

### Generic Known Issues

You may refer to [this link](https://docs.vmware.com/en/VMware-Tanzu-Kubernetes-releases/services/rn/vmware-tanzu-kubernetes-releases-release-notes/index.html) for generic known issues for vSphere Kubernetes Service.
