"""Main FastAPI application for ClawBot."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

from config import settings
from api import health, ingest, signals, audit, compliance


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Create a database connection."""
    return psycopg2.connect(
        settings.database_url,
        cursor_factory=RealDictCursor
    )


def init_database():
    """Initialize database schema."""
    logger.info("Initializing database schema...")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create signals table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    signal_id VARCHAR(255) UNIQUE NOT NULL,
                    category VARCHAR(100),
                    urgency VARCHAR(50),
                    sentiment VARCHAR(50),
                    anonymized_content TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create audit_log table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    signal_id VARCHAR(255),
                    action VARCHAR(100) NOT NULL,
                    actor VARCHAR(255),
                    details JSONB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create pseudonym_mapping table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pseudonym_mapping (
                    id SERIAL PRIMARY KEY,
                    tenant_id VARCHAR(255) NOT NULL,
                    original_hash VARCHAR(255) NOT NULL,
                    pseudonym VARCHAR(255) NOT NULL,
                    pii_type VARCHAR(50) NOT NULL,
                    encrypted_original TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, original_hash)
                )
            """)

            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_tenant ON signals(tenant_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_log(tenant_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_audit_signal ON audit_log(signal_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_pseudonym_tenant ON pseudonym_mapping(tenant_id)")

            conn.commit()
            logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ClawBot DSGVO MVP...")
    try:
        init_database()
        logger.info("ClawBot is ready!")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down ClawBot...")


# Create FastAPI app
app = FastAPI(
    title="ClawBot DSGVO MVP",
    description="Privacy-first customer feedback processing with DSGVO compliance",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Ingest"])
app.include_router(signals.router, prefix="/api/v1", tags=["Signals"])
app.include_router(audit.router, prefix="/api/v1", tags=["Audit"])
app.include_router(compliance.router, prefix="/api/v1", tags=["Compliance"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "ClawBot DSGVO MVP",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }
