# Ansible Home Lab Infrastructure

Infrastructure automation for home lab environment managing Ubuntu servers,
Raspberry Pi devices, Proxmox VE hypervisors, and Kubernetes clusters.

Against my better judgement, I'm making this repository public. I have removed
all the secrets. Yes, it does contain information that is specific to, and
provides knowledge of, my internal network, but I don't think anything too bad.

This is a far from complete project, very much a work in progress. It doesn't
include all of my work yet, just stuff that I had put in this directory already
as tested(ish). I will continue over time to migrate more of my lab work here
as I get a chance to clean it up.

## Operations

### Host and Group Configuration

```bash
# Configure host groups (common role)
ansible-playbook playbooks/ssh/common-ubuntu.yaml
ansible-playbook playbooks/ssh/common-k3s-prod.yaml
ansible-playbook playbooks/ssh/common-rpi.yaml

# Configure specific individual hosts
ansible-playbook playbooks/ssh/host-adambalm.yaml
ansible-playbook playbooks/ssh/host-backup.yaml
ansible-playbook playbooks/ssh/host-smb.yaml

# Include system updates
ansible-playbook playbooks/ssh/common-ubuntu.yaml -e apt_dist_upgrade=true
ansible-playbook playbooks/ssh/host-backup.yaml -e apt_dist_upgrade=true
```

### K3s Application Updates

```bash
# Unified update playbook for all K3s applications
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=grafana
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=homeassistant
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=traefik

# Update specific instance of multi-instance apps
ansible-playbook playbooks/k3s/update-app.yaml \
  -e app_name=homeassistant -e target_instance=prod
```

### ESPHome Device Updates

```bash
# Upgrade all ESPHome devices
ansible-playbook playbooks/esphome/upgrade-esphome.yaml

# Upgrade specific device or pattern
ansible-playbook playbooks/esphome/upgrade-esphome.yaml -e target_pattern=<device-name>
```

### Cluster Upgrade

Rolling upgrade of the Proxmox cluster, the Ubuntu k3s VMs, and k3s itself.
Includes a pre-flight health gate, Ceph health checks before every drain,
post-drain pod snapshots, and operator confirmation prompts throughout.

```bash
# Required: target k3s version
ansible-playbook playbooks/ops-upgrade-cluster.yaml \
  -e k3s_target_version=<version>

# Run unattended (skip pause prompts)
ansible-playbook playbooks/ops-upgrade-cluster.yaml \
  -e k3s_target_version=<version> -e interactive_mode=false
```

Pre-flight checks Ceph health and opnsense location, then pauses for operator
confirmation before making any changes. Setup order: mute alerts first, then
stop iotawatt-sync, shutdown shared VMs, set Ceph noout, enable CNPG
maintenance. Each pair opens with a Ceph health check, a pre-pair status
snapshot, and an operator pause; after drain a pod snapshot is shown before
the Ubuntu upgrade begins; a second pause gates the PVE reboot; after the PVE
reboots, shared VMs on that node are started before the k3s VM to ensure
mounts are available. The pve11 pair additionally migrates opnsense to pve12
with a network connectivity test before and after. Post-flight pauses for a
final cluster review, then reverses maintenance gates and waits for Ceph
HEALTH_OK; alerts are unmuted last.

If the playbook is interrupted, re-running it detects the checkpoint in
`/tmp/cluster-upgrade-YYYY-MM-DD/` and prompts to resume from where it left
off or start over.

### Maintenance Mode

```bash
# Enable maintenance mode (mutes all alerts: Graylog, Alertmanager, Uptime Kuma)
ansible-playbook playbooks/ops-maintenance-mode.yaml -e maintenance_action=enable

# Disable maintenance mode (unmutes all alerts)
ansible-playbook playbooks/ops-maintenance-mode.yaml -e maintenance_action=disable

# Target specific alert system
ansible-playbook playbooks/ops-maintenance-mode.yaml \
  -e maintenance_action=enable -e target=graylog

# Customize silence duration (default: 2 hours)
ansible-playbook playbooks/ops-maintenance-mode.yaml \
  -e maintenance_action=enable -e duration_hours=4

# Silence a single Alertmanager alert (default: 1 hour)
ansible-playbook playbooks/ops-maintenance-mode-single.yaml \
  -e 'alert_name="Node Exporter - CPU High"'

# Remove a single alert silence early
ansible-playbook playbooks/ops-maintenance-mode-single.yaml \
  -e 'alert_name="Node Exporter - CPU High"' -e silence_action=disable
```

## Infrastructure Overview

- **Ubuntu Servers**: General purpose servers (ui-network, backup, dev, adambalm)
- **Raspberry Pi**: IoT and edge services (Home Assistant, NUT UPS monitoring)
- **Kubernetes**: k3s production cluster with Ceph storage
- **Proxmox VE**: Virtualization platform hosts
- **LXC Containers**: Lightweight application containers (smb)

## Key Features

- **Clear playbook naming**: `common-*` for groups, `host-*` for specific servers
- **Service-based configuration**: Hosts define their roles via `services` variables
- **Unified update architecture**: Single playbook for all K3s application updates
- **Optional system updates**: Add `-e apt_dist_upgrade=true` to any playbook using
  common role
- **Centralized alert management**: Control alerts across Graylog, Alertmanager,
  and Uptime Kuma
- **Secure secret management**: ansible-vault encrypted credentials
- **Automated storage mounting**: SMB media shares and Ceph distributed storage
- **AWX compatible**: Native Ansible implementation works in both local and AWX
  environments

## Documentation

- **[CLAUDE.md](CLAUDE.md)**: AI assistant working instructions and command
  reference
- **[ANSIBLE.md](ANSIBLE.md)**: Detailed technical documentation and
  architecture

## Repository Structure

```text
├── inventories/
│   ├── hosts.yml           # Host inventory and group definitions
│   └── group_vars/         # Group-specific variables
│       └── all/
│           ├── common.yml          # Common variables
│           ├── k3s_applications.yml # K3s app definitions
│           └── vault.yml           # Encrypted secrets
├── playbooks/              # Main execution playbooks
│   ├── ssh/                # SSH host configuration
│   ├── k3s/                # Kubernetes app updates
│   ├── esphome/            # ESPHome device updates
│   └── ops-*.yaml          # Operational tasks
├── roles/                  # Ansible roles
│   ├── backup/             # Backup server configuration
│   ├── common/             # Shared configuration (packages, users, mounts)
│   ├── llm/                # GPU/AI server setup
│   ├── rpi/                # Raspberry Pi configuration
│   ├── samba/              # Samba file server
│   ├── ui-network/         # UniFi Network controller
│   └── ui-protect/         # UniFi Protect
├── tasks/                  # Reusable task modules
├── files/                  # Static configuration files
└── host_vars/              # Host-specific overrides
```

## Requirements

- Ansible 2.9+
- SSH key authentication configured
- Vault password file at `~/.ansible/.vault-pass` (for local execution)
- Git submodules initialized:
  - `files/k3s-config/` - Kubernetes manifest configurations

## AWX/Tower Compatibility

Playbooks are designed to run both locally and on AWX/Ansible Tower. Variables
use an `awx_*` prefix pattern with fallback to vault/local defaults, allowing
AWX to use its native credential management while maintaining local vault file
support.
