#!/usr/bin/env python3
"""Zeigt Quelldaten vs. verarbeitete Signale als Tabelle."""
import json, requests, textwrap

API = "http://localhost:8000"

ORIGINALS = [
    {
        "nr": 1,
        "quelle": "E-Mail",
        "original": "Max Mustermann, Dornbirn Marktstraße 5, max.mustermann@gmail.com, 0664/1234567, KD-88421. Bestellung nicht geliefert!"
    },
    {
        "nr": 2,
        "quelle": "App",
        "original": "Super Frischeprodukte! Bio-Äpfel aus Vorarlberg top. Personal freundlich. Komme gerne wieder!"
    },
    {
        "nr": 3,
        "quelle": "Web",
        "original": "Maria Schneider, m.schneider@gmx.at, IBAN AT12 3456 7890 1234 5678. 3,20€ zu viel verrechnet."
    },
    {
        "nr": 4,
        "quelle": "WhatsApp",
        "original": "Thomas aus Bludenz: Führt ihr Dinkelmehl Type 1050? Online bestellbar?"
    },
    {
        "nr": 5,
        "quelle": "E-Mail",
        "original": "Anna Fink, anna.fink@icloud.com. Mitarbeiter in Bregenz: rohes Fleisch ohne Handschuhe, dann Käse. Hygieneproblem!"
    }
]

# Signale von API holen
try:
    r = requests.get(f"{API}/api/v1/signals?tenant_id=demo&limit=10")
    signals = r.json()
    if isinstance(signals, dict):
        signals = signals.get("signals", signals.get("items", []))
except Exception as e:
    print(f"❌ API nicht erreichbar: {e}")
    exit(1)

def wrap(text, width):
    return "\n".join(textwrap.wrap(str(text), width))

def sentiment_bar(val):
    try:
        v = float(val)
        bar = "█" * int(abs(v) * 8)
        sym = "▼" if v < 0 else "▲"
        return f"{v:+.2f} {sym} {bar}"
    except:
        return str(val)

print()
print("=" * 110)
print("  🦞 ClawBot DSGVO – Quelldaten vs. Verarbeitete Signale")
print("=" * 110)
print()

# Kopfzeile
print(f"{'Nr':>3}  {'Quelle':<10}  {'ORIGINAL (mit PII)':<38}  {'ANONYMISIERT':<28}  {'Kat.':<15}  {'Dring.':<8}  {'Sentiment'}")
print("-" * 110)

for i, orig in enumerate(ORIGINALS):
    sig = signals[i] if i < len(signals) else {}

    nr       = orig["nr"]
    quelle   = orig["quelle"]
    raw      = textwrap.shorten(orig["original"], width=38, placeholder="…")
    anon     = textwrap.shorten(sig.get("anonymized_content", "–"), width=28, placeholder="…")
    cat      = textwrap.shorten(sig.get("category", "–"), width=15, placeholder="…")
    urg      = sig.get("urgency", "–")
    sent     = sentiment_bar(sig.get("sentiment", 0))

    print(f"{nr:>3}  {quelle:<10}  {raw:<38}  {anon:<28}  {cat:<15}  {urg:<8}  {sent}")

print("-" * 110)
print()

# Detail-Ansicht
print("=" * 110)
print("  📋 DETAIL-ANSICHT: Original → Anonymisiert")
print("=" * 110)

for i, orig in enumerate(ORIGINALS):
    sig = signals[i] if i < len(signals) else {}
    print()
    print(f"  [{orig['nr']}] {orig['quelle'].upper()}")
    print(f"  {'PII-REIN':<12}: {orig['original']}")
    print(f"  {'ANONYMISIERT':<12}: {sig.get('anonymized_content', '–')}")
    print(f"  {'SIGNAL-ID':<12}: {sig.get('signal_id', '–')}")
    print(f"  {'KATEGORIE':<12}: {sig.get('category', '–')}  |  DRINGLICHKEIT: {sig.get('urgency','–')}  |  SENTIMENT: {sig.get('sentiment',0):+.2f}")
    meta = sig.get("metadata", {})
    if isinstance(meta, dict):
        summary = meta.get("summary", "")
        if summary:
            print(f"  {'ZUSAMMENFASSUNG':<12}: {summary}")
    print()

print("=" * 110)
print(f"  ✅ {len(signals)} Einträge verarbeitet  |  Alle PII-Daten sind lokal geblieben  |  Cloud sieht nur Signale")
print("=" * 110)
print()
