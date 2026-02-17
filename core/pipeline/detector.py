"""PII detection module using regex patterns."""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


# Regex patterns for PII detection
PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone_at": r'\b(?:\+43|0043|0)\s*\d{1,4}\s*\d{3,4}\s*\d{3,4}\b',
    "phone_de": r'\b(?:\+49|0049|0)\s*\d{2,4}\s*\d{3,4}\s*\d{3,4}\b',
    "iban": r'\b[A-Z]{2}\d{2}\s?(?:\d{4}\s?){3,7}\d{1,4}\b',
    "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "austrian_ssn": r'\b\d{4}\s?\d{6}\b',  # Austrian social security number format
}


def detect_pii(content: str) -> List[Dict[str, Any]]:
    """
    Detect PII entities in text using regex patterns.

    This is a privacy-first detection approach that runs locally
    without sending data to external services.

    Args:
        content: Text content to scan for PII

    Returns:
        List of detected PII entities with type, value, and position
    """
    detections = []

    for pii_type, pattern in PATTERNS.items():
        for match in re.finditer(pattern, content, re.IGNORECASE):
            detections.append({
                "type": pii_type,
                "value": match.group(0),
                "start": match.start(),
                "end": match.end(),
                "confidence": 1.0
            })

    # Sort by start position
    detections.sort(key=lambda x: x["start"])

    logger.info(f"Detected {len(detections)} PII entities: {dict((d['type'], sum(1 for x in detections if x['type'] == d['type'])) for d in detections)}")

    return detections
