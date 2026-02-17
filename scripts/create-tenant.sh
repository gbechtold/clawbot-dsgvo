#!/bin/bash
set -e

TENANT_ID="${1:-demo-tenant}"

echo "Creating tenant: $TENANT_ID"

# This would normally create tenant-specific configuration
# For MVP, we just validate the tenant ID format

if [[ ! "$TENANT_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Tenant ID must contain only alphanumeric characters, hyphens, and underscores"
    exit 1
fi

echo "✅ Tenant '$TENANT_ID' is ready"
echo ""
echo "Use this tenant_id in API requests:"
echo "curl -X POST http://localhost:8000/api/v1/ingest \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"tenant_id\": \"$TENANT_ID\", \"content\": \"Test feedback\", \"source\": \"email\"}'"
