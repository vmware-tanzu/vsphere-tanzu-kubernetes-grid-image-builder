# Configuring the Packer HTTP port

As a customer, I want to configure the port or port range used by the Packer HTTP service during the Node Image build process.

## Backgroud

For unattended installation during the image build process photon preseed approach where the [kickstart](https://github.com/kubernetes-sigs/image-builder/blob/master/images/capi/packer/ova/linux/photon/http/3/ks.json) file is hosted by packer by starting an http server. Packer can use one of the opened ports between `8000` and `9000` by default.

## Customization

Packer HTTP server port can be configured using `http_port_max` and `http_port_min` packer variables.

- Only use ports between `8500` and `8550`. Create a new `packer-ports.json` file in [packer variables folder](./../../packer-variables/) with below contents

```JSON
{
    "http_port_max": "8500",
    "http_port_min": "8550"
}
```

- Specify a single port `8939`. Create a new `packer-ports.json` file in [packer variables folder](./../../packer-variables/) with below contents

```JSON
{
    "http_port_max": "8939",
    "http_port_min": "8939"
}
```
