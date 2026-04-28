#!/usr/bin/env python3
"""
Uptime Kuma Maintenance Window Management

Creates or deletes maintenance windows in Uptime Kuma, or reports down monitors.

Usage:
    python3 uptime_kuma_maintenance.py --action enable --url URL --username USER --password PASS
    python3 uptime_kuma_maintenance.py --action disable --url URL --username USER --password PASS
    python3 uptime_kuma_maintenance.py --action status --url URL --username USER --password PASS

Action:
    enable  - Create maintenance window (mute alerts)
    disable - Delete maintenance window (unmute alerts)
    status  - Print any monitors that are not currently UP. Exit 0 if all up,
              exit 2 if any are down (other errors exit 1).

Requirements:
    pip install uptime-kuma-api
"""

import argparse
import sys
import traceback

try:
    from uptime_kuma_api import UptimeKumaApi, MaintenanceStrategy
except ImportError:
    print("ERROR: uptime-kuma-api not installed. Run: pip install uptime-kuma-api")
    traceback.print_exc()
    sys.exit(1)


def create_maintenance(api):
    """Create a maintenance window for all monitor groups and status pages."""
    # Get all groups (monitors within groups inherit maintenance status)
    monitors = api.get_monitors()
    monitor_ids = [{"id": m["id"]} for m in monitors if m.get("type") == "group"]

    if not monitor_ids:
        print("No monitor groups found")
        return True

    # Create manual maintenance window (stays active until cancelled)
    result = api.add_maintenance(
        title="Ansible Maintenance Window",
        description="Automated maintenance created by Ansible maintenance mode playbook",
        strategy=MaintenanceStrategy.MANUAL,
        active=True
    )

    maintenance_id = result.get("maintenanceID")
    if not maintenance_id:
        print("Failed to create maintenance window")
        return False

    # Associate all monitors with the maintenance
    api.add_monitor_maintenance(maintenance_id, monitor_ids)

    # Associate all status pages with the maintenance
    status_pages = api.get_status_pages()
    if status_pages:
        status_page_ids = [{"id": sp["id"]} for sp in status_pages]
        api.add_status_page_maintenance(maintenance_id, status_page_ids)
        print(f"Created maintenance window {maintenance_id} for {len(monitor_ids)} monitors and {len(status_page_ids)} status pages")
    else:
        print(f"Created maintenance window {maintenance_id} for {len(monitor_ids)} monitors")

    return True


def report_status(api):
    """Print any monitors that are not currently UP.

    Exit code 0 = all monitors up. Exit code 2 = one or more down/unknown.
    Monitors of type 'group' are skipped (their state is derived).
    Monitors that are paused/inactive are skipped.
    """
    monitors = api.get_monitors()
    down = []
    for m in monitors:
        if m.get("type") == "group":
            continue
        if not m.get("active", True):
            continue
        try:
            beats = api.get_monitor_beats(m["id"], 1)
        except Exception:
            beats = []
        if not beats:
            continue
        last = beats[-1]
        # status: 0=down, 1=up, 2=pending, 3=maintenance
        if last.get("status") != 1:
            down.append({
                "name": m.get("name"),
                "id": m.get("id"),
                "status": last.get("status"),
                "msg": last.get("msg", ""),
            })

    if down:
        print(f"DOWN: {len(down)} monitor(s) not up:")
        for d in down:
            print(f"  - {d['name']} (id={d['id']}, status={d['status']}): {d['msg']}")
        return False

    print(f"OK: all {len(monitors)} monitors up")
    return True


def delete_maintenance(api):
    """Delete all Ansible-created maintenance windows."""
    maintenances = api.get_maintenances()
    deleted_count = 0

    for maintenance in maintenances:
        if maintenance.get("title") == "Ansible Maintenance Window":
            api.delete_maintenance(maintenance["id"])
            print(f"Deleted maintenance window: {maintenance['id']}")
            deleted_count += 1

    if deleted_count == 0:
        print("No Ansible maintenance windows found to delete")
    else:
        print(f"Deleted {deleted_count} maintenance window(s)")

    return True


def main():
    parser = argparse.ArgumentParser(description="Manage Uptime Kuma maintenance windows")
    parser.add_argument("--action", required=True, choices=["enable", "disable", "status"],
                        help="enable=create maintenance, disable=delete maintenance, status=report down monitors")
    parser.add_argument("--url", required=True, help="Uptime Kuma URL")
    parser.add_argument("--username", required=True, help="Uptime Kuma username")
    parser.add_argument("--password", required=True, help="Uptime Kuma password")
    args = parser.parse_args()

    try:
        api = UptimeKumaApi(args.url)
        api.login(args.username, args.password)

        if args.action == "enable":
            success = create_maintenance(api)
            api.disconnect()
            sys.exit(0 if success else 1)
        elif args.action == "disable":
            success = delete_maintenance(api)
            api.disconnect()
            sys.exit(0 if success else 1)
        else:
            success = report_status(api)
            api.disconnect()
            sys.exit(0 if success else 2)

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
