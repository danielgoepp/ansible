# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Core Ansible Operations

```bash
# Run playbooks (most common commands)
ansible-playbook playbooks/setup-global.yaml
ansible-playbook playbooks/setup-rpi.yaml
ansible-playbook playbooks/setup-lxc-prep.yaml
ansible-playbook playbooks/ops-upgrade-cluster.yaml

# Target specific hosts or groups
ansible-playbook playbooks/setup-global.yaml -l ubuntu
ansible-playbook playbooks/setup-rpi.yaml -l morgspi,mudderpi

# Check syntax and validate
ansible-playbook playbooks/setup-global.yaml --syntax-check
ansible-inventory --list
ansible-inventory --graph

# Test connectivity
ansible all -m ping
ansible ubuntu -m ping
```

### Vault Operations

```bash
# Edit encrypted variables
ansible-vault edit group_vars/vault.yaml.secret

# View encrypted content
ansible-vault view group_vars/vault.yaml.secret

# Encrypt new files
ansible-vault encrypt group_vars/vault.yaml.secret
```

### Version Checking Operations

```bash
# List all applications tracked by version-checker
ansible-playbook playbooks/version-check.yaml -e version_check_action=list

# Check all application versions and update status
ansible-playbook playbooks/version-check.yaml -e version_check_action=check-all

# Show version summary with status counts
ansible-playbook playbooks/version-check.yaml -e version_check_action=summary

# Check specific application (all instances)
ansible-playbook playbooks/version-check.yaml -e version_check_action=app -e app_name="home assistant"
ansible-playbook playbooks/version-check.yaml -e version_check_action=app -e app_name="k3s"

# Run system info only (original functionality - commented out in current version)
# ansible-playbook playbooks/version-check.yaml
```

### Manifest Update Operations

```bash
# Individual service playbooks (recommended approach - clean and simple)
# Located in playbooks/k3s/ directory
ansible-playbook playbooks/k3s/update-homeassistant-manifest.yaml
ansible-playbook playbooks/k3s/update-zigbee2mqtt-manifest.yaml
ansible-playbook playbooks/k3s/update-esphome-manifest.yaml

# Update specific instance (for multi-instance services)
ansible-playbook playbooks/k3s/update-homeassistant-manifest.yaml -e target_instance=prod
ansible-playbook playbooks/k3s/update-homeassistant-manifest.yaml -e target_instance=morgspi
ansible-playbook playbooks/k3s/update-zigbee2mqtt-manifest.yaml -e target_instance=11

# CRD manifest upgrades (for services with multiple CRD instances)
ansible-playbook playbooks/k3s/ops-upgrade-mongodb-crd-manifests.yaml
ansible-playbook playbooks/k3s/ops-upgrade-victoriametrics-crd-manifests.yaml

# Other k3s service upgrades
ansible-playbook playbooks/k3s/ops-upgrade-postfix-manifest.yaml
ansible-playbook playbooks/k3s/ops-upgrade-grafana-manifest.yaml
ansible-playbook playbooks/k3s/ops-upgrade-n8n-manifest.yaml
ansible-playbook playbooks/k3s/ops-upgrade-telegraf-manifest.yaml
ansible-playbook playbooks/k3s/ops-upgrade-cnpg-manifest.yaml
ansible-playbook playbooks/k3s/ops-upgrade-hertzbeat-manifest.yaml

# Generic manifest upgrade (alternative approach - useful for ad-hoc services)
ansible-playbook playbooks/ops-upgrade-manifest-generic.yaml -e service_name=postfix
ansible-playbook playbooks/ops-upgrade-manifest-generic.yaml -e service_name=grafana

# With custom parameters for non-standard deployments
ansible-playbook playbooks/ops-upgrade-manifest-generic.yaml -e service_name=myservice -e k8s_context=k3s-dev -e context_suffix=dev
```

### Helm Upgrade Operations

```bash
# Upgrade individual helm charts (updates repo, shows before/after versions)
# Located in playbooks/k3s/ directory
ansible-playbook playbooks/k3s/ops-upgrade-alertmanager-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-cert-manager-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-fluent-bit-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-metallb-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-opensearch-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-pgadmin-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-traefik-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-weather-helm.yaml

# Operator helm upgrades (upgrades the operators that manage CRDs)
ansible-playbook playbooks/k3s/ops-upgrade-mongodb-operator-helm.yaml
ansible-playbook playbooks/k3s/ops-upgrade-victoriametrics-operator-helm.yaml
```

### ESPHome Operations

