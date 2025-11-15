"""Internet connectivity monitor service."""
import logging
import socket
from datetime import datetime
from typing import Optional

import requests

from src.config import get_settings
from src.services.alert_service import get_alert_service

logger = logging.getLogger(__name__)


class InternetMonitor:
    """Monitor internet connectivity and ping healthchecks.io."""

    def __init__(self):
        """Initialize internet monitor."""
        self.settings = get_settings()
        self.alert_service = get_alert_service()
        self.last_status = None  # True = up, False = down, None = unknown
        self.last_down_time: Optional[datetime] = None

    def check_connectivity(self) -> bool:
        """
        Check internet connectivity.

        Performs multiple checks:
        1. DNS resolution (8.8.8.8, 1.1.1.1)
        2. HTTP requests to known endpoints
        3. Socket connection test

        Returns:
            True if internet is available, False otherwise
        """
        checks = [
            self._check_dns,
            self._check_http,
            self._check_socket,
        ]

        results = []
        for check in checks:
            try:
                result = check()
                results.append(result)
                if result:
                    # If any check passes, consider internet up
                    logger.debug(f"Connectivity check passed: {check.__name__}")
                    return True
            except Exception as e:
                logger.error(f"Connectivity check {check.__name__} failed: {e}")
                results.append(False)

        # All checks failed
        logger.error("All connectivity checks failed")
        return False

    def _check_dns(self) -> bool:
        """
        Check DNS resolution.

        Returns:
            True if DNS works, False otherwise
        """
        try:
            # Try to resolve a known domain
            socket.gethostbyname("google.com")
            return True
        except socket.gaierror:
            return False

    def _check_http(self) -> bool:
        """
        Check HTTP connectivity.

        Returns:
            True if HTTP request succeeds, False otherwise
        """
        test_urls = [
            "https://www.google.com",
            "https://www.cloudflare.com",
            "https://1.1.1.1",
        ]

        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                continue

        return False

    def _check_socket(self) -> bool:
        """
        Check socket connectivity to known IP.

        Returns:
            True if socket connection succeeds, False otherwise
        """
        try:
            # Try to connect to Google's DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(("8.8.8.8", 53))
            sock.close()
            return True
        except (socket.error, socket.timeout):
            return False

    def ping_healthchecks(self) -> bool:
        """
        Ping healthchecks.io to signal system is alive.

        Returns:
            True if ping successful, False otherwise
        """
        if not self.settings.healthchecks_url:
            logger.debug("Healthchecks.io URL not configured")
            return False

        try:
            response = requests.get(self.settings.healthchecks_url, timeout=10)
            response.raise_for_status()
            logger.info("Healthchecks.io ping successful")
            return True
        except requests.RequestException as e:
            logger.error(f"Failed to ping healthchecks.io: {e}")
            return False

    def run_check(self):
        """
        Run connectivity check and ping healthchecks.io.

        Updates status and sends alerts if connectivity changes.
        """
        logger.debug("Running internet connectivity check")

        is_connected = self.check_connectivity()

        # Handle state transitions
        if is_connected:
            if self.last_status is False:
                # Internet came back up
                downtime = None
                if self.last_down_time:
                    downtime = int((datetime.utcnow() - self.last_down_time).total_seconds())

                logger.info(f"Internet connectivity restored (downtime: {downtime}s)")
                self.alert_service.internet_up_alert(downtime_seconds=downtime)
                self.last_down_time = None

            # Ping healthchecks.io
            self.ping_healthchecks()

        else:
            if self.last_status is True or self.last_status is None:
                # Internet just went down
                logger.error("Internet connectivity lost")
                self.alert_service.internet_down_alert()
                self.last_down_time = datetime.utcnow()

        self.last_status = is_connected

    def get_status(self) -> dict:
        """
        Get current internet monitor status.

        Returns:
            Dictionary with status information
        """
        return {
            "connected": self.last_status,
            "last_check": datetime.utcnow().isoformat(),
            "healthchecks_enabled": bool(self.settings.healthchecks_url),
        }


def run_internet_monitor_loop():
    """Run internet monitor in a loop (for standalone service)."""
    import time

    monitor = InternetMonitor()
    check_interval = 300  # 5 minutes

    logger.info(f"Starting internet monitor service (interval: {check_interval}s)")

    while True:
        try:
            monitor.run_check()
        except Exception as e:
            logger.error(f"Error in internet monitor: {e}")

        time.sleep(check_interval)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_internet_monitor_loop()
