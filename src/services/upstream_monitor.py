"""Upstream monitoring service - sends heartbeats to external monitoring service."""
import logging
from typing import Optional

import requests

from src.database import Config, get_db_context

logger = logging.getLogger(__name__)


class UpstreamMonitorService:
    """Service for sending heartbeats to upstream monitoring service."""

    def __init__(self):
        """Initialize upstream monitor service."""
        self.last_status = None

    def get_config(self) -> tuple[bool, Optional[str], int]:
        """
        Get upstream monitoring configuration from database.

        Returns:
            Tuple of (enabled, url, frequency_seconds)
        """
        try:
            with get_db_context() as db:
                db_enabled = (
                    db.query(Config)
                    .filter(Config.key == "upstream_monitoring_enabled")
                    .first()
                )
                db_url = (
                    db.query(Config)
                    .filter(Config.key == "upstream_monitoring_url")
                    .first()
                )
                db_freq = (
                    db.query(Config)
                    .filter(Config.key == "upstream_monitoring_frequency")
                    .first()
                )

                enabled = db_enabled.value == "true" if db_enabled else False
                url = db_url.value if db_url else None
                frequency = int(db_freq.value) if db_freq else 300

                return enabled, url, frequency
        except Exception as e:
            logger.error(f"Error getting upstream monitoring config: {e}")
            return False, None, 300

    def send_heartbeat(self) -> bool:
        """
        Send heartbeat to upstream monitoring service.

        Returns:
            True if successful, False otherwise
        """
        enabled, url, _ = self.get_config()

        if not enabled:
            logger.debug("Upstream monitoring is disabled")
            return False

        if not url:
            logger.warning("Upstream monitoring enabled but no URL configured")
            return False

        try:
            logger.info(f"Sending heartbeat to upstream monitor: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            logger.info(
                f"Upstream heartbeat sent successfully: HTTP {response.status_code}"
            )
            self.last_status = "success"
            return True

        except requests.exceptions.Timeout:
            logger.error(f"Timeout sending heartbeat to {url}")
            self.last_status = "timeout"
            return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send heartbeat to {url}: {e}")
            self.last_status = "error"
            return False

    def send_heartbeat_with_status(self, status: str = "success") -> bool:
        """
        Send heartbeat with specific status indicator.

        Some upstream services (like healthchecks.io) support status paths:
        - /your-uuid - success
        - /your-uuid/fail - failure
        - /your-uuid/start - job started
        - /your-uuid/log - with log data

        Args:
            status: Status to send ('success', 'fail', 'start')

        Returns:
            True if successful, False otherwise
        """
        enabled, url, _ = self.get_config()

        if not enabled or not url:
            return False

        # Append status to URL if not 'success'
        if status != "success" and not url.endswith(f"/{status}"):
            heartbeat_url = f"{url}/{status}"
        else:
            heartbeat_url = url

        try:
            logger.info(f"Sending {status} heartbeat to upstream monitor")
            response = requests.get(heartbeat_url, timeout=10)
            response.raise_for_status()
            logger.info(f"Upstream heartbeat ({status}) sent successfully")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send {status} heartbeat: {e}")
            return False


# Global instance
_upstream_monitor = None


def get_upstream_monitor() -> UpstreamMonitorService:
    """
    Get UpstreamMonitorService instance.

    Returns:
        UpstreamMonitorService instance
    """
    global _upstream_monitor
    if _upstream_monitor is None:
        _upstream_monitor = UpstreamMonitorService()
    return _upstream_monitor
