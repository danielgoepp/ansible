#!/usr/bin/env python3
"""
Create AWX job templates from ESPHome playbooks.

This script scans the playbooks/esphome directory, extracts metadata from each
playbook, and creates corresponding job templates in AWX via the REST API.

Requirements:
    pip install requests pyyaml

Configuration:
    Set environment variables or update the CONFIG dictionary:
    - AWX_URL: AWX/Tower URL (e.g., https://awx.example.com)
    - AWX_TOKEN: API token for authentication
    - AWX_PROJECT_ID: Project ID containing these playbooks
    - AWX_INVENTORY_ID: Inventory ID to use for job templates
    - AWX_CREDENTIAL_ID: Credential ID for authentication
"""

import os
import sys
import json
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

# Configuration - can be overridden with environment variables
CONFIG = {
    'awx_url': os.getenv('AWX_URL', ''),
    'awx_token': os.getenv('AWX_TOKEN', ''),
    'project_id': os.getenv('AWX_PROJECT_ID', ''),
    'inventory_id': os.getenv('AWX_INVENTORY_ID', ''),
    'credential_id': os.getenv('AWX_CREDENTIAL_ID', ''),
    'execution_environment_id': os.getenv('AWX_EXECUTION_ENVIRONMENT_ID', ''),
    'playbook_dir': 'playbooks/esphome',
    'verify_ssl': os.getenv('AWX_VERIFY_SSL', 'true').lower() == 'true',
}


