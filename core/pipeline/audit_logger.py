"""Audit logging module for DSGVO compliance."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor, Json

from config import settings

logger = logging.getLogger(__name__)


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


async def log_audit_event(
    tenant_id: str,
    action: str,
    signal_id: Optional[str] = None,
    actor: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event for DSGVO compliance.

    All operations on customer data are logged to provide a complete audit trail,
    supporting transparency and accountability requirements.

    Args:
        tenant_id: Tenant identifier
        action: Action performed (INGEST, ACCESS, EXPORT, DELETE, etc.)
        signal_id: Optional signal identifier
        actor: Optional actor (user, system, etc.)
        details: Optional additional details about the action
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO audit_log
                    (tenant_id, signal_id, action, actor, details, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        tenant_id,
                        signal_id,
                        action,
                        actor or "system",
                        Json(details) if details else None,
                        datetime.utcnow()
                    )
                )
                conn.commit()
                logger.debug(f"Logged audit event: {action} for tenant {tenant_id}")
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}", exc_info=True)
        # Don't raise - audit logging failure shouldn't break the main flow
