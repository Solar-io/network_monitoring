"""Alert service for managing and sending alerts."""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.database import Alert, Host, get_db_context
from src.database.schemas import AlertCreate
from src.utils import get_discord_client

logger = logging.getLogger(__name__)


class AlertService:
    """Service for creating and managing alerts."""

    # Deduplication window in seconds
    DEDUP_WINDOW = 300  # 5 minutes

    def __init__(self):
        """Initialize alert service."""
        self.discord = get_discord_client()

    def create_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        host_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        send_discord: bool = True,
    ) -> Optional[Alert]:
        """
        Create an alert and optionally send to Discord.

        Args:
            alert_type: Type of alert ('heartbeat', 'log_analysis', 'internet', 'system')
            message: Alert message
            severity: Severity level ('info', 'warning', 'critical')
            host_id: Associated host ID (if applicable)
            details: Additional alert details
            send_discord: Whether to send Discord notification

        Returns:
            Created Alert object or None if deduplicated
        """
        # Check for duplicate recent alerts
        if self._is_duplicate_alert(host_id, alert_type, message):
            logger.info(f"Skipping duplicate alert: {alert_type} for host {host_id}")
            return None

        # Create alert in database
        with get_db_context() as db:
            alert = Alert(
                host_id=host_id,
                alert_type=alert_type,
                severity=severity,
                message=message,
                details=json.dumps(details) if details else None,
            )
            db.add(alert)
            db.flush()

            # Send Discord notification
            if send_discord:
                self._send_discord_for_alert(alert, db)

            return alert

    def heartbeat_missed_alert(self, host: Host) -> Optional[Alert]:
        """
        Create alert for missed heartbeat.

        Args:
            host: Host that missed heartbeat

        Returns:
            Created Alert or None
        """
        logger.warning(f"Heartbeat missed for host: {host.name}")

        # Create alert in database
        alert = self.create_alert(
            alert_type="heartbeat",
            message=f"Host '{host.name}' missed heartbeat",
            severity="critical",
            host_id=host.id,
            details={
                "host_name": host.name,
                "host_id": host.host_id,
                "last_seen": host.last_seen.isoformat() if host.last_seen else None,
                "expected_frequency": host.expected_frequency_seconds,
                "grace_period": host.grace_period_seconds,
            },
            send_discord=True,
        )

        # Update host status
        with get_db_context() as db:
            db_host = db.query(Host).filter(Host.id == host.id).first()
            if db_host:
                db_host.status = "down"

        return alert

    def heartbeat_recovered_alert(self, host: Host) -> Optional[Alert]:
        """
        Create alert for heartbeat recovery.

        Args:
            host: Host that recovered

        Returns:
            Created Alert or None
        """
        logger.info(f"Heartbeat recovered for host: {host.name}")

        return self.create_alert(
            alert_type="heartbeat",
            message=f"Host '{host.name}' recovered",
            severity="info",
            host_id=host.id,
            details={
                "host_name": host.name,
                "host_id": host.host_id,
            },
            send_discord=True,
        )

    def log_analysis_alert(
        self,
        host: Host,
        findings: List[Dict[str, Any]],
        severity: str,
    ) -> Optional[Alert]:
        """
        Create alert for log analysis findings.

        Args:
            host: Host where logs were analyzed
            findings: List of findings from LLM
            severity: Highest severity level found

        Returns:
            Created Alert or None
        """
        findings_count = len(findings)
        findings_summary = self._summarize_findings(findings)

        logger.info(f"Log analysis alert for {host.name}: {findings_count} findings")

        return self.create_alert(
            alert_type="log_analysis",
            message=f"Log analysis found {findings_count} issue(s) on '{host.name}'",
            severity=severity,
            host_id=host.id,
            details={
                "host_name": host.name,
                "findings_count": findings_count,
                "findings_summary": findings_summary,
                "findings": findings,
            },
            send_discord=True,
        )

    def internet_down_alert(self) -> Optional[Alert]:
        """
        Create alert for internet connectivity loss.

        Returns:
            Created Alert or None
        """
        logger.error("Internet connectivity lost")

        return self.create_alert(
            alert_type="internet",
            message="Internet connectivity lost",
            severity="critical",
            host_id=None,
            send_discord=True,
        )

    def internet_up_alert(self, downtime_seconds: Optional[int] = None) -> Optional[Alert]:
        """
        Create alert for internet connectivity restoration.

        Args:
            downtime_seconds: Duration of downtime in seconds

        Returns:
            Created Alert or None
        """
        logger.info("Internet connectivity restored")

        details = {}
        if downtime_seconds:
            details["downtime_seconds"] = downtime_seconds

        return self.create_alert(
            alert_type="internet",
            message="Internet connectivity restored",
            severity="info",
            host_id=None,
            details=details if details else None,
            send_discord=True,
        )

    def system_alert(self, title: str, message: str, severity: str = "warning") -> Optional[Alert]:
        """
        Create a general system alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Severity level

        Returns:
            Created Alert or None
        """
        return self.create_alert(
            alert_type="system",
            message=f"{title}: {message}",
            severity=severity,
            host_id=None,
            send_discord=True,
        )

    def _is_duplicate_alert(
        self,
        host_id: Optional[int],
        alert_type: str,
        message: str,
    ) -> bool:
        """
        Check if similar alert was recently created.

        Args:
            host_id: Host ID (or None)
            alert_type: Alert type
            message: Alert message

        Returns:
            True if duplicate found, False otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.DEDUP_WINDOW)

        with get_db_context() as db:
            recent_alert = (
                db.query(Alert)
                .filter(Alert.created_at >= cutoff_time)
                .filter(Alert.host_id == host_id)
                .filter(Alert.alert_type == alert_type)
                .filter(Alert.message == message)
                .filter(Alert.acknowledged == False)
                .first()
            )

            return recent_alert is not None

    def _send_discord_for_alert(self, alert: Alert, db: Session):
        """
        Send Discord notification for alert.

        Args:
            alert: Alert object
            db: Database session
        """
        try:
            # Get host details if applicable
            host = None
            if alert.host_id:
                host = db.query(Host).filter(Host.id == alert.host_id).first()

            # Send appropriate Discord message based on alert type
            if alert.alert_type == "heartbeat":
                if host:
                    if "missed" in alert.message.lower():
                        self.discord.send_heartbeat_alert(
                            host_name=host.name,
                            host_id=host.host_id,
                            last_seen=host.last_seen,
                            expected_frequency=host.expected_frequency_seconds,
                            grace_period=host.grace_period_seconds,
                        )
                    elif "recovered" in alert.message.lower():
                        self.discord.send_heartbeat_recovery(
                            host_name=host.name,
                            host_id=host.host_id,
                        )

            elif alert.alert_type == "log_analysis":
                if host and alert.details:
                    details = json.loads(alert.details)
                    self.discord.send_log_analysis_alert(
                        host_name=host.name,
                        host_id=host.host_id,
                        severity=alert.severity,
                        findings_summary=details.get("findings_summary", ""),
                        findings_count=details.get("findings_count", 0),
                    )

            elif alert.alert_type == "internet":
                if "lost" in alert.message.lower() or "down" in alert.message.lower():
                    self.discord.send_internet_down_alert()
                elif "restored" in alert.message.lower() or "up" in alert.message.lower():
                    downtime = None
                    if alert.details:
                        details = json.loads(alert.details)
                        downtime = details.get("downtime_seconds")
                    self.discord.send_internet_up_alert(downtime_duration=downtime)

            elif alert.alert_type == "system":
                self.discord.send_system_alert(
                    title="System Alert",
                    message=alert.message,
                    severity=alert.severity,
                )

        except Exception as e:
            logger.error(f"Failed to send Discord notification: {e}")

    @staticmethod
    def _summarize_findings(findings: List[Dict[str, Any]]) -> str:
        """
        Create a summary of findings for Discord.

        Args:
            findings: List of finding dictionaries

        Returns:
            Summary string
        """
        if not findings:
            return "No issues found"

        # Group by severity
        critical = [f for f in findings if f.get("severity") == "critical"]
        warning = [f for f in findings if f.get("severity") == "warning"]
        info = [f for f in findings if f.get("severity") == "info"]

        parts = []
        if critical:
            parts.append(f"🔴 {len(critical)} critical")
        if warning:
            parts.append(f"🟡 {len(warning)} warning")
        if info:
            parts.append(f"🔵 {len(info)} info")

        return ", ".join(parts)


def get_alert_service() -> AlertService:
    """
    Get AlertService instance.

    Returns:
        AlertService instance
    """
    return AlertService()
