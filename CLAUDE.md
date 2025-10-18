# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Commit Policy

**IMPORTANT**: Never create git commits without explicitly asking the user first. Always present changes and wait for user approval before committing.

## Commands

### Core Ansible Operations

```bash
# Run playbooks (most common commands)
ansible-playbook playbooks/ssh/common-ubuntu.yaml
ansible-playbook playbooks/ssh/common-rpi.yaml
ansible-playbook playbooks/ssh/common-k3s-prod.yaml
ansible-playbook playbooks/ops-upgrade-cluster.yaml

# Run playbooks with system updates (apt update && apt dist-upgrade)
ansible-playbook playbooks/ssh/common-ubuntu.yaml -e apt_dist_upgrade=true
ansible-playbook playbooks/ssh/common-k3s-prod.yaml -e apt_dist_upgrade=true
ansible-playbook playbooks/ssh/common-lxc.yaml -e apt_dist_upgrade=true
ansible-playbook playbooks/ssh/common-rpi.yaml -e apt_dist_upgrade=true

# Target specific hosts or groups
ansible-playbook playbooks/ssh/common-ubuntu.yaml -l ui-network
ansible-playbook playbooks/ssh/common-rpi.yaml -l morgspi,mudderpi

# Update specific host with system updates
ansible-playbook playbooks/ssh/common-ubuntu.yaml -l ui-network -e apt_dist_upgrade=true

# Check syntax and validate
ansible-playbook playbooks/ssh/common-ubuntu.yaml --syntax-check
ansible-inventory --list
ansible-inventory --graph

# Test connectivity
ansible all -m ping
ansible ubuntu -m ping
```

### Vault Operations

```bash
# Edit encrypted variables
ansible-vault edit inventories/group_vars/all/vault.yml

# View encrypted content
ansible-vault view inventories/group_vars/all/vault.yml

# Encrypt new files
ansible-vault encrypt inventories/group_vars/all/vault.yml
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

### K3s Application Update Operations

```bash
# Unified update playbook - dynamically routes to appropriate deployment method
# Application configurations are defined in inventories/group_vars/all/k3s_applications.yml

# Update any application (manifest or helm)
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=<application>

# Examples - Single instance applications
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=grafana          # manifest
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=alertmanager     # helm
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=traefik          # helm
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=n8n              # manifest
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=postfix          # manifest

# Examples - Multi-instance applications (updates all instances by default)
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=homeassistant
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=zigbee2mqtt
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=victoriametrics
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=telegraf

# Update specific instance only (for multi-instance apps)
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=homeassistant -e target_instance=prod
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=homeassistant -e target_instance=morgspi
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=zigbee2mqtt -e target_instance=11
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=telegraf -e target_instance=vm

# Available applications:
# - alertmanager (helm)
# - cert-manager (helm)
# - esphome (manifest)
# - fluent-bit (helm)
# - grafana (manifest)
# - hertzbeat (manifest)
# - homeassistant (manifest-multi: morgspi, mudderpi, prod)
# - metallb (helm)
# - mongodb-operator (helm)
# - n8n (manifest)
# - opensearch (helm)
# - pgadmin (helm)
# - postfix (manifest)
# - telegraf (manifest-multi: vm, graylog)
# - traefik (helm)
# - victoriametrics (manifest-multi: vmsingle-main, vmsingle-lt)
# - victoriametrics-operator (helm)
# - weather (helm)
# - zigbee2mqtt (manifest-multi: 11, 15)
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

### LLM Operations

