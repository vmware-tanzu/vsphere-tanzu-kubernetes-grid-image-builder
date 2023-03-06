# Adding new OS packages and configuring the repositories or sources

## Use case

As a user I want to

1. Add new OS packages such as `pkg1` and `pkg2`.
2. Configure sources/repositories to an internal mirror to build the node images in an air-gapped scenario. Configuring new sources/repositories is also useful when we want to install internally built software.

## Customization

Configuration of OS packages and sources/repositories is exposed as packer variables. To view a list of packer variables exposed by [kubernetes image builder][kubernetes-image-builder] please refer to this [page][customizations-doc].

### Adding new packages

To add new packages [kubernetes image builder][kubernetes-image-builder] provides `extra_rpms` and `extra_debs` packer variables for Photon and Ubuntu respectively. To add new packages, add the packages to the packer variables in the [default-args.j2][default-args] file as shown below.

_**Note**: If you are building just the Ubuntu OS node image you will not have to modify the photon OS block._

```jinja
    {% if os_type == "photon-3" %}
    "distro_version": "3.0",
    "extra_rpms": "existing_packages pkg1 pkg2"
    {% elif os_type == "ubuntu-2004-efi" %}
    "extra_debs": "existing_packages pkg1 pkg2",
    "boot_disable_ipv6": "1"
    {% endif %}
```

### Configuring new sources/repositories

[kubernetes image builder][kubernetes-image-builder] provides `extra_repos` packer variables through which sources/repositories can be configured for both Photon and Ubuntu. As there is a difference in how Ubuntu/Photon sources are configured we need to have separate source files for Photon/Ubuntu.

- Create new folder `repos` in [ansible files](./../../../ansible/files/) folder
- Create a new file for Photon sources called `photon.repo` in the `repos` folder. Refer below for sample content and refer to the official Photon [document][photon-repo-doc] for more information

```text
[photon]
name=VMware Photon Linux $releasever ($basearch)
baseurl=<internal_mirror_url>/$releasever/photon_release_$releasever_$basearch
gpgkey=<gpg_key>
gpgcheck=1
enabled=1

[photon-updates]
name=VMware Photon Linux $releasever ($basearch) Updates
baseurl=<internal_mirror_url>/$releasever/photon_updates_$releasever_$basearch
gpgkey=<gpg_key>
gpgcheck=1
enabled=1

[photon-extras]
name=VMware Photon Extras $releasever ($basearch)
baseurl=<internal_mirror_url>/$releasever/photon_extras_$releasever_$basearch
gpgkey=<gpg_key>
gpgcheck=1
enabled=1
```

- Create a new file for Ubuntu sources called `ubuntu.list` in the `repos` folder. Refer to the official ubuntu [documentation][ubuntu-sources-doc] for more information.
  - _**Note**: `focal` is for ubuntu 20.04 so this needs to be changed if the ubuntu version is also changed example for ubuntu 22.04 it is `jammy`_

```text
deb <internal_source_url> focal main restricted universe
deb <internal_source_url> focal-security main restricted
deb <internal_source_url> focal-updates main restricted
```

- Create a new file `repos.j2` or `repos.json` in [packer-variables](./../../packer-variables/) folder for configuring the `extra_repos` packer variable folder. (Uses [jinja][jinja] templating)

```jinja
{
    {% if os_type == "photon-3" %}
    "extra_repos": "/image-builder/images/capi/image/ansible/files/repos/photon.repo"
    {% elif os_type == "ubuntu-2004-efi" %}
    "extra_repos": "/image-builder/images/capi/image/ansible/files/repos/ubuntu.list"
    {% endif %}
}
```

### Disabling public repositories/sources

For disabling public repos set the `disable_public_repos` packer variable to `true` in the `repos.j2` file.

### Removing the extra repositories/sources

To remove the extra repositories/sources that were configured during the image build process set the `remove_extra_repos` packer variable to `true`.

```jinja
{
    "disable_public_repos": true,
    "remove_extra_repos": true
    {% if os_type == "photon-3" %}
    "extra_repos": "/image-builder/images/capi/image/ansible/files/repos/photon.repo"
    {% elif os_type == "ubuntu-2004-efi" %}
    "extra_repos": "/image-builder/images/capi/image/ansible/files/repos/ubuntu.list"
    {% endif %}
}
```

[//]: Links

[ansible-files]: [./../../../ansible/files/]
[customizations-doc]: https://image-builder.sigs.k8s.io/capi/capi.html#customization
[default-args]: [./../../../packer-variables/default-args.j2]
[jinja]: https://jinja.palletsprojects.com/en/3.1.x/
[kubernetes-image-builder]: https://github.com/kubernetes-sigs/image-builder/
[photon-repo-doc]: https://vmware.github.io/photon/assets/files/html/3.0/photon_admin/adding-a-new-repository.html
[ubuntu-sources-doc]: https://manpages.ubuntu.com/manpages/focal/man5/sources.list.5.html