```bash
# Container Shell Upgrade (Two-step process for reliability)

# Step 1: Discover all devices and update group_vars/esphome.yml
ansible-playbook playbooks/ops-esphome-discover.yaml

# Step 2: Upgrade all configured devices
ansible-playbook playbooks/ops-upgrade-esphome.yaml

# Upgrade specific device only
ansible-playbook playbooks/ops-upgrade-esphome.yaml -e target_device=ble-proxy-greatroom

# Upgrade Konnected devices only
ansible-playbook playbooks/ops-upgrade-esphome-konnected.yaml

# Skip build cache cleanup (cleanup is enabled by default)
ansible-playbook playbooks/ops-upgrade-esphome.yaml -e esphome_clean_build=false
ansible-playbook playbooks/ops-upgrade-esphome-konnected.yaml -e esphome_clean_build=false

# Use different k3s context
ansible-playbook playbooks/ops-esphome-discover.yaml -e k3s_context=k3s-morgspi
ansible-playbook playbooks/ops-upgrade-esphome.yaml -e k3s_context=k3s-morgspi

# Customize namespace and deployment name
ansible-playbook playbooks/ops-upgrade-esphome.yaml -e esphome_namespace=homeassistant -e esphome_deployment_name=esphome

# Dashboard Remote Install (Legacy - uses dashboard API)
# Trigger remote install for all configured devices (equivalent to clicking "Install" in GUI)
ansible-playbook playbooks/ops-esphome-ota.yaml

# Install specific device by name and IP
ansible-playbook playbooks/ops-esphome-ota.yaml -e device_name=sensor-garage -e device_ip=192.168.1.100

# Install specific device with custom config name
ansible-playbook playbooks/ops-esphome-ota.yaml -e device_name=my-sensor -e device_config=custom-sensor -e device_ip=192.168.1.101

# Validate/compile only (equivalent to "Validate" button)
ansible-playbook playbooks/ops-esphome-ota.yaml -e esphome_compile_only=true

# Run install without waiting for completion (fire and forget)
ansible-playbook playbooks/ops-esphome-ota.yaml -e esphome_wait_for_completion=false

# Use custom dashboard URL
ansible-playbook playbooks/ops-esphome-ota.yaml -e esphome_dashboard_url=https://esphome.your-domain.com

# Set custom timeout (default 10 minutes)
ansible-playbook playbooks/ops-esphome-ota.yaml -e esphome_timeout=900
```

### Additional Operations

```bash
# Cluster maintenance and testing
ansible-playbook playbooks/ops-proxmox-maintenance-on.yaml
ansible-playbook playbooks/ops-test-alerts.yaml
ansible-playbook playbooks/ops-test-ceph-noout.yaml
```

## Architecture

### Repository Structure

