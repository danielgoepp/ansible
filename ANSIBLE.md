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
│   ├── setup-*.yaml       # Initial system setup
│   ├── ops-*.yaml         # Operational tasks
│   └── linux-*.yaml       # Linux-specific configurations
├── tasks/                 # Reusable task files
│   ├── setup-global-*.yaml    # Global system configuration tasks
│   ├── setup-rpi-*.yaml       # Raspberry Pi specific tasks
│   └── tasks-*.yaml           # Legacy task files
├── files/                 # Static files and encrypted secrets
├── group_vars/           # Group-specific variables
│   └── vault.yaml.secret # Encrypted secrets (ansible-vault)
├── host_vars/            # Host-specific variables
├── vars/                 # Additional variable files
└── ansible.cfg           # Ansible configuration
```

## Host Groups

### Infrastructure Groups

- **`ubuntu`** - Ubuntu servers (ui-network, backup, dev, adambalm, smb)
- **`rpi`** - Raspberry Pi devices (rockyledge, morgspi, mudderpi, probepi,
  magpi, voicepi-greatroom)
- **`k3s_prod`** - Kubernetes production cluster nodes (k3s-prod-11,
  k3s-prod-12, k3s-prod-13, k3s-prod-15)
- **`pve`** - Proxmox VE hosts (pve11, pve12, pve13, pve15)
- **`lxc`** - LXC containers (smb, k3s-prod-15)

### Service-Based Organization

Uses `services` host variable to define what runs on each host:

```yaml
morgspi:
  services: ['nut', 'homeassistant']
voicepi-greatroom:
  services: ['wyoming']
```

## Key Playbooks

### System Setup

- **`setup-global.yaml`** - Base system configuration for all non-Proxmox hosts
  - Timezone, packages, user shells, oh-my-zsh
  - SMB and Ceph mounts (conditional)
  - Rsyslog configuration
  - Virtual machine specific packages
- **`setup-lxc-prep.yaml`** - LXC container preparation
  - Global configuration tasks
  - Ceph mounts
  - User creation and SSH key setup
- **`setup-rpi.yaml`** - Raspberry Pi specific setup
  - Package upgrades with automatic reboot detection
  - Service-specific tasks (NUT, Home Assistant, Wyoming satellites)

### Task Organization

Tasks are organized by function:

- **`setup-global-*.yaml`** - System-wide configuration
- **`setup-rpi-*.yaml`** - Raspberry Pi specific tasks
- Service-specific includes based on `services` variable

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

- Secrets stored in `group_vars/vault.yaml.secret` (encrypted with ansible-vault)
- Vault password stored in `~/.ansible/.vault-pass` (default location)
- SSH keys, passwords, and credentials all encrypted

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
