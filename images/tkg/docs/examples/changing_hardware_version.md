# Changing the Hardware version

## Use case

As a customer, I want to change the Hardware version of the node image to use the latest hardware functionalities.

## Background

By default, node images use the hardware version(`VMX`) 17. Please refer to the below documents to learn more about the hardware version and its compatibility with the vSphere environment.

- [Hardware Features Available with Virtual Machine Compatibility Settings](https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-vm-administration/GUID-789C3913-1053-4850-A0F0-E29C3D32B6DA.html)
- [ESXi/ESX hosts and compatible virtual machine hardware versions list](https://kb.vmware.com/s/article/2007240)

## Customization

[Kubernetes Image Builder][kubernetes-image-builder] has a `vmx_version` packer variable through which the hardware version can be configured. Edit the `vmx_version` filed in the [default-args.j2][default-args] present in [packer variables](./../../packer-variables/) folder with the appropriate hardware version and build the image

```text
    "vmx_version": "17",
```

[//]: Links

[default-args]: [./../../../packer-variables/default-args.j2]
[kubernetes-image-builder]: https://github.com/kubernetes-sigs/image-builder/
