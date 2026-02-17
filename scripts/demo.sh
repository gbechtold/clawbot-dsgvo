#!/bin/bash
# ClawBot DSGVO Demo - 5 typische Einträge

API="http://localhost:8000"
TENANT="sutterlüty-demo"

echo "🦞 ClawBot DSGVO Demo"
echo "====================="
echo "Verarbeite 5 Kunden-Feedbacks..."
echo ""

# --- Eintrag 1: Beschwerde mit vielen PII ---
echo "📨 Eintrag 1/5: Lieferbeschwerde (viel PII)"
curl -s -X POST "$API/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "sutterlüty-demo",
    "source": "email",
    "content": "Sehr geehrte Damen und Herren, ich bin Max Mustermann aus Dornbirn, Marktstraße 5. Meine Bestellung vom 14. Februar wurde nicht geliefert. Bitte kontaktieren Sie mich unter max.mustermann@gmail.com oder 0664/1234567. Meine Kundennummer ist KD-88421. Ich erwarte eine sofortige Rückmeldung!",
    "metadata": {"channel": "email", "priority": "high"}
  }' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  Signal-ID:  {d.get(\"signal_id\",\"ERROR\")}')
print(f'  PII erkannt: {d.get(\"pii_detected\",0)} Felder')
print(f'  Kategorie:  {d.get(\"category\",\"?\")}')
print(f'  Dringlichkeit: {d.get(\"urgency\",\"?\")}')
print(f'  Sentiment:  {d.get(\"sentiment\",0):.2f}')
print(f'  Vorschau:   {d.get(\"anonymized_preview\",\"\")[:120]}')
"
echo ""

# --- Eintrag 2: Lob ohne PII ---
echo "📨 Eintrag 2/5: Positives Feedback"
curl -s -X POST "$API/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "sutterlüty-demo",
    "source": "app_review",
    "content": "Super Frischeprodukte heute im Markt Feldkirch! Die Bio-Äpfel aus Vorarlberg waren wirklich top. Das Personal war sehr freundlich und hat mir geholfen einen veganen Aufstrich zu finden. Komme gerne wieder!",
    "metadata": {"channel": "app", "rating": 5}
  }' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  Signal-ID:  {d.get(\"signal_id\",\"ERROR\")}')
print(f'  PII erkannt: {d.get(\"pii_detected\",0)} Felder')
print(f'  Kategorie:  {d.get(\"category\",\"?\")}')
print(f'  Dringlichkeit: {d.get(\"urgency\",\"?\")}')
print(f'  Sentiment:  {d.get(\"sentiment\",0):.2f}')
print(f'  Vorschau:   {d.get(\"anonymized_preview\",\"\")[:120]}')
"
echo ""

# --- Eintrag 3: Preisbeschwerde mit E-Mail ---
echo "📨 Eintrag 3/5: Preisbeschwerde"
curl -s -X POST "$API/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "sutterlüty-demo",
    "source": "web_form",
    "content": "Hallo, ich heiße Maria Schneider und bin seit 15 Jahren Stammkundin. Letzte Woche wurde mir an der Kasse 3,20€ zu viel verrechnet. Bitte erstatten Sie mir den Betrag. Meine E-Mail: m.schneider@gmx.at, IBAN AT12 3456 7890 1234 5678.",
    "metadata": {"channel": "web", "amount_disputed": 3.20}
  }' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  Signal-ID:  {d.get(\"signal_id\",\"ERROR\")}')
print(f'  PII erkannt: {d.get(\"pii_detected\",0)} Felder')
print(f'  Kategorie:  {d.get(\"category\",\"?\")}')
print(f'  Dringlichkeit: {d.get(\"urgency\",\"?\")}')
print(f'  Sentiment:  {d.get(\"sentiment\",0):.2f}')
print(f'  Vorschau:   {d.get(\"anonymized_preview\",\"\")[:120]}')
"
echo ""

