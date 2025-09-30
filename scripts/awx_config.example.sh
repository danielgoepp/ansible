#!/usr/bin/env bash
# Example configuration for AWX job template creation
# Copy this file to awx_config.sh and fill in your values

# AWX/Tower URL
export AWX_URL="https://awx-prod.goepp.net"

# API Token (create via AWX UI: User > Tokens)
export AWX_TOKEN="h0GHiTqqmJYcbT0Vt29oshfQtE3meS"

# Project ID (find via: awx projects list or AWX UI)
export AWX_PROJECT_ID="9"

# Inventory ID (find via: awx inventory list or AWX UI)
export AWX_INVENTORY_ID="3"

# Credential ID (optional - find via: awx credentials list or AWX UI)
export AWX_CREDENTIAL_ID="1"

# Execution Environment ID (optional - find via: awx execution_environments list or AWX UI)
export AWX_EXECUTION_ENVIRONMENT_ID=""

# SSL Verification (set to 'false' for self-signed certs)
export AWX_VERIFY_SSL="true"