"""Discord webhook client."""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class DiscordWebhook:
    """Discord webhook client for sending alerts."""

    # Color codes for different severity levels
    COLORS = {
        "info": 3447003,  # Blue
        "warning": 16776960,  # Yellow
        "critical": 15158332,  # Red
        "success": 3066993,  # Green
    }

    def __init__(self, webhook_url: str):
        """
        Initialize Discord webhook client.

        Args:
            webhook_url: Discord webhook URL
        """
        self.webhook_url = webhook_url

    def send_embed(
        self,
        title: str,
        description: str,
        color: str = "info",
        fields: Optional[List[Dict[str, Any]]] = None,
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """
        Send an embed message to Discord.

        Args:
            title: Embed title
            description: Embed description
            color: Color name ('info', 'warning', 'critical', 'success')
            fields: List of field dictionaries with 'name' and 'value'
            timestamp: Timestamp for the embed

        Returns:
            True if successful, False otherwise
        """
        embed = {
            "title": title,
            "description": description,
            "color": self.COLORS.get(color, self.COLORS["info"]),
        }

        if fields:
            embed["fields"] = fields

        if timestamp:
            embed["timestamp"] = timestamp.isoformat()
        else:
            embed["timestamp"] = datetime.utcnow().isoformat()

        payload = {"embeds": [embed]}

        return self._send(payload)

    def send_heartbeat_alert(
        self,
        host_name: str,
        host_id: str,
        last_seen: Optional[datetime],
        expected_frequency: int,
        grace_period: int,
    ) -> bool:
        """
        Send a heartbeat missed alert.

        Args:
            host_name: Name of the host
            host_id: Host identifier
            last_seen: Last heartbeat timestamp
            expected_frequency: Expected heartbeat frequency in seconds
            grace_period: Grace period in seconds

        Returns:
            True if successful, False otherwise
        """
        last_seen_str = last_seen.strftime("%Y-%m-%d %H:%M:%S UTC") if last_seen else "Never"
        expected_str = self._format_duration(expected_frequency)
        grace_str = self._format_duration(grace_period)

        return self.send_embed(
            title=f"🚨 Alert: Host Heartbeat Missed",
            description=f"Host **{host_name}** (`{host_id}`) has missed its heartbeat check.",
            color="critical",
            fields=[
                {"name": "Host", "value": host_name, "inline": True},
                {"name": "Host ID", "value": host_id, "inline": True},
                {"name": "Last Seen", "value": last_seen_str, "inline": False},
                {"name": "Expected Every", "value": expected_str, "inline": True},
                {"name": "Grace Period", "value": grace_str, "inline": True},
            ],
        )

    def send_heartbeat_recovery(self, host_name: str, host_id: str) -> bool:
        """
        Send a heartbeat recovery notification.

        Args:
            host_name: Name of the host
            host_id: Host identifier

        Returns:
            True if successful, False otherwise
        """
        return self.send_embed(
            title=f"✅ Host Recovered",
            description=f"Host **{host_name}** (`{host_id}`) is back online.",
            color="success",
            fields=[
                {"name": "Host", "value": host_name, "inline": True},
                {"name": "Host ID", "value": host_id, "inline": True},
            ],
        )

    def send_log_analysis_alert(
        self,
        host_name: str,
        host_id: str,
        severity: str,
        findings_summary: str,
        findings_count: int,
    ) -> bool:
        """
        Send a log analysis finding alert.

        Args:
            host_name: Name of the host
            host_id: Host identifier
            severity: Severity level
            findings_summary: Summary of findings
            findings_count: Number of findings

        Returns:
            True if successful, False otherwise
        """
        severity_lower = severity.lower() if severity else "warning"
        color = "critical" if severity_lower == "critical" else "warning"

        return self.send_embed(
            title=f"🔍 Log Analysis Alert",
            description=f"Log analysis found **{findings_count}** issue(s) on host **{host_name}**.",
            color=color,
            fields=[
                {"name": "Host", "value": host_name, "inline": True},
                {"name": "Severity", "value": severity.upper(), "inline": True},
                {"name": "Findings", "value": findings_summary, "inline": False},
            ],
        )

    def send_internet_down_alert(self) -> bool:
        """
        Send internet connectivity down alert.

        Returns:
            True if successful, False otherwise
        """
        return self.send_embed(
            title=f"🌐 Internet Connectivity Lost",
            description="The monitoring system has lost internet connectivity.",
            color="critical",
            fields=[
                {"name": "Status", "value": "Offline", "inline": True},
                {"name": "Action", "value": "Investigating", "inline": True},
            ],
        )

    def send_internet_up_alert(self, downtime_duration: Optional[int] = None) -> bool:
        """
        Send internet connectivity restored alert.

        Args:
            downtime_duration: Duration of downtime in seconds

        Returns:
            True if successful, False otherwise
        """
        fields = [
            {"name": "Status", "value": "Online", "inline": True},
        ]

        if downtime_duration:
            fields.append({
                "name": "Downtime",
                "value": self._format_duration(downtime_duration),
                "inline": True,
            })

        return self.send_embed(
            title=f"✅ Internet Connectivity Restored",
            description="The monitoring system has regained internet connectivity.",
            color="success",
            fields=fields,
        )

    def send_system_alert(
        self, title: str, message: str, severity: str = "warning"
    ) -> bool:
        """
        Send a general system alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Severity level

        Returns:
            True if successful, False otherwise
        """
        return self.send_embed(
            title=f"⚙️ {title}",
            description=message,
            color=severity,
        )

    def _send(self, payload: Dict[str, Any]) -> bool:
        """
        Send payload to Discord webhook.

        Args:
            payload: JSON payload to send

        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()
            logger.debug(f"Discord webhook sent successfully: {response.status_code}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Discord webhook: {e}")
            return False

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """
        Format duration in seconds to human-readable string.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted string (e.g., "5 minutes", "2 hours")
        """
        if seconds < 60:
            return f"{seconds} second{'s' if seconds != 1 else ''}"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''}"


def get_discord_client() -> DiscordWebhook:
    """
    Get Discord webhook client from settings.

    Returns:
        DiscordWebhook instance
    """
    from src.config import get_settings

    settings = get_settings()
    return DiscordWebhook(settings.discord_webhook_url)
