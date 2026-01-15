# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Git Commit Policy

**IMPORTANT**: Never create git commits without explicitly asking the user first. Always present changes and wait for user approval before committing.

## Commands

This repository supports three primary operation types:

1. **SSH Operations**: Configure and update hosts via SSH
2. **ESPHome Operations**: Update ESPHome devices
3. **K3s Operations**: Update Kubernetes applications

### SSH Host Operations

Update and configure hosts via SSH.

```bash
# Run group playbooks (apply common role to host groups)
ansible-playbook playbooks/ssh/common-<group>.yaml

# Run host playbooks (configure specific servers)
ansible-playbook playbooks/ssh/host-<hostname>.yaml

# Run with system updates (apt update && apt dist-upgrade)
ansible-playbook playbooks/ssh/common-<group>.yaml -e apt_dist_upgrade=true

# Target specific hosts or groups
ansible-playbook playbooks/ssh/common-<group>.yaml -l <hostname>
ansible-playbook playbooks/ssh/common-<group>.yaml -l <host1>,<host2>

# LLM host upgrades (NVIDIA drivers, Docker, Ollama, Open WebUI, Portainer)
ansible-playbook playbooks/ssh/host-<llm-host>.yaml -e llm_upgrade_all=true
ansible-playbook playbooks/ssh/host-<llm-host>.yaml -e llm_upgrade_component=<component>

# Discovery commands
ls playbooks/ssh/          # List all SSH playbooks
ansible-inventory --graph  # View host organization
```

### ESPHome Device Operations

Update ESPHome firmware on IoT devices.

```bash
# Two-step container shell upgrade (recommended)
ansible-playbook playbooks/esphome/upgrade-esphome.yaml                                 # Upgrade all devices
ansible-playbook playbooks/esphome/upgrade-esphome.yaml -e target_device=<device-name>  # Specific device
ansible-playbook playbooks/esphome/upgrade-esphome.yaml -e esphome_clean_build=false    # Skip build cache cleanup
```

### K3s Application Operations

Update Kubernetes applications (Helm charts and manifests).

```bash
# Unified update playbook (routes to appropriate deployment method)
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=<application>

# Update specific instance (for multi-instance apps)
ansible-playbook playbooks/k3s/update-app.yaml -e app_name=<application> -e target_instance=<instance>

# Discovery commands
cat inventories/group_vars/all/k3s_applications.yml  # List available applications
ls playbooks/k3s/                                     # List K3s playbooks
```

### Cluster Alert Management

Manage alerts across monitoring systems (Graylog, Alertmanager, Uptime Kuma).

```bash
# Disable all alerts for maintenance
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=disable

# Enable all alerts after maintenance
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=enable

# Target specific alert system
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=disable -e target=graylog
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=disable -e target=alertmanager
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=disable -e target=uptime-kuma

# Customize silence duration (default: 2 hours)
ansible-playbook playbooks/ops-cluster-alerts.yaml -e alert_action=disable -e duration_hours=4
```

### Supporting Operations

```bash
# Vault operations
ansible-vault edit inventories/group_vars/all/vault.yml
ansible-vault view inventories/group_vars/all/vault.yml
ansible-vault encrypt inventories/group_vars/all/vault.yml

# Inventory and connectivity
ansible-inventory --list
ansible-inventory --graph
ansible all -m ping
ansible <group> -m ping

# Validation
ansible-playbook <playbook>.yaml --syntax-check

# Operational playbooks (cluster upgrades, maintenance, testing)
ls playbooks/ops-*.yaml
ansible-playbook playbooks/ops-<operation>.yaml
```

## Architecture

### Repository Structure

