# Ansible Configuration Documentation

## Project Overview

Infrastructure automation for home lab environment including Ubuntu servers,
Raspberry Pi devices, Proxmox VE hosts, LXC containers, and Kubernetes
clusters.

## Directory Structure

```text
ansible/
├── inventories/hosts.yml   # Main inventory with host groups and variables
├── playbooks/             # Ansible playbooks
│   ├── ssh/               # SSH host configuration and updates
│   │   ├── common-*.yaml  # Group playbooks (apply common role)
│   │   └── host-*.yaml    # Host-specific playbooks
│   ├── k3s/               # Kubernetes application updates
│   │   └── update-app.yaml # Unified update playbook
│   ├── esphome/           # ESPHome device firmware updates
│   └── ops-*.yaml         # Operational tasks
├── roles/                 # Ansible roles
│   ├── backup/            # Backup server configuration
│   ├── common/            # Shared config (packages, users, mounts, rsyslog)
│   ├── llm/               # GPU server setup (NVIDIA, Docker, Ollama, Open WebUI)
│   ├── rpi/               # Raspberry Pi (NUT, Wyoming satellite)
│   ├── samba/             # Samba file server configuration
│   ├── ui-network/        # UniFi Network controller
│   └── ui-protect/        # UniFi Protect
├── tasks/                 # Reusable task files
│   ├── k3s-update-*.yaml  # K3s deployment task files
│   ├── esphome-*.yaml     # ESPHome task files
│   └── ops-upgrade-cluster-*.yaml # Cluster upgrade tasks
├── files/                 # Static files and configuration templates
│   └── k3s-config/        # Git submodule with Kubernetes manifests
├── inventories/          # Inventory and group variables
│   ├── hosts.yml         # Host inventory
│   └── group_vars/       # Group-specific variables
│       └── all/
│           ├── common.yml           # Common variables
│           ├── k3s_applications.yml # K3s application definitions
│           └── vault.yml            # Encrypted secrets (ansible-vault)
├── host_vars/            # Host-specific variables
└── ansible.cfg           # Ansible configuration
```

## Host Groups

### Infrastructure Groups

- **`ubuntu`** - Ubuntu servers (ui-network, backup, dev, adambalm)
- **`rpi`** - Raspberry Pi devices (rockyledge, morgspi, mudderpi, probepi,
  magpi)
- **`k3s_prod`** - Kubernetes production cluster nodes (k3s-prod-11,
  k3s-prod-12, k3s-prod-13, k3s-prod-15)
- **`pve`** - Proxmox VE hosts (pve11, pve12, pve13, pve15)
- **`lxc`** - LXC containers (smb)
- **`ui_protect`** - UniFi Protect (ui-protect)

### Service-Based Organization

Uses `services` host variable to define what runs on each host:

```yaml
morgspi:
  services: ['nut', 'homeassistant']
mudderpi:
  services: ['nut', 'homeassistant']
rockyledge:
  services: ['nut']
```

## Key Playbooks

### Group Playbooks (`common-*`)

Apply common configuration to host groups:

- **`ssh/common-ubuntu.yaml`** - Ubuntu servers group
- **`ssh/common-k3s-prod.yaml`** - K3s production cluster nodes
- **`ssh/common-pve.yaml`** - Proxmox VE hypervisors
- **`ssh/common-lxc.yaml`** - LXC containers
- **`ssh/common-rpi.yaml`** - Raspberry Pi servers (includes service-based
  configuration)

### Host Playbooks (`host-*`)

Configure specific individual servers:

- **`ssh/host-adambalm.yaml`** - GPU server for AI/ML workloads (common + optional llm)
- **`ssh/host-backup.yaml`** - Backup server (common + backup)
- **`ssh/host-dev.yaml`** - Development server (common only)
- **`ssh/host-smb.yaml`** - SMB/Samba file server (common + samba)
- **`ssh/host-ui-network.yaml`** - UniFi Network controller (common + ui-network)
- **`ssh/host-ui-protect.yaml`** - UniFi Protect (ui-protect)

### Operational Playbooks

- **`ops-maintenance-mode.yaml`** - Alert management (Graylog, Alertmanager,
  Uptime Kuma)
- **`ops-upgrade-cluster.yaml`** - Cluster upgrade orchestration
- **`ops-proxmox-maintenance-on.yaml`** - Proxmox maintenance mode
- **`ops-proxmox-migrate-vm.yaml`** - Proxmox VM migration
- **`ops-cloudflare-clear-acme.yaml`** - Cloudflare ACME cleanup
- **`ops-host-reboot.yaml`** - Host reboot management

