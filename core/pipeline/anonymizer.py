"""Anonymization module with pseudonymization and encryption."""
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from cryptography.fernet import Fernet
import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings

logger = logging.getLogger(__name__)


# Fun Austrian-themed animal names for pseudonyms
ADJECTIVES = [
    "alpine", "sunny", "snowy", "cozy", "foggy", "misty", "breezy", "rocky",
    "meadow", "crystal", "golden", "silver", "munchy", "happy", "sleepy", "zippy",
    "bouncy", "fluffy", "wise", "brave"
]

ANIMALS = [
    "marmot", "chamois", "ibex", "deer", "eagle", "otter", "beaver", "fox",
    "badger", "lynx", "owl", "falcon", "hare", "squirrel", "hedgehog", "trout",
    "salamander", "bat", "woodpecker", "bear"
]


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


def get_cipher():
    """Get Fernet cipher for encryption."""
    # Ensure key is properly formatted for Fernet
    key = settings.encryption_key.encode() if isinstance(settings.encryption_key, str) else settings.encryption_key
    return Fernet(key)


def generate_pseudonym(original_value: str, pii_type: str) -> str:
    """
    Generate a fun, deterministic pseudonym from the original value.

    Args:
        original_value: The original PII value
        pii_type: Type of PII (email, phone, etc.)

    Returns:
        A fun pseudonym like "alpine-marmot" or "munchy-otter"
    """
    # Create hash for deterministic selection
    hash_value = int(hashlib.sha256(original_value.encode()).hexdigest(), 16)

    adjective = ADJECTIVES[hash_value % len(ADJECTIVES)]
    animal = ANIMALS[(hash_value // len(ADJECTIVES)) % len(ANIMALS)]

    # Add type-specific suffix
    suffix_map = {
        "email": "@example.local",
        "phone_at": ".at",
        "phone_de": ".de",
        "iban": ".iban",
        "ip_address": ".ip",
        "credit_card": ".card",
        "austrian_ssn": ".ssn"
    }
    suffix = suffix_map.get(pii_type, "")

    return f"{adjective}-{animal}{suffix}"


def get_or_create_pseudonym(
    original_value: str,
    pii_type: str,
    tenant_id: str
) -> str:
    """
    Get existing pseudonym or create a new one for a PII value.

    This ensures consistency: the same PII value always maps to the same pseudonym
    within a tenant, supporting data linkage while maintaining privacy.

    Args:
        original_value: The original PII value
        pii_type: Type of PII
        tenant_id: Tenant identifier

    Returns:
        Pseudonym for the PII value
    """
    # Create hash of original value for lookup
    original_hash = hashlib.sha256(f"{tenant_id}:{original_value}".encode()).hexdigest()

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if pseudonym exists
            cur.execute(
                "SELECT pseudonym FROM pseudonym_mapping WHERE tenant_id = %s AND original_hash = %s",
                (tenant_id, original_hash)
            )
            result = cur.fetchone()

            if result:
                return result["pseudonym"]

            # Create new pseudonym
            pseudonym = generate_pseudonym(original_value, pii_type)

            # Encrypt original value
            cipher = get_cipher()
            encrypted_original = cipher.encrypt(original_value.encode()).decode()

            # Store mapping
            cur.execute(
                """
                INSERT INTO pseudonym_mapping
                (tenant_id, original_hash, pseudonym, pii_type, encrypted_original)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, original_hash) DO NOTHING
                """,
                (tenant_id, original_hash, pseudonym, pii_type, encrypted_original)
            )
            conn.commit()

            return pseudonym
    finally:
        conn.close()


def anonymize_content(
    content: str,
    pii_detections: List[Dict[str, Any]],
    tenant_id: str
) -> Tuple[str, List[Dict[str, str]]]:
    """
    Anonymize content by replacing PII with pseudonyms.

    Args:
        content: Original content with PII
        pii_detections: List of detected PII entities
        tenant_id: Tenant identifier

    Returns:
        Tuple of (anonymized_content, pseudonym_mappings)
    """
    if not pii_detections:
        return content, []

    # Sort detections by position (reverse order to maintain positions during replacement)
    sorted_detections = sorted(pii_detections, key=lambda x: x["start"], reverse=True)

    anonymized = content
    mappings = []

    for detection in sorted_detections:
        original_value = detection["value"]
        pii_type = detection["type"]
        start = detection["start"]
        end = detection["end"]

        # Get or create pseudonym
        pseudonym = get_or_create_pseudonym(original_value, pii_type, tenant_id)

        # Replace in content
        anonymized = anonymized[:start] + f"[{pseudonym}]" + anonymized[end:]

        mappings.append({
            "type": pii_type,
            "pseudonym": pseudonym,
            "position": start
        })

    logger.info(f"Anonymized content with {len(mappings)} replacements")

    return anonymized, mappings
