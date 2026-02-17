#!/bin/bash
# ClawBot DSGVO Demo – Vorher/Nachher Ansicht

API="http://localhost:8000"

show_entry() {
  local NR=$1
  local TITEL=$2
  local ORIGINAL=$3
  local PAYLOAD=$4

  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📨 EINTRAG $NR/5: $TITEL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "📥 ORIGINAL (mit PII):"
  echo "   $ORIGINAL"
  echo ""
  echo "⚙️  Pipeline läuft..."

  RESULT=$(curl -s -X POST "$API/api/v1/ingest" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

  echo ""
  echo "🔍 PII ERKANNT & ANONYMISIERT:"
  echo "$RESULT" | python3 -c "
import json,sys
d=json.load(sys.stdin)
preview = d.get('anonymized_preview','')
pii = d.get('pii_detected', 0)
print(f'   Gefundene PII-Felder: {pii}')
print('')
print('📤 ANONYMISIERTER TEXT (geht in Analyse):')
print(f'   {preview}')
print('')
print('📊 EXTRAHIERTES SIGNAL:')
print(f'   Signal-ID:     {d.get(\"signal_id\",\"ERROR\")}')
print(f'   Kategorie:     {d.get(\"category\",\"?\")}')
print(f'   Dringlichkeit: {d.get(\"urgency\",\"?\")}')
sentiment = d.get('sentiment', 0)
bar = '█' * int(abs(sentiment)*10)
direction = '▼ negativ' if sentiment < 0 else '▲ positiv'
print(f'   Sentiment:     {sentiment:.2f}  {bar} {direction}')
"
}

echo "🦞 ClawBot DSGVO – Vorher/Nachher Demo"
echo "======================================="
echo "Zeigt: Originaldaten → PII-Erkennung → Anonymisierung → Signal"

show_entry 1 "Lieferbeschwerde (viel PII)" \
  "Sehr geehrte Damen und Herren, ich bin Max Mustermann aus Dornbirn, Marktstraße 5. Meine Bestellung wurde nicht geliefert. Erreichbar unter max.mustermann@gmail.com oder 0664/1234567. Kundennummer KD-88421." \
  '{"tenant_id":"demo","source":"email","content":"Sehr geehrte Damen und Herren, ich bin Max Mustermann aus Dornbirn, Marktstraße 5. Meine Bestellung wurde nicht geliefert. Erreichbar unter max.mustermann@gmail.com oder 0664/1234567. Kundennummer KD-88421.","metadata":{"channel":"email"}}'

show_entry 2 "Positives Feedback (kein PII)" \
  "Super Frischeprodukte heute! Die Bio-Äpfel aus Vorarlberg waren top. Personal sehr freundlich. Komme gerne wieder!" \
  '{"tenant_id":"demo","source":"app_review","content":"Super Frischeprodukte heute! Die Bio-Äpfel aus Vorarlberg waren top. Personal sehr freundlich. Komme gerne wieder!","metadata":{"rating":5}}'

show_entry 3 "Preisbeschwerde (IBAN + E-Mail)" \
  "Hallo, ich bin Maria Schneider, seit 15 Jahren Stammkundin. Wurde 3,20€ zu viel verrechnet. Bitte erstatten. E-Mail: m.schneider@gmx.at, IBAN AT12 3456 7890 1234 5678." \
  '{"tenant_id":"demo","source":"web_form","content":"Hallo, ich bin Maria Schneider, seit 15 Jahren Stammkundin. Wurde 3,20€ zu viel verrechnet. Bitte erstatten. E-Mail: m.schneider@gmx.at, IBAN AT12 3456 7890 1234 5678.","metadata":{"channel":"web"}}'

show_entry 4 "Produktanfrage (Name + Ort)" \
  "Grüß Gott, führt ihr Dinkelmehl Type 1050? Ich backe jedes Wochenende Brot. Falls ja, ist es online bestellbar? LG, Thomas aus Bludenz" \
  '{"tenant_id":"demo","source":"whatsapp","content":"Grüß Gott, führt ihr Dinkelmehl Type 1050? Ich backe jedes Wochenende Brot. Falls ja, ist es online bestellbar? LG, Thomas aus Bludenz","metadata":{"channel":"whatsapp"}}'

show_entry 5 "Hygiene-Beschwerde (kritisch)" \
  "Guten Tag, Anna Fink hier, anna.fink@icloud.com. Im Markt Bregenz hat ein Mitarbeiter ohne Handschuhe rohes Fleisch und dann direkt Käse für mich angefasst. Gravierendes Hygieneproblem!" \
  '{"tenant_id":"demo","source":"email","content":"Guten Tag, Anna Fink hier, anna.fink@icloud.com. Im Markt Bregenz hat ein Mitarbeiter ohne Handschuhe rohes Fleisch und dann direkt Käse für mich angefasst. Gravierendes Hygieneproblem!","metadata":{"severity":"critical"}}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 ZUSAMMENFASSUNG ALLER SIGNALE:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
curl -s "$API/api/v1/signals?tenant_id=demo" | python3 -c "
import json,sys
data = json.load(sys.stdin)
items = data.get('signals', data) if isinstance(data, dict) else data
print(f'  Verarbeitet: {len(items)} Einträge')
print(f'  ☁️  Cloud-AI sieht NUR diese anonymen Signale – KEINE Rohdaten!')
print('')
for s in items:
    print(f'  [{s.get(\"signal_id\",\"?\")}] {s.get(\"category\",\"?\"):<25} | {s.get(\"urgency\",\"?\"):<8} | {s.get(\"sentiment\",0):+.2f}')
" 2>/dev/null
echo ""
echo "✅ Fertig! Dashboard: http://localhost:8443"
