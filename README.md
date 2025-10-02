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
ansible-playbook playbooks/ops-version-check.yaml -e version_check_action=list

# Check specific application versions
ansible-playbook playbooks/ops-version-check.yaml \
  -e version_check_action=app -e app_name="home assistant"

# Full version check across all services
ansible-playbook playbooks/ops-version-check.yaml \
  -e version_check_action=check-all
```

### Manifest Upgrades

```bash
# Individual service upgrades (recommended)
ansible-playbook playbooks/ops-upgrade-postfix-manifest.yaml
ansible-playbook playbooks/ops-upgrade-grafana-manifest.yaml

# Multi-context service upgrades (Home Assistant example)
ansible-playbook playbooks/ops-upgrade-homeassistant-manifest.yaml

# Target specific Home Assistant instance
ansible-playbook playbooks/ops-upgrade-homeassistant-manifest.yaml \
  -e target_instance=prod
ansible-playbook playbooks/ops-upgrade-homeassistant-manifest.yaml \
  -e target_instance=morgspi

# Generic manifest upgrade for ad-hoc services
ansible-playbook playbooks/ops-upgrade-manifest-generic.yaml \
  -e service_name=myservice
```

### Helm Chart Upgrades

```bash
# Individual helm chart upgrades
ansible-playbook playbooks/ops-upgrade-traefik-helm.yaml
ansible-playbook playbooks/ops-upgrade-cert-manager-helm.yaml
ansible-playbook playbooks/ops-upgrade-mongodb-operator-helm.yaml
```

## Infrastructure Overview

- **Ubuntu Servers**: General purpose servers (ui-network, backup, dev, smb)
- **Raspberry Pi**: IoT and edge services (Home Assistant, NUT UPS, Wyoming
  voice satellites)
- **Kubernetes**: k3s production cluster with Ceph storage
- **Proxmox VE**: Virtualization platform hosts
- **LXC Containers**: Lightweight application containers

## Key Features

- **Service-based configuration**: Hosts define their roles via `services`
  variables
- **Consolidated upgrade architecture**: Task-based approach for manifest
  upgrades
- **Version tracking**: Automated version checking across all applications
- **Secure secret management**: ansible-vault encrypted credentials
- **Automated storage mounting**: SMB media shares and Ceph distributed
  storage
- **Multi-play structure**: System and user-level configuration separation

## Documentation

- **[CLAUDE.md](CLAUDE.md)**: AI assistant working instructions and command
  reference
- **[ANSIBLE.md](ANSIBLE.md)**: Detailed technical documentation and
  architecture

## Repository Structure

```text
├── inventories/hosts.yml    # Host inventory and group definitions
├── playbooks/              # Main execution playbooks
├── tasks/                  # Reusable task modules
├── files/                  # Static configuration files
├── group_vars/             # Group-specific variables (encrypted)
└── host_vars/              # Host-specific overrides
```

## Requirements

- Ansible 2.9+
- SSH key authentication configured
- Vault password file at `~/.ansible/.vault-pass` (for local execution)
- Git submodules initialized:
  - `scripts/utility-scripts/` - Python utility scripts for cluster operations
  - `files/k3s-config/` - Kubernetes manifest configurations

## AWX/Tower Compatibility

Playbooks are designed to run both locally and on AWX/Ansible Tower. Vault
variables are conditionally loaded using `pre_tasks` that check for the
`AWX_HOST` environment variable, allowing AWX to use its native credential
management while maintaining local vault file support.