```bash
# Configure base system only (common role)
ansible-playbook playbooks/ssh/host-adambalm.yaml

# Initial setup or upgrade all LLM components (NVIDIA drivers, Docker, Python AI/ML packages, Ollama, Open WebUI, Portainer)
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_all=true

# Upgrade specific component only
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_component=ollama
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_component=openwebui
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_component=portainer

# Override configuration during upgrade
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_component=ollama -e ollama_bind_address=127.0.0.1
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_component=ollama -e ollama_max_loaded_models=2
ansible-playbook playbooks/ssh/host-adambalm.yaml -e llm_upgrade_component=openwebui -e openwebui_port=8080
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
  - **ssh/**: SSH-accessible host playbooks for configuration management
    - **{target}.yaml**: Host/group configuration (idempotent, handles both setup and updates)
    - All playbooks support optional system updates via `-e apt_dist_upgrade=true`
  - **ops-*.yaml**: Operational tasks (cluster upgrades, maintenance, testing)
  - **k3s/**: K3s-specific playbooks (application updates)
- **roles/**: Ansible roles for modular configuration
  - **llm/**: LLM role for GPU server setup (NVIDIA drivers, Docker, Python AI/ML packages, Ollama, Open WebUI, Portainer)
    - **tasks/ollama.yml**: Ollama installation and upgrade tasks (idempotent)
    - **tasks/openwebui.yml**: Open WebUI Docker container deployment and upgrade tasks
    - **tasks/portainer.yml**: Portainer Docker container deployment and upgrade tasks
    - **templates/ollama-override.conf.j2**: Systemd service override for Ollama configuration
    - **defaults/main.yml**: Configurable variables (ollama_*, openwebui_*, portainer_*, llm_install_*)
- **tasks/**: Reusable task files
  - **common-update-manifest.yaml**: Shared manifest update logic
  - **setup-global-***: Global system setup tasks
  - **setup-rpi-***: Raspberry Pi specific tasks
  - **ops-upgrade-cluster-***: Cluster upgrade tasks
- **files/k3s-config/**: Git submodule containing Kubernetes manifests
- **files/**: Static files and configuration templates
- **inventories/group_vars/all/common.yml**: Common variables (k3s_config_base_path, contexts) - automatically loaded for all hosts
- **inventories/group_vars/all/vault.yml**: Encrypted secrets using ansible-vault - automatically loaded for all hosts
- **host_vars/**: Host-specific variables

### Configuration Management

- **k3s-config submodule**: Kubernetes manifests managed as a separate Git repository
- **Relative paths**: All playbooks use `{{ playbook_dir }}` for portable submodule references
- **Vault password**: Automatically loaded from `~/.ansible/.vault-pass`
- **SSH optimization**: ControlMaster enabled for connection reuse
- **Python interpreter**: Set to `auto_silent` to suppress discovery warnings
- **Host key checking**: Disabled for lab environment
- **Utility scripts**: Git submodule at `scripts/utility-scripts/` containing Python scripts for cluster upgrade operations

**Vault Variable Auto-Loading**: Vault variables are automatically loaded from `inventories/group_vars/all/vault.yml` for all playbooks, regardless of their location in the directory structure. The vault file is placed next to the inventory file (`inventories/hosts.yml`), following Ansible best practices.

**AWX Compatibility**: When running on AWX, vault variables are managed through AWX's credential system and do not need to be explicitly loaded.

**Manifest Path Resolution**: The system uses a standardized pattern:
`{k3s_config_base_path}/{service_name}/manifests/{service_name}-{context_suffix}.yaml`

**Common Variables**: The `k3s_config_base_path` is defined in `inventories/group_vars/all/common.yml` and automatically available to all playbooks.

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
- **Security exclusion**: The `adambalm` host is excluded from sensitive operations

### Multi-Play Structure

Playbooks typically have multiple plays:

1. System-level tasks (`become: true`) for root operations
2. User-level tasks (`become: false`, `remote_user: dang`) for user configuration
3. Service-specific tasks with conditionals based on host groups or services

### Task-Based Architecture

K3s application updates use a unified, configuration-driven approach:

- **inventories/group_vars/all/k3s_applications.yml**: Centralized application configuration defining all K3s applications, their deployment methods (helm, manifest, manifest-multi), and deployment-specific parameters
- **playbooks/k3s/update-app.yaml**: Unified playbook that loads application config and routes to appropriate task file based on deployment method
- **tasks/k3s-update-manifest.yaml**: Reusable task file for single manifest deployments
- **tasks/k3s-update-manifest-multi.yaml**: Reusable task file for multi-instance manifest deployments
- **tasks/k3s-update-helm.yaml**: Reusable task file for Helm deployments
- **Benefits**: Single playbook for all updates, eliminates code duplication, consistent behavior, configuration-driven, easy to add new applications
- **Pattern**: Applications are referenced by name (`app_name=<application>`), configuration is automatically loaded and used

### Playbook Naming Conventions

- **SSH playbooks**: Two types with clear naming
  - **Group playbooks** (`common-*`): Apply common role to host groups
    - Examples: `common-ubuntu.yaml`, `common-rpi.yaml`, `common-k3s-prod.yaml`, `common-pve.yaml`, `common-lxc.yaml`
  - **Host playbooks** (`host-*`): Configure specific individual servers
    - Examples: `host-adambalm.yaml`, `host-backup.yaml`, `host-dev.yaml`, `host-smb.yaml`, `host-ui-network.yaml`
  - All playbooks are idempotent (handle both initial setup and ongoing management)
  - Variables for selective operations:
    - `apt_dist_upgrade=true`: Run apt update/dist-upgrade (available on all playbooks using common role)
    - `llm_upgrade_component=<component>`: Upgrade specific LLM component (host-adambalm only)
    - `llm_upgrade_all=true`: Upgrade all LLM components (host-adambalm only)
  - All playbooks include usage headers with invocation examples
- **K3s application updates**: Use `playbooks/k3s/update-app.yaml` with `-e app_name=<application>` (unified approach)
- **Operations**: `ops-{action}-{target}.yaml` for operational tasks (cluster upgrades, maintenance, etc.)
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