- **inventories/hosts.yml**: Main inventory with host groups (ubuntu, rpi, k3s_prod, pve, lxc)
- **playbooks/**: Organized by purpose
  - **setup-*.yaml**: Initial system configuration
  - **ops-*.yaml**: Operational tasks (maintenance, testing)
  - **k3s/**: K3s-specific playbooks (manifest updates, helm upgrades)
- **tasks/**: Reusable task files
  - **common-update-manifest.yaml**: Shared manifest update logic
  - **setup-global-***: Global system setup tasks
  - **setup-rpi-***: Raspberry Pi specific tasks
  - **ops-upgrade-cluster-***: Cluster upgrade tasks
- **files/k3s-config/**: Git submodule containing Kubernetes manifests
- **files/**: Static files and configuration templates
- **vars/common.yml**: Common variables (k3s_config_base_path, contexts)
- **group_vars/vault.yaml.secret**: Encrypted secrets using ansible-vault
- **host_vars/**: Host-specific variables

### Configuration Management

- **k3s-config submodule**: Kubernetes manifests managed as a separate Git repository
- **Relative paths**: All playbooks use `{{ playbook_dir }}` for portable submodule references
- **Vault password**: Automatically loaded from `~/.ansible/.vault-pass`
- **SSH optimization**: ControlMaster enabled for connection reuse
- **Python interpreter**: Set to `auto_silent` to suppress discovery warnings
- **Host key checking**: Disabled for lab environment
- **Utility scripts**: Git submodule at `scripts/utility-scripts/` containing Python scripts for cluster upgrade operations

**Variable Loading for Localhost Playbooks**: Due to Ansible's behavior with `ansible_connection: local`, localhost-based playbooks need to explicitly load variables. Use:

```yaml
- name: My Localhost Playbook
  hosts: localhost
  gather_facts: false
  vars_files:
    - ../vars/common.yml  # Recommended: Contains all global vars
    # OR
```

**Vault Loading Pattern for AWX Compatibility**: When playbooks need vault variables but must also run on AWX (where vault files are loaded differently), use conditional loading in `pre_tasks`:

```yaml
- name: My Playbook
  hosts: somehost
  become: true

  pre_tasks:
    - name: Load vault variables when running locally
      include_vars:
        file: ../group_vars/all/vault.yml
      when: lookup('env', 'AWX_HOST') | default('') == ''

  roles:
    - somerole
```

This pattern checks for the `AWX_HOST` environment variable and only loads vault files when running locally, avoiding conflicts with AWX's built-in credential management.

**Manifest Path Resolution**: The system uses a standardized pattern:
`{k3s_config_base_path}/{service_name}/manifests/{service_name}-{context_suffix}.yaml`

**Override Capability**: Configuration can be overridden per-playbook or via command line:

```bash
# Override base path for different environment
ansible-playbook playbooks/k3s/ops-upgrade-grafana-manifest.yaml -e k3s_config_base_path="/path/to/dev/config"

# Override context for different cluster
ansible-playbook playbooks/k3s/ops-upgrade-grafana-manifest.yaml -e k3s_default_context="k3s-dev"
```

**Path Patterns for K3s Config References**:

- **Manifest playbooks**: Use `{{ playbook_dir }}/../../files/k3s-config/{service}/manifests/{service}-{context}.yaml`
- **Helm playbooks**: Use `{{ playbook_dir }}/../../files/k3s-config/{service}/helm/` for chart paths and values files
- **Vars file**: Uses `{{ playbook_dir }}/../files/k3s-config` (one level up from vars directory)

### Host Organization

The infrastructure is organized into logical groups:

- **ubuntu**: Ubuntu servers (ui-network, backup, dev, adambalm, smb)
- **rpi**: Raspberry Pi devices with service-specific roles
- **k3s_prod**: Kubernetes production cluster nodes
- **pve**: Proxmox VE hypervisor hosts
- **lxc**: LXC containers

### Service-Based Configuration

Hosts use a `services` variable to define what runs on each system:

```yaml
morgspi:
  services: ['nut', 'homeassistant']
voicepi-greatroom:
  services: ['wyoming']
```

Tasks use conditionals like `when: "'nut' in (services | default([]))"` to run service-specific configuration.

### Storage Architecture

- **SMB mounts**: Media storage available to k3s_prod hosts at `/mnt/smb_media`
- **Ceph mounts**: Production Kubernetes data, homes, and backups for k3s_prod hosts
- **Host entries**: Infrastructure hosts from `files/linux/hosts` are automatically added to `/etc/hosts`
- **Security exclusion**: The `adambalm` host is excluded from sensitive operations

### Multi-Play Structure

Playbooks typically have multiple plays:

1. System-level tasks (`become: true`) for root operations
2. User-level tasks (`become: false`, `remote_user: dang`) for user configuration
3. Service-specific tasks with conditionals based on host groups or services

### Task-Based Architecture

Recent manifest upgrade playbooks use a consolidated task-based approach:

- **tasks/common-update-manifest.yaml**: Reusable task file containing all manifest update logic
- **Individual playbooks**: Simple wrappers that set `service_name` and include the task file
- **Benefits**: Eliminates code duplication, consistent behavior, single place for bug fixes
- **Pattern**: Most services follow standard `/k3s-config/{service}/manifests/{service}-{context}.yaml`

### Playbook Naming Conventions

- **Manifest updates**: `update-{service}-manifest.yaml` for services that update K8s manifests (preferred for new playbooks)
- **Operations**: `ops-{action}-{target}.yaml` for operational tasks (upgrades, maintenance, etc.)
- **Setup**: `setup-{target}.yaml` for initial system configuration
- **Location**: K3s-specific playbooks are located in `playbooks/k3s/` directory

### Cluster Upgrade Task Naming Convention

All cluster upgrade task files use the prefix `ops-upgrade-cluster-` for consistency:

- **tasks/ops-upgrade-cluster-alerts.yaml**: Alert management (mute/unmute monitoring)
- **tasks/ops-upgrade-cluster-ceph-noout.yaml**: Ceph noout flag management
- **tasks/ops-upgrade-cluster-cnpg-maintenance.yaml**: CloudNativePG maintenance mode
- **tasks/ops-upgrade-cluster-drain.yaml**: Node draining and uncordoning operations
- **tasks/ops-upgrade-cluster-health.yaml**: Cluster and node health validation
- **tasks/ops-upgrade-cluster-k3s.yaml**: K3s node lifecycle operations (drain, shutdown, startup, uncordon, validate)
- **tasks/ops-upgrade-cluster-paired.yaml**: Orchestrates paired PVE+K3s node upgrades
- **tasks/ops-upgrade-cluster-proxmox.yaml**: Proxmox node upgrade operations
- **tasks/ops-upgrade-cluster-vm.yaml**: VM/LXC operations (migrate, shutdown, startup)
- **Future additions**: Always prefix new cluster upgrade task files with `ops-upgrade-cluster-`

### Modular Architecture

The cluster upgrade system uses a highly modular approach:

- **Main playbook**: Orchestrates overall upgrade flow and maintenance mode
- **Paired upgrade**: Coordinates upgrade of matched PVE+K3s pairs
- **Component modules**: Specialized task files for each type of operation
- **Action-based**: Each module accepts an action parameter to specify what operation to perform

## Markdown Standards

Follow all markdownlint standards when creating or maintaining Markdown files in this project.
