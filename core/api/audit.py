"""Audit log endpoints."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from models.schemas import AuditLogEntry, AuditLogResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


@router.get("/audit-log", response_model=AuditLogResponse)
async def get_audit_log(
    tenant_id: str = Query(..., description="Tenant identifier"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    signal_id: Optional[str] = Query(None, description="Filter by signal ID"),
    action: Optional[str] = Query(None, description="Filter by action type")
):
    """
    Retrieve audit log entries for a tenant.

    The audit log provides a complete trail of all operations performed on signals,
    supporting DSGVO compliance and transparency requirements.

    Args:
        tenant_id: Tenant identifier
        limit: Maximum number of entries (1-500)
        offset: Number of entries to skip for pagination
        signal_id: Optional filter for specific signal
        action: Optional filter for action type

    Returns:
        AuditLogResponse: List of audit log entries with total count
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Build query with filters
                query = "SELECT * FROM audit_log WHERE tenant_id = %s"
                params = [tenant_id]

                if signal_id:
                    query += " AND signal_id = %s"
                    params.append(signal_id)

                if action:
                    query += " AND action = %s"
                    params.append(action)

                # Get total count
                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cur.execute(count_query, params)
                total = cur.fetchone()["count"]

                # Get paginated results
                query += " ORDER BY timestamp DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cur.execute(query, params)
                entries = cur.fetchall()

                return AuditLogResponse(
                    total=total,
                    entries=[AuditLogEntry(**entry) for entry in entries]
                )
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to retrieve audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audit log: {str(e)}")
