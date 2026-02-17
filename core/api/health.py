"""Health check endpoint."""
import logging
from fastapi import APIRouter, HTTPException
import psycopg2
import httpx

from config import settings
from models.schemas import HealthResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of all services.

    Returns:
        HealthResponse: Health status of the application and its dependencies
    """
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "ollama": "unknown",
        "version": "1.0.0"
    }

    # Check database
    try:
        conn = psycopg2.connect(settings.database_url)
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            if result and result[0] == 1:
                health_status["database"] = "healthy"
            else:
                health_status["database"] = "unhealthy"
        conn.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_url}/api/tags")
            if response.status_code == 200:
                health_status["ollama"] = "healthy"
            else:
                health_status["ollama"] = "unhealthy"
                health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        health_status["ollama"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status
