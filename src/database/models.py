"""SQLAlchemy database models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.database.db import Base


class Host(Base):
    """Host configuration and status."""

    __tablename__ = "hosts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    host_id = Column(String(100), unique=True, nullable=False, index=True)
    token = Column(String(255), nullable=False)

    # Heartbeat configuration
    heartbeat_url = Column(String(500), nullable=True)
    cron_expression = Column(String(255), nullable=True)  # Cron expression for heartbeat frequency
    expected_frequency_seconds = Column(Integer, nullable=False, default=300)  # Fallback/calculated frequency
    schedule_type = Column(
        String(50), nullable=False, default="always"
    )  # 'always', 'business_hours', 'custom'
    schedule_config = Column(Text, nullable=True)  # JSON for custom schedules
    grace_period_seconds = Column(Integer, nullable=False, default=60)

    # Status
    last_seen = Column(DateTime, nullable=True)
    status = Column(
        String(20), nullable=False, default="unknown"
    )  # 'up', 'down', 'unknown'

    # Log analysis configuration (JSON)
    log_analysis_config = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    heartbeats = relationship("Heartbeat", back_populates="host", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="host", cascade="all, delete-orphan")
    log_analyses = relationship(
        "LogAnalysis", back_populates="host", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Host(id={self.id}, name={self.name}, status={self.status})>"

    def is_overdue(self, current_time: Optional[datetime] = None) -> bool:
        """
        Check if host heartbeat is overdue, taking schedule into account.

        For 'always' schedule: Alert if time since last heartbeat exceeds frequency + grace.
        For 'business_hours'/'custom' schedule: Only check frequency within the monitoring window.
        - If last heartbeat was before current window started, wait for window_start + frequency + grace
        - If last heartbeat was within current window, use normal frequency + grace logic
        """
        if not self.last_seen:
            return True

        current_time = current_time or datetime.utcnow()
        threshold = self.expected_frequency_seconds + self.grace_period_seconds

        # For 'always' schedule, use simple elapsed time check
        if self.schedule_type == "always":
            elapsed = (current_time - self.last_seen).total_seconds()
            return elapsed > threshold

        # For scheduled monitoring (business_hours, custom), be aware of monitoring windows
        if self.schedule_type in ["business_hours", "custom"]:
            from src.utils.schedule_utils import should_monitor_host, get_window_start_time

            # Only consider overdue if we're currently in a monitoring window
            if not should_monitor_host(self.schedule_type, self.schedule_config, current_time):
                # Outside monitoring window - never overdue
                return False

            # We're in a monitoring window - check if last heartbeat was before this window
            window_start = get_window_start_time(self.schedule_type, self.schedule_config, current_time)

            if window_start and self.last_seen < window_start:
                # Last heartbeat was before this window started
                # Check if we're past: window_start + frequency + grace
                elapsed_since_window_start = (current_time - window_start).total_seconds()
                return elapsed_since_window_start > threshold
            else:
                # Last heartbeat was within this window (or window_start unknown)
                # Use normal frequency check
                elapsed = (current_time - self.last_seen).total_seconds()
                return elapsed > threshold

        # Default to simple check for unknown schedule types
        elapsed = (current_time - self.last_seen).total_seconds()
        return elapsed > threshold


class Heartbeat(Base):
    """Heartbeat log entries."""

    __tablename__ = "heartbeats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    extra_data = Column(Text, nullable=True)  # JSON for additional data (renamed from metadata to avoid SQLAlchemy reserved name)

    # Relationships
    host = relationship("Host", back_populates="heartbeats")

    def __repr__(self):
        return f"<Heartbeat(id={self.id}, host_id={self.host_id}, timestamp={self.timestamp})>"


class Alert(Base):
    """Alert records."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=True, index=True)
    alert_type = Column(
        String(50), nullable=False, index=True
    )  # 'heartbeat', 'log_analysis', 'internet', 'system'
    severity = Column(
        String(20), nullable=False, default="warning"
    )  # 'info', 'warning', 'critical'
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)  # JSON
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    host = relationship("Host", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.alert_type}, severity={self.severity})>"


class LogAnalysis(Base):
    """Log analysis results."""

    __tablename__ = "log_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    host_id = Column(Integer, ForeignKey("hosts.id"), nullable=False, index=True)
    log_source = Column(String(500), nullable=False)
    lines_analyzed = Column(Integer, nullable=True)
    llm_model = Column(String(100), nullable=True)
    findings = Column(Text, nullable=True)  # JSON array of findings
    severity = Column(String(20), nullable=True)  # Highest severity found
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    host = relationship("Host", back_populates="log_analyses")

    def __repr__(self):
        return f"<LogAnalysis(id={self.id}, host_id={self.host_id}, severity={self.severity})>"


class Config(Base):
    """System configuration key-value store."""

    __tablename__ = "config"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Config(key={self.key})>"