class AWXTemplateManager:
    """Manages AWX job template creation via REST API."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {config["awx_token"]}',
            'Content-Type': 'application/json',
        })
        self.session.verify = config['verify_ssl']
        self.base_url = config['awx_url'].rstrip('/')

    def _api_call(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API call to AWX."""
        url = urljoin(f"{self.base_url}/api/v2/", endpoint.lstrip('/'))
        response = self.session.request(method, url, **kwargs)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Print detailed error info for debugging
            try:
                error_detail = response.json()
                print(f"  API Error Details: {error_detail}")
            except:
                print(f"  API Error: {response.text}")
            raise
        return response

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Check if a job template already exists."""
        try:
            response = self._api_call('GET', '/job_templates/', params={'name': name})
            results = response.json().get('results', [])
            return results[0] if results else None
        except requests.exceptions.RequestException as e:
            print(f"Error checking for existing template: {e}")
            return None

    def create_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new job template."""
        response = self._api_call('POST', '/job_templates/', json=template_data)
        return response.json()

    def update_template(self, template_id: int, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing job template."""
        response = self._api_call('PATCH', f'/job_templates/{template_id}/', json=template_data)
        return response.json()

    def create_or_update_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a job template."""
        existing = self.get_template(template_data['name'])

        # Extract credentials to add separately
        credentials = template_data.pop('credentials', None)

        if existing:
            print(f"Updating existing template: {template_data['name']}")
            result = self.update_template(existing['id'], template_data)
            template_id = existing['id']
        else:
            print(f"Creating new template: {template_data['name']}")
            result = self.create_template(template_data)
            template_id = result['id']

        # Associate credentials if provided
        if credentials:
            self.associate_credentials(template_id, credentials)

        return result

    def associate_credentials(self, template_id: int, credential_ids: list):
        """Associate credentials with a job template."""
        for cred_id in credential_ids:
            try:
                self._api_call(
                    'POST',
                    f'/job_templates/{template_id}/credentials/',
                    json={'id': cred_id}
                )
                print(f"  ✓ Associated credential {cred_id}")
            except Exception as e:
                print(f"  Warning: Could not associate credential {cred_id}: {e}")


class PlaybookParser:
    """Parses Ansible playbooks to extract metadata."""

    @staticmethod
    def parse_playbook(filepath: Path) -> Dict[str, Any]:
        """Extract metadata from a playbook file."""
        with open(filepath, 'r') as f:
            playbook = yaml.safe_load(f)

        if not playbook or not isinstance(playbook, list):
            return {}

        # Get the first play
        play = playbook[0]

        # Get relative path from project root
        try:
            rel_path = filepath.relative_to(Path.cwd())
        except ValueError:
            # If filepath is not relative to cwd, use absolute then make relative
            rel_path = filepath

        return {
            'name': play.get('name', ''),
            'hosts': play.get('hosts', 'localhost'),
            'vars': play.get('vars', {}),
            'filepath': str(rel_path),
        }

    @staticmethod
    def extract_extra_vars(playbook_vars: Dict[str, Any]) -> Dict[str, Any]:
        """Extract variables that should be exposed as extra_vars."""
        extra_vars = {}

        # Common variables to expose
        var_keys = [
            'k3s_context',
            'esphome_namespace',
            'esphome_deployment_name',
            'esphome_timeout',
            'esphome_no_logs',
        ]

        for key in var_keys:
            if key in playbook_vars:
                extra_vars[key] = playbook_vars[key]

        return extra_vars

    @staticmethod
    def generate_description(playbook_name: str, playbook_vars: Dict[str, Any]) -> str:
        """Generate a description for the job template."""
        desc_parts = [playbook_name]

        # Add device pattern info if available
        for key in playbook_vars.keys():
            if key.endswith('_patterns'):
                patterns = playbook_vars[key]
                if isinstance(patterns, list):
                    desc_parts.append(f"Patterns: {', '.join(patterns)}")

        return " | ".join(desc_parts)


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate required configuration is present."""
    required = ['awx_url', 'awx_token', 'project_id', 'inventory_id']
    missing = [k for k in required if not config.get(k)]

    if missing:
        print(f"Error: Missing required configuration: {', '.join(missing)}")
        print("\nSet the following environment variables:")
        print("  AWX_URL - AWX/Tower URL")
        print("  AWX_TOKEN - API authentication token")
        print("  AWX_PROJECT_ID - Project ID containing playbooks")
        print("  AWX_INVENTORY_ID - Inventory ID for job templates")
        print("  AWX_CREDENTIAL_ID - (Optional) Credential ID")
        return False

    return True


def scan_playbooks(playbook_dir: str) -> List[Path]:
    """Scan directory for playbook files."""
    playbook_path = Path(playbook_dir)
    if not playbook_path.exists():
        print(f"Error: Playbook directory not found: {playbook_dir}")
        sys.exit(1)

    return sorted(playbook_path.glob('*.yaml'))


def build_template_data(playbook_meta: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Build AWX job template data structure."""
    parser = PlaybookParser()

    # Generate template name from playbook name
    template_name = playbook_meta['name']
    if not template_name:
        template_name = Path(playbook_meta['filepath']).stem.replace('_', ' ').title()

    extra_vars = parser.extract_extra_vars(playbook_meta['vars'])
    description = parser.generate_description(playbook_meta['name'], playbook_meta['vars'])

    template_data = {
        'name': template_name,
        'description': description,
        'job_type': 'run',
        'inventory': int(config['inventory_id']),
        'project': int(config['project_id']),
        'playbook': playbook_meta['filepath'],
        'ask_variables_on_launch': True,  # Allow overriding extra_vars
        'extra_vars': yaml.dump(extra_vars, default_flow_style=False),
    }

    # Add credential if provided
    if config.get('credential_id'):
        template_data['credentials'] = [int(config['credential_id'])]

    # Add execution environment if provided
    if config.get('execution_environment_id'):
        template_data['execution_environment'] = int(config['execution_environment_id'])

    # Add survey for specific playbooks
    if 'target_device' in playbook_meta['filepath'] or 'all' in playbook_meta['filepath']:
        template_data['ask_limit_on_launch'] = False  # Not applicable for localhost

    return template_data


def main():
    """Main execution function."""
    print("AWX Job Template Creator for ESPHome Playbooks")
    print("=" * 60)

    # Validate configuration
    if not validate_config(CONFIG):
        sys.exit(1)

    # Initialize manager
    manager = AWXTemplateManager(CONFIG)

    # Sync project to get latest playbooks from git
    print(f"\nSyncing project {CONFIG['project_id']} to fetch latest playbooks...")
    try:
        sync_response = manager._api_call('POST', f'/projects/{CONFIG["project_id"]}/update/')
        print(f"  ✓ Project sync initiated")

        # Wait for sync to complete
        import time
        print("  Waiting for sync to complete...", end='', flush=True)
        for i in range(10):
            time.sleep(2)
            project_response = manager._api_call('GET', f'/projects/{CONFIG["project_id"]}/')
            status = project_response.json().get('status')
            if status == 'successful':
                print(" Done!")
                break
            print(".", end='', flush=True)
        else:
            print("\n  Warning: Sync may still be running, continuing anyway...")
    except Exception as e:
        print(f"  Warning: Could not sync project: {e}")
        print("  Continuing anyway...")

    # Scan for playbooks
    playbooks = scan_playbooks(CONFIG['playbook_dir'])
    print(f"\nFound {len(playbooks)} playbook(s) in {CONFIG['playbook_dir']}")

    # Process each playbook
    results = {'created': [], 'updated': [], 'failed': []}

    for playbook_path in playbooks:
        print(f"\nProcessing: {playbook_path.name}")

        try:
            # Parse playbook
            parser = PlaybookParser()
            playbook_meta = parser.parse_playbook(playbook_path)

            if not playbook_meta.get('name'):
                print(f"  Warning: Could not extract name from playbook, skipping")
                continue

            # Build template data
            template_data = build_template_data(playbook_meta, CONFIG)

            # Debug: Print playbook path being used
            print(f"  Using playbook path: {template_data['playbook']}")

            # Create or update template
            result = manager.create_or_update_template(template_data)

            if result.get('id'):
                action = 'updated' if manager.get_template(template_data['name']) else 'created'
                results[action].append(template_data['name'])
                print(f"  ✓ Template {action}: {template_data['name']} (ID: {result['id']})")

        except Exception as e:
            results['failed'].append(playbook_path.name)
            print(f"  ✗ Failed: {e}")

    # Print summary
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Created: {len(results['created'])}")
    print(f"  Updated: {len(results['updated'])}")
    print(f"  Failed:  {len(results['failed'])}")

    if results['failed']:
        print("\nFailed playbooks:")
        for name in results['failed']:
            print(f"  - {name}")
        sys.exit(1)


if __name__ == '__main__':
    main()