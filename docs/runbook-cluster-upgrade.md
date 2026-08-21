# Runbook: Cluster Upgrade

Operator checklist for a maintenance window covering Proxmox, the k3s-prod
Ubuntu VMs, and k3s itself. This is the "what I actually do, in order" list —
for full flag/option reference see [`CLAUDE.md`](../CLAUDE.md#cluster-upgrade)
and [`README.md`](../README.md#cluster-upgrade).

Use the **Ansible** section for a normal run. Use the **Manual** section only
if Ansible/AWX itself is unavailable, or you need to pick up a step by hand
mid-run.

---

## Before starting

- [ ] Launch the Proxmox web UI for **pve11** and **pve12** in browser tabs
      (pve12 is opnsense's landing spot during the pve11 pair)
- [ ] Check for a newer k3s version (in the sibling `version-checker` repo):
  ```bash
  ./check_versions.py --app k3s
  ```

---

## Ansible (normal path)

```bash
# Full upgrade: PVE + Ubuntu + k3s
ansible-playbook playbooks/ops-upgrade-cluster.yaml -e k3s_target_version=<version>

# Resume after an interruption (maintenance setup already active)
ansible-playbook playbooks/ops-upgrade-cluster.yaml -e k3s_target_version=<version> -e skip_preflight=true

# Full upgrade, unattended (no operator prompts)
ansible-playbook playbooks/ops-upgrade-cluster.yaml -e k3s_target_version=<version> -e interactive_mode=false

# PVE + Ubuntu only, unattended - omit k3s_target_version to skip the k3s install step
ansible-playbook playbooks/ops-upgrade-cluster.yaml -e interactive_mode=false
```

### Checking status (during or after)

```bash
# Pods on a specific node
kubectl get pods --all-namespaces --field-selector spec.nodeName=k3s-prod-13

# All pods, grouped by node
kubectl get pods --all-namespaces -o wide --sort-by='{.spec.nodeName}'

# CNPG cluster health
kubectl cnpg status homeassistant-prod -n cnpg-homeassistant
kubectl cnpg status grafana-prod -n cnpg-grafana
kubectl cnpg status doholm-prod -n cnpg-doholm

kubectl get nodes
```

---

## Manual (fallback)

Mirrors what `ops-upgrade-cluster.yaml` does automatically. Pair order is
**15 → 13 → 12 → 11** (matching PVE node to its k3s VM by last two digits).

### 1. Pre-flight

- [ ] Health check: Ceph HEALTH_OK, no open alerts/down servers in Uptime
      Kuma, Alertmanager, Grafana
- [ ] Confirm opnsense is running on **pve11**
- [ ] Silence monitoring — Uptime Kuma / Alertmanager / Grafana maintenance
      windows (`ops-maintenance-mode.yaml` if Ansible is reachable, otherwise
      by hand in each UI)
- [ ] Stop `iotawatt-sync` (`management` namespace):
  ```bash
  kubectl delete deployment iotawatt-sync -n management
  ```
- [ ] Set Ceph `noout` (once, from any PVE node):
  ```bash
  ssh root@pve11
  ceph osd set noout
  ```
- [ ] Set CNPG maintenance mode:
  ```bash
  kubectl cnpg maintenance set --all-namespaces
  ```
- [ ] If a PVE upgrade is in scope, shut down: **ui-network, dev, smb,
      backup**

### 2. Per pair (repeat for 15, 13, 12, 11)

- [ ] **pve11 pair only:** migrate opnsense `pve11 → pve12`, confirm
      connectivity (`ping google.com`)
- [ ] Check for any other running VMs/LXCs on this PVE node besides the
      paired k3s VM (matters mainly for pve15) — shut them down
- [ ] Drain the node:
  ```bash
  kubectl drain k3s-prod-XX --ignore-daemonsets --delete-emptydir-data
  ```
  Confirm all pods rescheduled before continuing.
- [ ] Ubuntu upgrade (only if in scope):
  ```bash
  apt update && apt dist-upgrade
  ```
- [ ] k3s upgrade — **no `--server` flag** on an upgrade (only used for a
      fresh install; the existing server URL is retained). Skip this step
      entirely if not upgrading k3s this run:
  ```bash
  curl -sfL https://get.k3s.io | \
    K3S_TOKEN=k3s-prod \
    INSTALL_K3S_VERSION=<version> \
    INSTALL_K3S_SKIP_START=true \
    INSTALL_K3S_EXEC="server" \
    sh -s - --disable servicelb --disable traefik --flannel-backend=none --disable-network-policy
  ```
- [ ] Shut down the k3s VM:
  ```bash
  shutdown -h now
  ```
  (If only k3s is being upgraded — no PVE step — `reboot` instead so the VM
  comes back up on its own.)
- [ ] Upgrade Proxmox on the paired PVE node via the web UI, reboot at the
      end
  - [ ] Wait for the node to come back up, Ceph to go HEALTH_OK (noout
        warning expected and fine)
- [ ] Start the VMs/LXCs that were shut down on this node, **then** the k3s
      VM (so SMB mounts are available first)
  - [ ] Wait for the k3s VM to settle (idle CPU/load) before continuing
- [ ] Uncordon:
  ```bash
  kubectl uncordon k3s-prod-XX
  ```
- [ ] **pve11 pair only:** migrate opnsense back `pve12 → pve11`, confirm
      connectivity

### 3. Post-flight

- [ ] Unset CNPG maintenance mode:
  ```bash
  kubectl cnpg maintenance unset --all-namespaces
  ```
- [ ] Unset Ceph `noout`:
  ```bash
  ceph osd unset noout
  ```
- [ ] Confirm opnsense is back on pve11
- [ ] Re-apply `iotawatt-sync` (manifest at
      `files/k3s-config/iotawatt-sync/manifests/iotawatt-sync-prod.yaml`)
- [ ] Restore monitoring — remove the Uptime Kuma / Alertmanager / Grafana
      maintenance windows
- [ ] Final health check — Ceph, all nodes, and specifically **Postgres
      (CNPG), Zigbee, Home Assistant**