# --- Eintrag 4: Produktanfrage ---
echo "📨 Eintrag 4/5: Produktanfrage"
curl -s -X POST "$API/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "sutterlüty-demo",
    "source": "whatsapp",
    "content": "Grüß Gott, führt ihr Dinkelmehl Type 1050 von der Mühle Lampert? Ich backe jedes Wochenende Brot und das Mehl aus dem letzten Besuch war super. Falls ja, könnt ihr mir sagen ob es auch online bestellbar ist? LG, Thomas aus Bludenz",
    "metadata": {"channel": "whatsapp", "product_inquiry": true}
  }' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  Signal-ID:  {d.get(\"signal_id\",\"ERROR\")}')
print(f'  PII erkannt: {d.get(\"pii_detected\",0)} Felder')
print(f'  Kategorie:  {d.get(\"category\",\"?\")}')
print(f'  Dringlichkeit: {d.get(\"urgency\",\"?\")}')
print(f'  Sentiment:  {d.get(\"sentiment\",0):.2f}')
print(f'  Vorschau:   {d.get(\"anonymized_preview\",\"\")[:120]}')
"
echo ""

# --- Eintrag 5: Kritische Hygiene-Beschwerde ---
echo "📨 Eintrag 5/5: Hygiene-Beschwerde (kritisch)"
curl -s -X POST "$API/api/v1/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "sutterlüty-demo",
    "source": "email",
    "content": "Guten Tag, mein Name ist Anna Fink, anna.fink@icloud.com. Ich musste heute im Markt Bregenz Kaiserstraße beobachten wie ein Mitarbeiter ohne Handschuhe rohes Fleisch angefasst und danach direkt Käse für mich aufgeschnitten hat. Das ist ein gravierendes Hygieneproblem! Ich verlange sofortiges Handeln und eine Rückmeldung.",
    "metadata": {"channel": "email", "severity": "critical", "store": "Bregenz-Kaiserstraße"}
  }' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f'  Signal-ID:  {d.get(\"signal_id\",\"ERROR\")}')
print(f'  PII erkannt: {d.get(\"pii_detected\",0)} Felder')
print(f'  Kategorie:  {d.get(\"category\",\"?\")}')
print(f'  Dringlichkeit: {d.get(\"urgency\",\"?\")}')
print(f'  Sentiment:  {d.get(\"sentiment\",0):.2f}')
print(f'  Vorschau:   {d.get(\"anonymized_preview\",\"\")[:120]}')
"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Alle Signale im System:"
curl -s "$API/api/v1/signals?tenant_id=sutterlüty-demo" | python3 -c "
import json,sys
signals = json.load(sys.stdin)
items = signals.get('signals', signals) if isinstance(signals, dict) else signals
print(f'  Gesamt: {len(items)} Signale verarbeitet')
for s in items:
    print(f'  • {s.get(\"signal_id\",\"?\")} | {s.get(\"category\",\"?\"):<20} | {s.get(\"urgency\",\"?\"):<8} | Sentiment: {s.get(\"sentiment\",0):.2f}')
"
echo ""
echo "📋 Audit-Log (letzte 5 Einträge):"
curl -s "$API/api/v1/audit-log?tenant_id=sutterlüty-demo&limit=5" | python3 -c "
import json,sys
data = json.load(sys.stdin)
logs = data.get('logs', data) if isinstance(data, dict) else data
for l in logs[:5]:
    print(f'  • {l.get(\"timestamp\",\"?\")[:19]} | {l.get(\"action\",\"?\")} | {l.get(\"signal_id\",\"?\")}')
" 2>/dev/null || echo "  (Audit-Log abrufbar unter /api/v1/audit-log)"
echo ""
echo "✅ Demo abgeschlossen!"
echo "🌐 Dashboard: http://localhost:8443"
echo "📚 API Docs:  http://localhost:8000/docs"
