# Running Prometheus node exporter service on the nodes

## Use case

I want to monitor the nodes using the hardware and OS metrics exposed by Prometheus [Node Exporter](https://prometheus.io/docs/guides/node-exporter/).

## Customization

For this we will create a new ansible task that will create and configure the node exporter service.

- Create unit file for the new service `node_exporter.service` in [ansible files](./../../ansible/files/) folder.

```text
[Unit]
Description=Prometheus Node Exporter
Documentation=https://github.com/prometheus/node_exporter
After=network-online.target

[Service]
User=root
ExecStart=/opt/node_exporter/node_exporter
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target

```

- Create new variables in the [main.yml](./../../ansible/defaults/main.yml) for configuring where to pull the service binary and the version

```yaml
node_exporter_url: "https://github.com/prometheus/node_exporter/releases/download/v{{ node_exporter_version }}/node_exporter-{{ node_exporter_version }}.linux-amd64.tar.gz"
node_exporter_binary: "node_exporter-{{ node_exporter_version }}.linux-amd64"
node_exporter_location: /opt/node_exporter
node_exporter_tar: /tmp/node_exporter.tar.gz
```

- `node_exporter_version` is a ansible variable that can be passed through the `node_exporter_version` packer variable present in [default-args.j2](./../../packer-variables/default-args.j2)

```text
    "ansible_user_vars": "<existing_values_snip> node_exporter_version=1.4.0 ",
```

- Open the `9100` for the service (For external services to pull the metrics). Edit the [iptables.rules](./../../ansible/files/iptables.rules)

```text
-A INPUT -p tcp -m multiport --dports 6443,10250,2379,2380,179,22,10349,10350,10351,10100,9100 -j ACCEPT
```

- Create the ansible task(`node_exporter.yaml`) for creating the service in [ansible tasks](./../../ansible/tasks/) folder

```yaml
- name: Download Prometheus node exporter tar file
  get_url:
    url: "{{ node_exporter_url }}"
    dest: "{{ node_exporter_tar }}"

- name: Extracting the Node Exporter binary
  unarchive:
    src: "{{ node_exporter_tar }}"
    remote_src: yes
    dest: /tmp/

- name: Create node exporter directory
  file:
    path: "{{ node_exporter_location }}"
    state: directory

- name: Renaming node exporter binrary
  command: mv "/tmp/{{ node_exporter_binary }}/node_exporter" "{{ node_exporter_location }}/"

- name: Create node exporter unit file
  copy:
    src: files/node_exporter.service
    dest: /etc/systemd/system/node_exporter.service
    mode: 0644

- name: Enable node exporter service
  systemd:
    name: node_exporter
    daemon_reload: yes
    enabled: yes

- name: Start node_exporter, if not started
  service:
    name: node_exporter
    state: started
```

- Edit [main.yml](./../../ansible/tasks/main.yml) for adding the tasks to the ansible role.

```yaml
# At the end of the file
- import_tasks: node_exporter.yml
```
