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

### Version Management

```bash
# List all tracked applications
ansible-playbook playbooks/version-check.yaml -e version_check_action=list

# Check specific application versions
ansible-playbook playbooks/version-check.yaml \
  -e version_check_action=app -e app_name="home assistant"

# Full version check across all services
ansible-playbook playbooks/version-check.yaml \
  -e version_check_action=check-all
```

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

### Cluster Alert Management

```bash
# Disable all alerts (Graylog, Alertmanager, HertzBeat)
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=disable

# Enable all alerts
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=enable

# Manage specific alert system
ansible-playbook playbooks/ops-cluster-alerts.yaml \
  -e alert_action=disable -e target=graylog

# Customize silence duration (default: 2 hours)
ansible-playbook playbooks/ops-cluster-alerts.yaml \
  -e alert_action=disable -e duration_hours=4
```

## Infrastructure Overview

- **Ubuntu Servers**: General purpose servers (ui-network, backup, dev, smb)
- **Raspberry Pi**: IoT and edge services (Home Assistant, NUT UPS, Wyoming
  voice satellites)
- **Kubernetes**: k3s production cluster with Ceph storage
- **Proxmox VE**: Virtualization platform hosts
- **LXC Containers**: Lightweight application containers

## Key Features

- **Clear playbook naming**: `common-*` for groups, `host-*` for specific servers
- **Service-based configuration**: Hosts define their roles via `services` variables
- **Unified update architecture**: Single playbook for all K3s application updates
- **Optional system updates**: Add `-e apt_dist_upgrade=true` to any playbook using common role
- **Version tracking**: Automated version checking across all applications
- **Centralized alert management**: Control alerts across Graylog, Alertmanager, and HertzBeat
- **Secure secret management**: ansible-vault encrypted credentials
- **Automated storage mounting**: SMB media shares and Ceph distributed storage
- **AWX compatible**: Native Ansible implementation works in both local and AWX environments

## Documentation

- **[CLAUDE.md](CLAUDE.md)**: AI assistant working instructions and command
  reference
- **[ANSIBLE.md](ANSIBLE.md)**: Detailed technical documentation and
  architecture

## Repository Structure

```text
├── inventories/
│   ├── hosts.yml           # Host inventory and group definitions
│   └── group_vars/         # Group-specific variables (encrypted)
├── playbooks/              # Main execution playbooks
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

Playbooks are designed to run both locally and on AWX/Ansible Tower. Vault
variables are conditionally loaded using `pre_tasks` that check for the
`AWX_HOST` environment variable, allowing AWX to use its native credential
management while maintaining local vault file support.
