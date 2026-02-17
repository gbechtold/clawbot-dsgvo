#!/bin/bash
set -e

API_URL="${API_URL:-http://localhost:8000}"
TENANT_ID="${TENANT_ID:-default}"

echo "🦞 Testing ClawBot Pipeline"
echo "==========================="
echo "API: $API_URL"
echo "Tenant: $TENANT_ID"
echo ""

# Test 1: Retail complaint with PII
echo "Test 1: Retail complaint with PII"
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$TENANT_ID"'",
    "content": "Hallo, ich habe am 15. Januar eine Bestellung aufgegeben aber nichts erhalten. Meine E-Mail ist max.mustermann@example.com und meine Telefonnummer ist +43 664 1234567. Bitte um Rückruf!",
    "source": "email",
    "metadata": {"order_id": "ORD-12345"}
  }' | jq .
echo ""
echo ""

# Test 2: Energy billing issue
echo "Test 2: Energy billing issue"
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$TENANT_ID"'",
    "content": "Meine Stromrechnung ist viel zu hoch! Letzten Monat 450 EUR, das kann nicht sein. Bitte kontaktieren Sie mich unter anna.schmidt@gmx.at oder 0664 9876543. Kundennummer: AT123456789.",
    "source": "email",
    "metadata": {"customer_number": "AT123456789"}
  }' | jq .
echo ""
echo ""

# Test 3: Tourism praise
echo "Test 3: Tourism praise"
curl -X POST "$API_URL/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "'"$TENANT_ID"'",
    "content": "Vielen Dank für den wunderbaren Aufenthalt in Ihrem Hotel! Das Frühstück war ausgezeichnet und das Personal sehr freundlich. Wir kommen gerne wieder. Mit freundlichen Grüßen, peter.huber@aon.at",
    "source": "email",
    "metadata": {"booking_id": "BK-78910"}
  }' | jq .
echo ""
echo ""

# Check results
echo "📊 Checking results..."
echo ""

echo "Recent signals:"
curl -s "$API_URL/api/v1/signals?tenant_id=$TENANT_ID&limit=3" | jq '.signals[] | {signal_id, category, urgency, sentiment}'
echo ""

echo "Audit log:"
curl -s "$API_URL/api/v1/audit-log?tenant_id=$TENANT_ID&limit=5" | jq '.entries[] | {action, signal_id, timestamp}'
echo ""

echo "✅ Pipeline test complete!"
