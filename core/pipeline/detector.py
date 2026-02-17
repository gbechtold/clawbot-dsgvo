"""PII detection module using regex patterns for German/Austrian text."""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Core regex patterns
PATTERNS = {
    "email":        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone_at":     r'\b(?:\+43|0043|0)\s*\d{1,4}[\s/\-]?\d{3,4}[\s/\-]?\d{3,4}\b',
    "phone_de":     r'\b(?:\+49|0049)\s*\d{2,4}[\s/\-]?\d{3,4}[\s/\-]?\d{3,4}\b',
    "iban":         r'\b[A-Z]{2}\d{2}(?:\s?\d{4}){3,7}\s?\d{1,4}\b',
    "ip_address":   r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    "credit_card":  r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "austrian_ssn": r'\b\d{4}\s?\d{6}\b',
    "postal_code_at": r'\b[1-9]\d{3}\b(?=\s+[A-ZÄÖÜ][a-zäöüß])',  # AT PLZ vor Ortsname
}

# Häufige österreichische/deutsche Vor- und Nachnamen (erweiterbar)
FIRST_NAMES = {
    "max","moritz","hans","peter","paul","franz","karl","thomas","michael","stefan",
    "christian","markus","andreas","david","martin","florian","sebastian","alexander",
    "lukas","simon","anna","maria","lisa","julia","sarah","laura","katharina","eva",
    "sophie","lena","emma","hannah","nina","claudia","andrea","petra","monika","susanne",
    "maria","marie","guntram","willi","günter","helmut","gerhard","walter","werner",
    "ewald","alfred","heinz","dieter","reinhard","jürgen","manfred","rainer",
}

LAST_NAME_INDICATORS = [
    r'\b(?:Herr|Frau|Dr\.|Mag\.|DI|Ing\.)\s+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)*)',
    r'\bich\s+(?:bin|heiße|heiß)\s+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)',
    r'\b(?:mein\s+Name\s+ist|meine\s+Name\s+ist)\s+([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)',
    r'\bLG[,\s]+([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)',  # "LG, Thomas"
    r'\b([A-ZÄÖÜ][a-zäöüß]+\s+[A-ZÄÖÜ][a-zäöüß]+)\s+hier\b',       # "Anna Fink hier"
]


def detect_pii(content: str) -> List[Dict[str, Any]]:
    """
    Detect PII entities in German/Austrian text using regex patterns.

    Erkennt: E-Mails, Telefonnummern (AT/DE), IBAN, Namen, IPs, PLZ.

    Args:
        content: Text content to scan for PII

    Returns:
        List of detected PII entities with type, value, start, end, confidence
    """
    detections = []
    found_spans: List[tuple] = []  # Verhindert Doppel-Matches

    def add_detection(pii_type: str, value: str, start: int, end: int, confidence: float = 1.0):
        # Überlappungen verhindern
        for (s, e) in found_spans:
            if not (end <= s or start >= e):
                return
        found_spans.append((start, end))
        detections.append({
            "type": pii_type,
            "value": value,
            "start": start,
            "end": end,
            "confidence": confidence,
        })

    # 1. Regex-Patterns
    for pii_type, pattern in PATTERNS.items():
        for match in re.finditer(pattern, content, re.IGNORECASE):
            add_detection(pii_type, match.group(0), match.start(), match.end())

    # 2. Vorname-Erkennung (case-insensitive Wortliste)
    words = re.finditer(r'\b([A-ZÄÖÜ][a-zäöüß]{2,})\b', content)
    for match in words:
        if match.group(1).lower() in FIRST_NAMES:
            add_detection("first_name", match.group(1), match.start(), match.end(), 0.85)

    # 3. Vollständige Namen via Kontext-Patterns
    for pattern in LAST_NAME_INDICATORS:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            name = match.group(1)
            start = content.find(name, match.start())
            if start >= 0:
                add_detection("full_name", name, start, start + len(name), 0.90)

    # Sortieren nach Position
    detections.sort(key=lambda x: x["start"])

    type_counts = {}
    for d in detections:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1
    logger.info(f"PII erkannt: {len(detections)} Felder – {type_counts}")

    return detections
