# AWX Job Template Creator

Automatically creates AWX job templates from ESPHome playbooks.

## Features

- Scans `playbooks/esphome/` directory for all playbook files
- Extracts playbook metadata (name, description, variables)
- Creates or updates job templates via AWX REST API
- Preserves default variables as extra_vars
- Enables variable overrides on launch

## Prerequisites

```bash
pip install requests pyyaml
```

## Configuration

### Option 1: Environment Variables

```bash
export AWX_URL="https://awx.example.com"
export AWX_TOKEN="your_api_token_here"
export AWX_PROJECT_ID="1"
export AWX_INVENTORY_ID="1"
export AWX_CREDENTIAL_ID="1"  # Optional
export AWX_EXECUTION_ENVIRONMENT_ID="1"  # Optional
export AWX_VERIFY_SSL="true"
```

### Option 2: Configuration File

```bash
cp scripts/awx_config.example.sh scripts/awx_config.sh
# Edit awx_config.sh with your values
source scripts/awx_config.sh
```

## Finding AWX IDs

### Via AWX CLI

```bash
# Install AWX CLI
pip install awxkit

# Configure
awx login

# Find project ID
awx projects list

# Find inventory ID
awx inventory list

# Find credential ID
awx credentials list

# Find execution environment ID
awx execution_environments list
```

### Via AWX UI

1. **Project ID**: Resources → Projects → Select your project → URL shows ID
2. **Inventory ID**: Resources → Inventories → Select inventory → URL shows ID
3. **Credential ID**: Resources → Credentials → Select credential → URL shows ID
4. **Execution Environment ID**: Administration → Execution Environments → Select EE → URL shows ID

### Via API

```bash
# Projects
curl -H "Authorization: Bearer $AWX_TOKEN" \
  https://awx.example.com/api/v2/projects/

# Inventories
curl -H "Authorization: Bearer $AWX_TOKEN" \
  https://awx.example.com/api/v2/inventories/

# Credentials
curl -H "Authorization: Bearer $AWX_TOKEN" \
  https://awx.example.com/api/v2/credentials/

# Execution Environments
curl -H "Authorization: Bearer $AWX_TOKEN" \
  https://awx.example.com/api/v2/execution_environments/
```

## Usage

### Basic Usage

```bash
cd /Users/dang/Documents/Development/ansible
./scripts/create_awx_templates.py
```

### With Configuration File

```bash
source scripts/awx_config.sh
./scripts/create_awx_templates.py
```

### Dry Run (validate config only)

Edit the script and set `DRY_RUN = True` near the top.

## What Gets Created

For each playbook in `playbooks/esphome/`, the script creates a job template with:

- **Name**: Extracted from playbook's `name` field
- **Description**: Includes device patterns if applicable
- **Playbook**: Path relative to project root
- **Extra Variables**: Default values from playbook (k3s_context, esphome_namespace, etc.)
- **Ask Variables on Launch**: Enabled (allows overriding defaults)

### Example Template

For `upgrade-esphome-konnected.yaml`:

```yaml
Name: "Upgrade Konnected ESPHome devices"
Description: "Upgrade Konnected ESPHome devices | Patterns: konnected"
Playbook: "playbooks/esphome/upgrade-esphome-konnected.yaml"
Extra Variables:
  esphome_namespace: "esphome"
  esphome_deployment_name: "esphome"
  k3s_context: "k3s-prod"
```

## Running Job Templates

### Via AWX UI

1. Navigate to Templates
2. Select the template
3. Click Launch
4. Override variables if needed (k3s_context, etc.)

### Via AWX CLI

```bash
# Basic launch
awx job_templates launch "Upgrade Konnected ESPHome devices"

# With variable overrides
awx job_templates launch "Upgrade Konnected ESPHome devices" \
  --extra_vars '{"k3s_context": "k3s-dev"}'
```

### Via API

```bash
curl -X POST \
  -H "Authorization: Bearer $AWX_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"extra_vars": {"k3s_context": "k3s-prod"}}' \
  https://awx.example.com/api/v2/job_templates/123/launch/
```

## Updating Templates

Run the script again to update existing templates. The script will:

1. Check if template already exists (by name)
2. Update if exists, create if new
3. Preserve template ID and settings not managed by script

## Troubleshooting

### Authentication Error

```
Error: 401 Unauthorized
```

**Solution**: Verify AWX_TOKEN is valid and not expired.

### Project Not Found

```
Error: Invalid project ID
```

**Solution**: Verify AWX_PROJECT_ID exists and contains your playbooks.

### SSL Certificate Error

```
Error: SSL certificate verification failed
```

**Solution**: Set `AWX_VERIFY_SSL="false"` for self-signed certificates.

### Playbook Not Found

```
Error: Playbook file not found
```

**Solution**: Ensure AWX project is synced and contains the playbook path.

## Customization

### Adding New Playbooks

1. Create new playbook in `playbooks/esphome/`
2. Follow existing playbook structure
3. Run script to create template

### Modifying Template Creation

Edit `build_template_data()` function in the script to customize:

- Template settings
- Survey questions
- Notification settings
- Job limits

### Adding Survey Questions

```python
# In build_template_data()
template_data['survey_enabled'] = True
template_data['survey_spec'] = {
    'name': 'Device Selection',
    'description': 'Select device to upgrade',
    'spec': [
        {
            'question_name': 'Device Name',
            'question_description': 'Name of ESPHome device',
            'variable': 'target_device',
            'type': 'text',
            'required': False,
        }
    ]
}
```

## Security Notes

- Store `awx_config.sh` outside version control (add to `.gitignore`)
- Use API tokens with minimum required permissions
- Rotate tokens regularly
- Use AWX RBAC to control template access