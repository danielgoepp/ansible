# AGENTS - ansible repository

## Purpose

Home lab infrastructure automation for Ubuntu servers, Raspberry Pi devices,
Proxmox hosts, LXC containers, and a k3s production cluster.

## Primary references

- `README.md` for high-level usage and operations.
- `CLAUDE.md` for workflow rules and command patterns.
- `ANSIBLE.md` for architecture and conventions.

## Core workflows

- SSH host/group configuration: `playbooks/ssh/common-<group>.yaml` and
  `playbooks/ssh/host-<hostname>.yaml` (optional `-e apt_dist_upgrade=true`).
- ESPHome updates: `playbooks/esphome/upgrade-esphome.yaml`.
- K3s app updates: `playbooks/k3s/update-app.yaml -e app_name=<application>`.
- Maintenance mode: `playbooks/ops-maintenance-mode.yaml`.
- Version checks: `playbooks/version-check.yaml`.

## Inventory and grouping

- Inventory: `inventories/hosts.yml` with groups for `ubuntu`, `rpi`, `k3s_prod`,
  `pve`, `lxc`, and service-based `services` variables.

## Secrets and AWX compatibility

- Secrets in `inventories/group_vars/all/vault.yml` (ansible-vault).
- Vault password at `~/.ansible/.vault-pass`.
- Use `awx_*` variables with defaults for dual local/AWX execution.

## K3s update architecture

- Config in `inventories/group_vars/all/k3s_applications.yml`.
- Tasks: `tasks/k3s-update-*.yaml`.
- Manifest/Helm paths based on `k3s_config_base_path`.
- `files/k3s-config/` is a submodule with manifests and Helm values.

## Agent policies

- **Do NOT** perform git `commit`, `push`, or any irreversible repository changes automatically.
- Only execute git operations when **explicitly instructed** by the repository owner, and after all validations and checks have been completed.
- I will prepare suggested git commands, commit messages, and validation checks, but I will not run them or push changes without your direct confirmation.

## Conventions

- Follow markdownlint standards for Markdown edits.
- Prefer idempotent playbooks and documented usage headers.
