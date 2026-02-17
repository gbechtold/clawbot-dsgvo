"""Pydantic schemas for ClawBot API."""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr


class IngestRequest(BaseModel):
    """Request model for ingesting customer feedback."""
    tenant_id: str = Field(..., description="Tenant identifier")
    content: str = Field(..., description="Customer feedback content")
    source: str = Field(default="email", description="Source of the feedback")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class PIIDetection(BaseModel):
    """Model for detected PII."""
    type: str = Field(..., description="Type of PII (email, phone, etc.)")
    value: str = Field(..., description="Original PII value")
    start: int = Field(..., description="Start position in text")
    end: int = Field(..., description="End position in text")
    confidence: float = Field(default=1.0, description="Detection confidence score")


class AnalysisResult(BaseModel):
    """Model for LLM analysis result."""
    category: str = Field(..., description="Feedback category")
    urgency: str = Field(..., description="Urgency level (low, medium, high, critical)")
    sentiment: float = Field(default=0.0, description="Sentiment score -1.0 (very negative) to +1.0 (very positive)")
    summary: Optional[str] = Field(None, description="Brief summary")


class IngestResponse(BaseModel):
    """Response model for ingest endpoint."""
    signal_id: str = Field(..., description="Generated signal ID")
    status: str = Field(..., description="Processing status")
    pii_detected: int = Field(..., description="Number of PII entities detected")
    category: str = Field(..., description="Categorized feedback type")
    urgency: str = Field(..., description="Urgency level")
    sentiment: float = Field(default=0.0, description="Sentiment score -1.0 to +1.0")
    anonymized_preview: str = Field(..., description="Preview of anonymized content")


class Signal(BaseModel):
    """Model for a processed signal."""
    id: int = Field(..., description="Database ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    signal_id: str = Field(..., description="Unique signal identifier")
    category: str = Field(..., description="Signal category")
    urgency: str = Field(..., description="Urgency level")
    sentiment: float = Field(default=0.0, description="Sentiment score -1.0 to +1.0")
    anonymized_content: str = Field(..., description="Anonymized content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SignalListResponse(BaseModel):
    """Response model for signal list."""
    total: int = Field(..., description="Total number of signals")
    signals: List[Signal] = Field(..., description="List of signals")


class AuditLogEntry(BaseModel):
    """Model for an audit log entry."""
    id: int = Field(..., description="Database ID")
    tenant_id: str = Field(..., description="Tenant identifier")
    signal_id: Optional[str] = Field(None, description="Related signal ID")
    action: str = Field(..., description="Action performed")
    actor: Optional[str] = Field(None, description="Actor who performed the action")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    timestamp: datetime = Field(..., description="Action timestamp")


class AuditLogResponse(BaseModel):
    """Response model for audit log."""
    total: int = Field(..., description="Total number of audit entries")
    entries: List[AuditLogEntry] = Field(..., description="List of audit entries")


class ComplianceReport(BaseModel):
    """Model for compliance report."""
    tenant_id: str = Field(..., description="Tenant identifier")
    report_date: datetime = Field(..., description="Report generation date")
    total_signals: int = Field(..., description="Total signals processed")
    pii_anonymized: int = Field(..., description="Total PII entities anonymized")
    audit_entries: int = Field(..., description="Total audit log entries")
    compliance_status: str = Field(..., description="Overall compliance status")
    details: Dict[str, Any] = Field(..., description="Detailed statistics")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    database: str = Field(..., description="Database connection status")
    ollama: str = Field(..., description="Ollama service status")
    version: str = Field(..., description="Application version")
