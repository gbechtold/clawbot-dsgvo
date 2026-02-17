"""Compliance reporting endpoints."""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from models.schemas import ComplianceReport

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


@router.get("/compliance/report", response_model=ComplianceReport)
async def generate_compliance_report(
    tenant_id: str = Query(..., description="Tenant identifier")
):
    """
    Generate a DSGVO compliance report for a tenant.

    The report includes:
    - Total signals processed
    - PII entities anonymized
    - Audit trail completeness
    - Overall compliance status

    Args:
        tenant_id: Tenant identifier

    Returns:
        ComplianceReport: Comprehensive compliance statistics
    """
    try:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # Count total signals
                cur.execute(
                    "SELECT COUNT(*) as count FROM signals WHERE tenant_id = %s",
                    (tenant_id,)
                )
                total_signals = cur.fetchone()["count"]

                # Count PII anonymizations
                cur.execute(
                    "SELECT COUNT(*) as count FROM pseudonym_mapping WHERE tenant_id = %s",
                    (tenant_id,)
                )
                pii_anonymized = cur.fetchone()["count"]

                # Count audit entries
                cur.execute(
                    "SELECT COUNT(*) as count FROM audit_log WHERE tenant_id = %s",
                    (tenant_id,)
                )
                audit_entries = cur.fetchone()["count"]

                # Get category breakdown
                cur.execute(
                    """
                    SELECT category, COUNT(*) as count
                    FROM signals
                    WHERE tenant_id = %s
                    GROUP BY category
                    """,
                    (tenant_id,)
                )
                category_stats = {row["category"]: row["count"] for row in cur.fetchall()}

                # Get urgency breakdown
                cur.execute(
                    """
                    SELECT urgency, COUNT(*) as count
                    FROM signals
                    WHERE tenant_id = %s
                    GROUP BY urgency
                    """,
                    (tenant_id,)
                )
                urgency_stats = {row["urgency"]: row["count"] for row in cur.fetchall()}

                # Get PII type breakdown
                cur.execute(
                    """
                    SELECT pii_type, COUNT(*) as count
                    FROM pseudonym_mapping
                    WHERE tenant_id = %s
                    GROUP BY pii_type
                    """,
                    (tenant_id,)
                )
                pii_type_stats = {row["pii_type"]: row["count"] for row in cur.fetchall()}

                # Determine compliance status
                compliance_status = "compliant"
                if total_signals > 0 and audit_entries == 0:
                    compliance_status = "warning"
                elif total_signals == 0:
                    compliance_status = "no_data"

                return ComplianceReport(
                    tenant_id=tenant_id,
                    report_date=datetime.utcnow(),
                    total_signals=total_signals,
                    pii_anonymized=pii_anonymized,
                    audit_entries=audit_entries,
                    compliance_status=compliance_status,
                    details={
                        "categories": category_stats,
                        "urgency_levels": urgency_stats,
                        "pii_types": pii_type_stats,
                        "anonymization_rate": round(pii_anonymized / max(total_signals, 1), 2),
                        "audit_coverage": round(audit_entries / max(total_signals, 1), 2)
                    }
                )
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
