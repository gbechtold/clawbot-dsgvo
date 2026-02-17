"""Signals endpoints for retrieving processed feedback."""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from models.schemas import Signal, SignalListResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


@router.get("/signals", response_model=SignalListResponse)
async def list_signals(
    tenant_id: str = Query(..., description="Tenant identifier"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of signals to return"),
    offset: int = Query(0, ge=0, description="Number of signals to skip"),
    category: Optional[str] = Query(None, description="Filter by category"),
    urgency: Optional[str] = Query(None, description="Filter by urgency level")
):
    """
    Retrieve a list of processed signals for a tenant.

    Args:
        tenant_id: Tenant identifier
        limit: Maximum number of results (1-100)
        offset: Number of results to skip for pagination
        category: Optional category filter
        urgency: Optional urgency filter

    Returns:
        SignalListResponse: List of signals with total count
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Build query with filters
                query = "SELECT * FROM signals WHERE tenant_id = %s"
                params = [tenant_id]

                if category:
                    query += " AND category = %s"
                    params.append(category)

                if urgency:
                    query += " AND urgency = %s"
                    params.append(urgency)

                # Get total count
                count_query = query.replace("SELECT *", "SELECT COUNT(*)")
                cur.execute(count_query, params)
                total = cur.fetchone()["count"]

                # Get paginated results
                query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                cur.execute(query, params)
                signals = cur.fetchall()

                return SignalListResponse(
                    total=total,
                    signals=[Signal(**signal) for signal in signals]
                )
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to retrieve signals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve signals: {str(e)}")


@router.get("/signals/{signal_id}", response_model=Signal)
async def get_signal(
    signal_id: str,
    tenant_id: str = Query(..., description="Tenant identifier")
):
    """
    Retrieve a specific signal by ID.

    Args:
        signal_id: Unique signal identifier
        tenant_id: Tenant identifier for authorization

    Returns:
        Signal: The requested signal

    Raises:
        HTTPException: If signal not found or access denied
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM signals WHERE signal_id = %s AND tenant_id = %s",
                    (signal_id, tenant_id)
                )
                signal = cur.fetchone()

                if not signal:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Signal {signal_id} not found for tenant {tenant_id}"
                    )

                return Signal(**signal)
        finally:
            conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve signal {signal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve signal: {str(e)}")
