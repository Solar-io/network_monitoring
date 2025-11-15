"""Pydantic schemas for validation and API responses."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Host Schemas
class HostBase(BaseModel):
    """Base host schema."""

    name: str = Field(..., min_length=1, max_length=255)
    host_id: str = Field(..., min_length=1, max_length=100)
    cron_expression: Optional[str] = None  # Cron expression for heartbeat frequency
    expected_frequency_seconds: int = Field(default=300, gt=0)  # Fallback if no cron
    schedule_type: str = Field(default="always")
    schedule_config: Optional[str] = None
    grace_period_seconds: int = Field(default=60, gt=0)
    log_analysis_config: Optional[str] = None


class HostCreate(HostBase):
    """Schema for creating a host."""

    token: str = Field(..., min_length=8)


class HostUpdate(BaseModel):
    """Schema for updating a host."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    cron_expression: Optional[str] = None
    expected_frequency_seconds: Optional[int] = Field(None, gt=0)
    schedule_type: Optional[str] = None
    schedule_config: Optional[str] = None
    grace_period_seconds: Optional[int] = Field(None, gt=0)
    log_analysis_config: Optional[str] = None


class HostResponse(HostBase):
    """Schema for host API responses."""

    id: int
    heartbeat_url: Optional[str] = None
    last_seen: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HostStatus(BaseModel):
    """Simplified host status."""

    id: int
    name: str
    host_id: str
    status: str
    last_seen: Optional[datetime] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True


# Heartbeat Schemas
class HeartbeatCreate(BaseModel):
    """Schema for creating a heartbeat."""

    host_id: str
    source_ip: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class HeartbeatResponse(BaseModel):
    """Schema for heartbeat API responses."""

    id: int
    host_id: int
    timestamp: datetime
    source_ip: Optional[str] = None

    class Config:
        from_attributes = True


# Alert Schemas
class AlertCreate(BaseModel):
    """Schema for creating an alert."""

    host_id: Optional[int] = None
    alert_type: str = Field(..., min_length=1, max_length=50)
    severity: str = Field(default="warning")
    message: str = Field(..., min_length=1)
    details: Optional[Dict[str, Any]] = None


class AlertResponse(BaseModel):
    """Schema for alert API responses."""

    id: int
    host_id: Optional[int] = None
    alert_type: str
    severity: str
    message: str
    details: Optional[str] = None
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Log Analysis Schemas
class LogAnalysisCreate(BaseModel):
    """Schema for creating log analysis record."""

    host_id: int
    log_source: str
    lines_analyzed: Optional[int] = None
    llm_model: Optional[str] = None
    findings: Optional[List[Dict[str, Any]]] = None
    severity: Optional[str] = None


class LogAnalysisResponse(BaseModel):
    """Schema for log analysis API responses."""

    id: int
    host_id: int
    log_source: str
    lines_analyzed: Optional[int] = None
    llm_model: Optional[str] = None
    findings: Optional[str] = None
    severity: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Health Check Schema
class HealthResponse(BaseModel):
    """Schema for health check endpoint."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"
    database: str = "connected"
    services: Dict[str, str] = Field(default_factory=dict)


# Dashboard Schema
class DashboardResponse(BaseModel):
    """Schema for dashboard data."""

    hosts: List[HostStatus]
    recent_alerts: List[AlertResponse]
    total_hosts: int
    hosts_up: int
    hosts_down: int
    hosts_unknown: int
    last_updated: datetime


# Authentication
class HeartbeatAuth(BaseModel):
    """Authentication for heartbeat endpoint."""

    token: str = Field(..., min_length=8)