- **inventories/hosts.yml**: Main inventory with host groups (ubuntu, rpi, k3s_prod, pve, lxc)
- **playbooks/**: Organized by operation type (matching the three primary operation types)
  - **ssh/**: SSH-based host configuration and updates
    - **common-{group}.yaml**: Group playbooks (apply common role to host groups)
    - **host-{hostname}.yaml**: Host-specific playbooks
    - All playbooks are idempotent and support optional system updates via `-e apt_dist_upgrade=true`
  - **esphome/**: ESPHome device firmware updates
    - **upgrade-esphome.yaml**: Main upgrade playbook for ESPHome devices
  - **k3s/**: Kubernetes application updates
    - **update-app.yaml**: Unified update playbook (routes to appropriate deployment method)
  - **ops-*.yaml**: Additional operational tasks (cluster upgrades, maintenance, testing)
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
  - **ops-upgrade-cluster-alerts-***: Alert management task modules (Graylog, Alertmanager, Uptime Kuma)
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

**Vault Variable Auto-Loading**: Vault variables are automatically loaded from `inventories/group_vars/all/vault.yml` for all playbooks, regardless of their location in the directory structure. The vault file is placed next to the inventory file (`inventories/hosts.yml`), following Ansible best practices.

**AWX Compatibility**: When running on AWX, vault variables are managed through AWX's credential system and do not need to be explicitly loaded.

### Dual-Environment Playbook Design

**IMPORTANT**: All playbooks must be designed to run in both local Ansible and AWX environments.

**Required Pattern for Variables**:

- Use `awx_*` prefix for AWX-injected variables with fallback to local defaults
- Example: `k3s_context: "{{ awx_k3s_context | default('k3s-prod') }}"`

**Implementation Checklist**:

1. All configurable values should check for AWX variables first
2. Provide sensible defaults for local execution
3. Document both usage patterns in playbook header comments
4. Avoid hardcoded paths or values that differ between environments

**Example Header**:

```yaml
# Usage:
#   Local:  ansible-playbook playbooks/k3s/example.yaml
#   AWX:    Run as job template (no additional configuration required)
```

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

### Secret Management

**Preferred Pattern**: All secrets should follow the AWX-friendly pattern that works seamlessly with both local Ansible and AWX.

**Implementation Pattern**:

1. Store secrets in `inventories/group_vars/all/vault.yml` with descriptive names (e.g., `vault_proxmox_api_token_id`, `vault_proxmox_api_token_secret`)
1. In playbooks/roles, use `set_fact` to check for AWX variables first, then fall back to vault variables:

```yaml
- name: Set credentials from AWX or vault
  ansible.builtin.set_fact:
    proxmox_api_token_id: "{{ awx_proxmox_api_token_id | default(vault_proxmox_api_token_id | default('')) }}"
    proxmox_api_token_secret: "{{ awx_proxmox_api_token_secret | default(vault_proxmox_api_token_secret | default('')) }}"
```

1. Use the fact variables in your tasks:

```yaml
- name: List virtual machines
  community.general.proxmox_vm_info:
    api_token_id: "{{ proxmox_api_token_id }}"
    api_token_secret: "{{ proxmox_api_token_secret }}"
```

**Benefits**:

- **Local Ansible**: Uses vault variables automatically
- **AWX**: Credentials injected as `awx_*` variables take precedence
- **Consistent**: Same pattern across all secrets
- **Flexible**: Easy to override for testing

**Examples in Codebase**:

- [roles/backup/tasks/main.yml](roles/backup/tasks/main.yml) - OPNsense, Jira, and SSH credentials
- [roles/common/tasks/mount-smb.yaml](roles/common/tasks/mount-smb.yaml) - CIFS credentials
- [roles/ui-network/tasks/main.yaml](roles/ui-network/tasks/main.yaml) - SSH public key
- [playbooks/ops-proxmox-maintenance-on.yaml](playbooks/ops-proxmox-maintenance-on.yaml) - Proxmox API credentials

### Host Organization

The infrastructure is organized into logical groups defined in `inventories/hosts.yml`:

- **ubuntu**: Ubuntu servers
- **rpi**: Raspberry Pi devices with service-specific roles
- **k3s_prod**: Kubernetes production cluster nodes
- **pve**: Proxmox VE hypervisor hosts
- **lxc**: LXC containers

Use `ansible-inventory --graph` to view the current host organization.

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
- **Security exclusions**: Certain hosts may be excluded from sensitive operations (check host_vars)

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

- **SSH playbooks** (`playbooks/ssh/`): Two types with clear naming
  - **Group playbooks** (`common-{group}.yaml`): Apply common role to host groups
  - **Host playbooks** (`host-{hostname}.yaml`): Configure specific individual servers
  - All playbooks are idempotent (handle both initial setup and ongoing management)
  - Common variables for selective operations:
    - `apt_dist_upgrade=true`: Run apt update/dist-upgrade (available on all playbooks using common role)
    - Role-specific upgrade variables may be available (check playbook headers)
  - All playbooks include usage headers with invocation examples
- **K3s application updates** (`playbooks/k3s/`): Use `update-app.yaml` with `-e app_name=<application>` (unified, configuration-driven approach)
- **Operations** (`playbooks/ops-*.yaml`): Operational tasks following `ops-{action}-{target}.yaml` pattern
- Use `ls playbooks/` and `ls playbooks/ssh/` to discover available playbooks

### Cluster Upgrade Task Naming Convention

All cluster upgrade task files use the prefix `ops-upgrade-cluster-` for consistency and are located in the `tasks/` directory.

**Pattern**: `tasks/ops-upgrade-cluster-{component}.yaml`

**Task Categories**:

- Alert and monitoring management
- Ceph storage operations
- Database maintenance mode
- Node lifecycle (drain, shutdown, startup, uncordon)
- Health validation
- VM/LXC operations
- Orchestration tasks

Use `ls tasks/ops-upgrade-cluster-*.yaml` to see all cluster upgrade tasks.

### Modular Architecture

The cluster upgrade system uses a highly modular approach:

- **Main playbook**: Orchestrates overall upgrade flow and maintenance mode
- **Paired upgrade**: Coordinates upgrade of matched PVE+K3s pairs
- **Component modules**: Specialized task files for each type of operation
- **Action-based**: Each module accepts an action parameter to specify what operation to perform

### Alert Management System

The alert management system provides centralized control over monitoring alerts during maintenance:

- **playbooks/ops-cluster-alerts.yaml**: Standalone playbook with simple interface (alert_action=disable/enable)
- **Native Ansible implementation**: Uses uri module for REST APIs, Python library for Socket.io APIs
- **Modular task files**: Separate task files for each alert system
  - **tasks/ops-upgrade-cluster-alerts-graylog.yaml**: Manages Graylog event definitions
  - **tasks/ops-upgrade-cluster-alerts-alertmanager.yaml**: Manages Alertmanager silences with timed expiration
  - **tasks/ops-upgrade-cluster-alerts-uptime-kuma.yaml**: Manages Uptime Kuma maintenance windows (requires `pip install uptime-kuma-api`)
- **Configuration split**: Non-sensitive URLs in common.yml, credentials in vault.yml
- **AWX compatible**: Uses native Ansible date/time filters instead of platform-specific shell commands
- **Targeted control**: Can manage all systems or target specific ones (graylog, alertmanager, uptime-kuma)

## Markdown Standards

Follow all markdownlint standards when creating or maintaining Markdown files in this project.