### K3s Playbooks

- **`k3s/update-app.yaml`** - Unified update playbook (routes by deployment
  method)
- **`k3s/update-cnpg-operator.yaml`** - CloudNative-PG operator update wrapper
- **`k3s/update-mongodb-crd-manifests.yaml`** - MongoDB CRD manifest management
- **`k3s/backup-uptime-kuma.yaml`** - Uptime Kuma database backup

### Task Organization

Reusable task files in `tasks/`:

- **K3s deployment tasks**:
  - `k3s-update-helm.yaml` - Helm chart deployments
  - `k3s-update-manifest.yaml` - Single manifest deployments
  - `k3s-update-manifest-multi.yaml` - Multi-instance manifest deployments
  - `k3s-update-manifest-cnpg.yaml` - CloudNative-PG manifest deployments
  - `k3s-update-manifest-multi-cnpg.yaml` - Multi-instance CNPG deployments
  - `k3s-update-rollout-restart.yaml` - Rollout restart deployments
- **ESPHome tasks**:
  - `esphome-discover-devices.yaml` - Device discovery
  - `esphome-upgrade-devices.yaml` - Device firmware upgrades
- **Cluster upgrade tasks** (`ops-upgrade-cluster-*`):
  - Alert management (graylog, alertmanager, uptime-kuma)
  - Ceph noout management
  - CNPG maintenance mode
  - Node drain and health checks
  - K3s, Proxmox, and VM operations
  - Paired node upgrade orchestration

## Host Variables and Conditionals

### Service-Based Conditionals

```yaml
when: "'nut' in (services | default([]))"
when: "'homeassistant' in (services | default([]))"
```

### Group-Based Conditionals

```yaml
when: inventory_hostname in groups['k3s_prod']
when: inventory_hostname in groups['ubuntu'] or
      inventory_hostname in groups['k3s_prod']
```

### Security Exclusions

```yaml
# Exclude shared/untrusted host
when: ansible_hostname != 'adambalm'
```

## Storage and Mounts

### SMB Mounts

- **Media**: `/mnt/smb_media` - Available on all hosts (except adambalm)
- **Kopia-HDD**: `/mnt/kopia-hdd` - Only on k3s_prod hosts

### Ceph Mounts (k3s_prod only)

- `/mnt/k3s-prod-data` - Production Kubernetes data
- `/mnt/k3s-lab-data` - Lab Kubernetes data
- `/mnt/homes` - User home directories
- `/mnt/kopia-ssd` - SSD backup storage
- `/mnt/backups` - General backup storage

## Security

### Vault Management

- Secrets stored in `inventories/group_vars/all/vault.yml` (encrypted with
  ansible-vault)
- Vault password stored in `~/.ansible/.vault-pass` (default location)
- SSH keys, passwords, and credentials all encrypted
- Vault variables automatically loaded for all playbooks

### User Management

- Creates `dang` user with sudo privileges (NOPASSWD)
- SSH public key deployment
- Shell configuration (zsh + oh-my-zsh)

### Access Control

- Root access for system tasks (`become: true`)
- User-specific tasks run as `dang` user (`become: false`,
  `remote_user: dang`)
- Sensitive operations excluded from `adambalm` host

## Operational Features

### Automatic Reboot Detection

Raspberry Pi playbook includes automatic reboot handling:

```yaml
- name: Check if reboot is required
  stat:
    path: /var/run/reboot-required
- name: Reboot if required
  reboot:
  when: reboot_required_file.stat.exists
```

### Service Management

- Handlers for service restarts (rsyslog, nut-server, nut-monitor)
- Systemd daemon reload capabilities
- Conditional service installation based on host services

### Backup Automation

- Home Assistant backup cron jobs (morgspi, mudderpi)
- Service-specific backup configurations

## Common Patterns

### Multi-Play Structure

Playbooks often have multiple plays:

1. System-level tasks (`become: true`)
2. User-level tasks (`become: false`, `remote_user: dang`)
3. Service-specific tasks with conditionals

### Package Management

- Update cache before installations
- Dist-upgrade with cleanup (autoclean, autoremove)
- Virtual machine detection for specific packages

### Configuration Management

- Template and file deployment from `files/` directory
- Handlers for service restarts after config changes
- Encrypted file deployment with proper permissions
