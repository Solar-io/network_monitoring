"""Project service health check polling."""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Optional

import requests
from requests import Response
from sqlalchemy.orm import Session

from src.database import ProjectService, ServiceHealthCheck, get_db_context
from src.services.alert_service import get_alert_service

logger = logging.getLogger(__name__)


class ProjectPollerService:
    """Polls configured project services and records their health."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "NetworkMonitoringProjectPoller/1.0",
            "Accept": "application/json, */*",
        })
        self.alert_service = get_alert_service()

    def poll_all_services(self) -> None:
        """Poll all enabled project services."""
        logger.info("Polling all project services")

        with get_db_context() as db:
            services = (
                db.query(ProjectService)
                .filter(ProjectService.enabled.is_(True))
                .all()
            )

            for service in services:
                try:
                    check = self.poll_service(service, db)
                    db.add(check)
                    db.commit()
                except Exception as exc:  # pylint: disable=broad-except
                    logger.exception(
                        "Failed to poll service %s/%s: %s",
                        service.project_name,
                        service.service_name,
                        exc,
                    )
                    db.rollback()

        logger.info("Project service polling complete")

    def poll_service(self, service: ProjectService, db: Session) -> ServiceHealthCheck:
        """Poll a single service and return the recorded health check."""
        logger.info(
            "Polling %s/%s", service.project_name, service.service_name
        )

        check = ServiceHealthCheck(
            service_id=service.id,
            timestamp=datetime.utcnow(),
        )

        start = time.monotonic()
        try:
            response = self._perform_request(service)
            elapsed_ms = int((time.monotonic() - start) * 1000)
            check.response_time_ms = elapsed_ms
            check.status_code = response.status_code
            check.response_body = response.text[:1000]

            if response.status_code != service.expected_status_code:
                check.status = "failure"
                check.error_message = (
                    f"Unexpected status: {response.status_code}"
                )
                self._mark_failure(service, check, db)
            elif (
                service.expected_response_pattern
                and not re.search(
                    service.expected_response_pattern,
                    response.text,
                    re.IGNORECASE,
                )
            ):
                check.status = "failure"
                check.error_message = "Response pattern mismatch"
                self._mark_failure(service, check, db)
            else:
                check.status = "success"
                self._mark_success(service, db)
        except requests.Timeout:
            check.status = "timeout"
            check.error_message = (
                f"Timed out after {service.timeout_seconds}s"
            )
            self._mark_failure(service, check, db)
        except requests.RequestException as exc:  # network errors
            check.status = "failure"
            check.error_message = str(exc)
            self._mark_failure(service, check, db)
        finally:
            service.last_checked = datetime.utcnow()

        return check

    def _perform_request(self, service: ProjectService) -> Response:
        """Execute an HTTP request based on service configuration."""
        headers = {}
        auth = None

        if service.auth_type and service.auth_config:
            try:
                cfg = json.loads(service.auth_config)
            except json.JSONDecodeError:
                cfg = {}

            if service.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {cfg.get('token', '')}"
            elif service.auth_type == "api_key":
                header_name = cfg.get("header", "X-API-Key")
                headers[header_name] = cfg.get("token", "")
            elif service.auth_type == "basic":
                auth = (cfg.get("username"), cfg.get("password"))

        method = "get"
        if service.endpoint_type.lower() == "post":
            method = "post"

        request = getattr(self.session, method)
        response = request(
            service.endpoint_url,
            headers=headers,
            timeout=service.timeout_seconds,
            auth=auth,
        )
        return response

    def _mark_success(self, service: ProjectService, db: Session) -> None:
        """Handle successful check state updates and recovery alerts."""
        send_recovery = service.status == "unhealthy"
        service.status = "healthy"
        service.consecutive_failures = 0
        service.last_error = None
        db.add(service)
        db.flush()

        if send_recovery:
            logger.info(
                "Service %s/%s recovered",
                service.project_name,
                service.service_name,
            )
            self.alert_service.project_service_recovered_alert(service)

    def _mark_failure(
        self, service: ProjectService, check: ServiceHealthCheck, db: Session
    ) -> None:
        """Handle a failed health check and alerting logic."""
        service.consecutive_failures += 1
        service.status = (
            "unhealthy"
            if service.consecutive_failures >= service.alert_threshold
            else "degraded"
        )
        service.last_error = check.error_message
        db.add(service)
        db.flush()

        if service.status == "unhealthy":
            logger.warning(
                "Service %s/%s unhealthy: %s",
                service.project_name,
                service.service_name,
                check.error_message,
            )
            self.alert_service.project_service_failure_alert(service, check)


def get_project_poller() -> ProjectPollerService:
    """Return singleton poller instance."""
    return ProjectPollerService()
