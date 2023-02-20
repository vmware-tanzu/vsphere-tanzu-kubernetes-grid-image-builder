# vSphere Tanzu Node Image Builder

The Image Builder provides tooling that can be used to build node images to use with [vSphere Tanzu](https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-with-tanzu-concepts-planning/GUID-70CAF0BB-1722-4526-9CE7-D5C92C15D7D0.html).

## Prerequisites

vSphere Environment and Docker on a Linux environment are required for building these images

- vSphere Environment version >= 8.0
- Linux environment should have the below utilities available on the system
  - [Docker](https://www.docker.com/)
  - [GNU Make](https://www.gnu.org/software/make/)
  - [jq](https://stedolan.github.io/jq/)

## Building

- vSphere Tanzu team generates an artifacts container image for a particular Kubernetes release and publishes it to the image registry.
  - artifacts container hosts(NGINX server) all the required Carvel packages and other files for building the Image.
- The customer needs to create an artifacts container before building the actual container.
  - Use `make list-versions` to list supported Kubernetes versions and a separate make target to start the artifacts container(`make run-artifacts-container`).
- Update the vSphere environment details like vCenter IP, Username, Password etc. in [vsphere.j2](packer-variables/vsphere.j2)
- Start the image-builder container to build the node image(use `make build-node-image` target).
  - When building photon images make sure to open ports from `8000` to `9000` or else create a JSON file with the below contents in the [packer-variables] folder(With this configuration only port `8039` needs to be opened) on the system where the image builder container is running.

  ```JSON
  {
    "http_port_max": "8039",
    "http_port_min": "8039"
  }
  ```

- Once the OVA is generated create a [local content library](https://docs.vmware.com/en/VMware-vSphere/7.0/com.vmware.vsphere.vm_admin.doc/GUID-2A0F1C13-7336-45CE-B211-610D39A6E1F4.html) and import the OVA.
- To clean the container use `make clean`.

## Supported Kubernetes Versions

`supported-versions.json` holds information about the supported Kubernetes versions and their corresponding supported OS targets along with the artifacts container image URL.

Below are the supported Kubernetes versions

- **v1.22.13+vmware.1**

## Make targets

### Help

- `make help` Provides help information about different make targets

```bash
make
make help
```

- `make list-versions` gives information about supported Kubernetes versions and the corresponding OS targets

```bash
make list-versions PRINT_HELP=y # To show the help information for this target.
make list-versions              # Retrieves information from supported-versions.json file.
```

### Clean

There are three different clean targets to clean the containers or artifacts generated during the process or both.

- `make clean-containers` is used to stop/remove the artifacts or image builder or both.
  - During the container creation all of the containers will have `byoi` label
    - artifacts container will have `byoi_artifacts` and Kubernetes version as labels.
    - image builder container will have `byoi_image_builder`, Kubernetes version and os target as labels

```bash
make clean-containers PRINT_HELP=y         # To show the help information for this target
make clean-containers                      # To clean all the artifacts and image-builder containers
make clean-containers LABEL=byoi_artifacts # To remove artifact containers
```

- `make clean-image-artifacts` is used to remove the image artifacts like OVA's and packer log files

```bash
make clean-image-artifacts PRINT_HELP=y                           # To show help information for this target
make clean-image-artifacts IMAGE_ARTIFACTS_PATH=/root/artifacts/  # To clean the image artifacts in a folder
```

- `make clean` is a combination of `clean-containers` and `clean-image-artifacts` that cleans both containers and image artifacts

```bash
make clean PRINT_HELP=y                                                   # To show the help information for this target
make clean IMAGE_ARTIFACTS_PATH=/root/artifacts/                          # To clean image artifacts and containers
make clean IMAGE_ARTIFACTS_PATH=/root/artifacts/ LABEL=byoi_image_builder # To clean image artifacts and image builder containers
```

### Image Building

- `make run-artifacts-container` is used to run the artifacts container for a Kubernetes version at a particular port
  - artifacts image URL will be fetched from the [supported-versions.json](supported-versions.json) based on the Kubernetes version selected.
  - By default artifacts container will use 8080 port but this can be configured through `ARTIFACTS_CONTAINER_PORT` parameter.

```bash
make run-artifacts-container PRINT_HELP=y                                                       # To show the help information for this target
make run-artifacts-container KUBERNETES_VERSION=v1.22.13+vmware.1 ARTIFACTS_CONTAINER_PORT=9090 # To run 1.22.13 kubernetes artifacts container on port 9090
```

- `make build-container` is used to build the image builder container locally with all the dependencies like `Packer`, `Ansible` and `OVF Tool`.

```bash
make build-image-builder-container PRINT_HELP=y # To show the help information for this target.
make build-image-builder-container              # To create the image builder container.
```

- `make build-node-image` is used to build the vSphere Tanzu compatible node image for a Kubernetes version.
  - Artifacts container IP is required to pull the required Carvel Packages during the image build process and the default artifacts container port is 8080 which can be configured through `ARTIFACTS_CONTAINER_PORT`.
  - TKR(Tanzu Kubernetes Release) Suffix is used to distinguish images built on the same version for a different purpose. Maximum suffix length can be 8 characters.

```bash
make build-node-image PRINT_HELP=y # To show the help information for this target.
make build-node-image OS_TARGET=photon-3 KUBERNETES_VERSION=v1.23.15+vmware.1 TKR_SUFFIX=byoi ARTIFACTS_CONTAINER_IP=1.2.3.4 IMAGE_ARTIFACTS_PATH=/Users/kosarajud/image ARTIFACTS_CONTAINER_PORT=9090 # Create photon-3 1.23.15 kubernetes node image
```

## Customizations

Sample customization examples can be found [here](docs/samples/README.md)

## Debugging

- To enable debugging for the [make file scripts](hack/make-helpers/) export `DEBUGGING=true`.
- Debug logs are enabled by default on the image builder container which can be viewed through `docker logs -f <container_name>` command.
- Packer logs can be found at `<artifacts-folder>/logs/packer-<random_id>.log` which will be helpful when debugging issues.
