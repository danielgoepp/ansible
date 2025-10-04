#!/usr/bin/env python3
"""
Update AWX job template survey for K3s application updates.

This script reads k3s_applications.yml and updates the AWX job template
to include a survey question asking which application to update.

Requirements:
    pip install requests pyyaml

Configuration:
    Set environment variables or update the CONFIG dictionary:
    - AWX_URL: AWX/Tower URL (e.g., https://awx-prod.goepp.net)
    - AWX_TOKEN: API token for authentication
    - TEMPLATE_ID: Job template ID to update (default: 32)

Usage:
    export AWX_URL="https://awx-prod.goepp.net"
    export AWX_TOKEN="your-token-here"
    ./update_awx_k3s_app_survey.py

    # Or specify custom template ID:
    export TEMPLATE_ID=32
    ./update_awx_k3s_app_survey.py
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
    'template_id': os.getenv('TEMPLATE_ID', '32'),
    'k3s_apps_file': 'inventories/group_vars/all/k3s_applications.yml',
    'verify_ssl': os.getenv('AWX_VERIFY_SSL', 'true').lower() == 'true',
}


class AWXSurveyManager:
    """Manages AWX job template survey via REST API."""

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
                print(f"API Error Details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"API Error: {response.text}")
            raise
        return response

    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get job template details."""
        try:
            response = self._api_call('GET', f'/job_templates/{template_id}/')
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting template: {e}")
            return None

    def get_survey(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Get current survey for a job template."""
        try:
            response = self._api_call('GET', f'/job_templates/{template_id}/survey_spec/')
            return response.json()
        except requests.exceptions.RequestException as e:
            # Survey may not exist yet
            return None

    def update_survey(self, template_id: int, survey_spec: Dict[str, Any]) -> bool:
        """Update survey for a job template."""
        response = self._api_call('POST', f'/job_templates/{template_id}/survey_spec/', json=survey_spec)
        # AWX survey_spec endpoint returns 200 with empty body on success
        return response.status_code == 200

    def enable_survey(self, template_id: int) -> Dict[str, Any]:
        """Enable survey for a job template."""
        response = self._api_call('PATCH', f'/job_templates/{template_id}/', json={'survey_enabled': True})
        return response.json()


def load_k3s_applications(filepath: str) -> Dict[str, Any]:
    """Load and parse k3s_applications.yml file."""
    app_file = Path(filepath)
    if not app_file.exists():
        print(f"Error: K3s applications file not found: {filepath}")
        sys.exit(1)

    with open(app_file, 'r') as f:
        data = yaml.safe_load(f)

    return data.get('k3s_applications', {})


def build_survey_spec(applications: Dict[str, Any]) -> Dict[str, Any]:
    """Build AWX survey specification from k3s applications."""
    # Get sorted list of application names
    app_names = sorted(applications.keys())

    # Build the survey specification
    survey_spec = {
        "name": "K3s Application Update Survey",
        "description": "Select which K3s application to update",
        "spec": [
            {
                "question_name": "Application Name",
                "question_description": "Which application do you want to update?",
                "required": True,
                "type": "multiplechoice",
                "variable": "app_name",
                "min": None,
                "max": None,
                "default": "",
                "choices": app_names,
                "new_question": True
            }
        ]
    }

    return survey_spec


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate required configuration is present."""
    required = ['awx_url', 'awx_token', 'template_id']
    missing = [k for k in required if not config.get(k)]

    if missing:
        print(f"Error: Missing required configuration: {', '.join(missing)}")
        print("\nSet the following environment variables:")
        print("  AWX_URL - AWX/Tower URL (e.g., https://awx-prod.goepp.net)")
        print("  AWX_TOKEN - API authentication token")
        print("  TEMPLATE_ID - (Optional) Template ID to update (default: 32)")
        return False

    return True


def main():
    """Main execution function."""
    print("AWX K3s Application Survey Updater")
    print("=" * 60)

    # Validate configuration
    if not validate_config(CONFIG):
        sys.exit(1)

    # Load k3s applications
    print(f"\nLoading K3s applications from: {CONFIG['k3s_apps_file']}")
    applications = load_k3s_applications(CONFIG['k3s_apps_file'])
    print(f"Found {len(applications)} applications:")
    for app_name in sorted(applications.keys()):
        deployment_method = applications[app_name].get('deployment_method', 'unknown')
        print(f"  - {app_name} ({deployment_method})")

    # Initialize manager
    manager = AWXSurveyManager(CONFIG)
    template_id = int(CONFIG['template_id'])

    # Get current template
    print(f"\nFetching job template {template_id}...")
    template = manager.get_template(template_id)
    if not template:
        print(f"Error: Could not find template with ID {template_id}")
        sys.exit(1)

    print(f"Template name: {template['name']}")
    print(f"Template playbook: {template.get('playbook', 'N/A')}")

    # Get current survey (if any)
    current_survey = manager.get_survey(template_id)
    if current_survey:
        print(f"\nCurrent survey exists with {len(current_survey.get('spec', []))} question(s)")

    # Build new survey spec
    print("\nBuilding survey specification...")
    survey_spec = build_survey_spec(applications)

    # Update survey
    print(f"Updating survey with {len(survey_spec['spec'][0]['choices'])} application choices...")
    try:
        success = manager.update_survey(template_id, survey_spec)
        if not success:
            raise Exception("Survey update returned non-200 status")
        print("✓ Survey updated successfully")

        # Enable survey on template
        print("Enabling survey on template...")
        manager.enable_survey(template_id)
        print("✓ Survey enabled")

        print("\n" + "=" * 60)
        print("Success!")
        print(f"\nTemplate URL: {CONFIG['awx_url']}/#/templates/job_template/{template_id}/details")
        print("\nSurvey question added:")
        print(f"  Variable: app_name")
        print(f"  Type: multiplechoice")
        print(f"  Choices: {len(survey_spec['spec'][0]['choices'])} applications")

    except Exception as e:
        print(f"\n✗ Failed to update survey: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
