"""Ingest endpoint for processing customer feedback."""
import json
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extras import Json

from config import settings
from models.schemas import IngestRequest, IngestResponse
from pipeline.detector import detect_pii
from pipeline.anonymizer import anonymize_content
from pipeline.analyzer import analyze_content
from pipeline.audit_logger import log_audit_event

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest_feedback(request: IngestRequest):
    """
    Ingest customer feedback through the complete privacy pipeline.

    Steps:
    1. Detect PII in the content
    2. Pseudonymize detected PII
    3. Analyze anonymized content with LLM
    4. Store signal in database
    5. Log audit trail

    Args:
        request: IngestRequest containing tenant_id, content, source, and metadata

    Returns:
        IngestResponse: Processing result with signal_id and analysis
    """
    try:
        # Generate signal ID
        signal_id = f"sig_{uuid.uuid4().hex[:12]}"
        logger.info(f"Processing feedback for tenant {request.tenant_id}, signal {signal_id}")

        # Step 1: Detect PII
        pii_detections = detect_pii(request.content)
        logger.info(f"Detected {len(pii_detections)} PII entities")

        # Step 2: Anonymize content
        anonymized_content, pseudonym_mappings = anonymize_content(
            request.content,
            pii_detections,
            request.tenant_id
        )
        logger.info(f"Anonymized content with {len(pseudonym_mappings)} pseudonyms")

        # Step 3: Analyze with LLM
        analysis = await analyze_content(anonymized_content)
        logger.info(f"Analysis complete: category={analysis.category}, urgency={analysis.urgency}")

        # Step 4: Store signal in database
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO signals
                    (tenant_id, signal_id, category, urgency, sentiment, anonymized_content, metadata, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    request.tenant_id,
                    signal_id,
                    analysis.category,
                    analysis.urgency,
                    analysis.sentiment,
                    anonymized_content,
                    Json({
                        "source": request.source,
                        "pii_count": len(pii_detections),
                        "original_metadata": request.metadata,
                        "summary": analysis.summary
                    }),
                    datetime.utcnow(),
                    datetime.utcnow()
                ))
                conn.commit()
                logger.info(f"Signal {signal_id} stored in database")
        finally:
            conn.close()

        # Step 5: Log audit event
        await log_audit_event(
            tenant_id=request.tenant_id,
            signal_id=signal_id,
            action="INGEST",
            actor="system",
            details={
                "source": request.source,
                "pii_detected": len(pii_detections),
                "pii_types": list(set(p["type"] for p in pii_detections)),
                "category": analysis.category,
                "urgency": analysis.urgency
            }
        )

        # Return response
        return IngestResponse(
            signal_id=signal_id,
            status="processed",
            pii_detected=len(pii_detections),
            category=analysis.category,
            urgency=analysis.urgency,
            sentiment=analysis.sentiment,
            anonymized_preview=anonymized_content[:200] + "..." if len(anonymized_content) > 200 else anonymized_content
        )

    except Exception as e:
        logger.error(f"Failed to process feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
