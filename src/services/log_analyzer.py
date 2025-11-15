"""Log analysis service using SSH and LLM."""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.database import Host, LogAnalysis, get_db_context
from src.services.alert_service import get_alert_service
from src.utils import SSHClient, get_llm_client

logger = logging.getLogger(__name__)


class LogAnalyzerService:
    """Service for analyzing logs from remote hosts."""

    def __init__(self):
        """Initialize log analyzer service."""
        self.llm_client = get_llm_client()
        self.alert_service = get_alert_service()

    def analyze_host_logs(self, host: Host) -> Optional[LogAnalysis]:
        """
        Analyze logs for a host.

        Args:
            host: Host to analyze logs for

        Returns:
            LogAnalysis object or None if failed
        """
        # Load log analysis config from host
        if not host.log_analysis_config:
            logger.warning(f"No log analysis config for host: {host.name}")
            return None

        try:
            config = json.loads(host.log_analysis_config)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid log analysis config for {host.name}: {e}")
            return None

        if not config.get("enabled", False):
            logger.debug(f"Log analysis disabled for host: {host.name}")
            return None

        method = config.get("method", "ssh")

        if method == "ssh":
            return self._analyze_via_ssh(host, config)
        elif method == "syslog":
            return self._analyze_via_syslog(host, config)
        else:
            logger.error(f"Unknown log analysis method: {method}")
            return None

    def _analyze_via_ssh(self, host: Host, config: Dict[str, Any]) -> Optional[LogAnalysis]:
        """
        Analyze logs via SSH.

        Args:
            host: Host to analyze
            config: Log analysis configuration

        Returns:
            LogAnalysis object or None
        """
        ssh_host = config.get("ssh_host")
        ssh_user = config.get("ssh_user")
        ssh_key_path = config.get("ssh_key_path")
        ssh_password = config.get("ssh_password")
        log_command = config.get("log_command")
        analysis_prompt = config.get("analysis_prompt")

        if not all([ssh_host, ssh_user, log_command, analysis_prompt]):
            logger.error(f"Incomplete SSH config for {host.name}")
            return None

        logger.info(f"Analyzing logs for {host.name} via SSH to {ssh_host}")

        # Retrieve logs via SSH
        try:
            with SSHClient(
                hostname=ssh_host,
                username=ssh_user,
                key_path=ssh_key_path,
                password=ssh_password,
            ) as ssh:
                if not ssh.connect():
                    logger.error(f"Failed to connect to {ssh_host}")
                    return None

                logs = ssh.get_logs(log_command)
                if not logs:
                    logger.error(f"Failed to retrieve logs from {ssh_host}")
                    return None

                logger.info(f"Retrieved {len(logs)} bytes of logs from {ssh_host}")

        except Exception as e:
            logger.error(f"SSH error for {host.name}: {e}")
            return None

        # Analyze logs with LLM
        return self._analyze_logs_with_llm(
            host=host,
            logs=logs,
            log_source=f"ssh://{ssh_host}:{log_command}",
            analysis_prompt=analysis_prompt,
        )

    def _analyze_via_syslog(self, host: Host, config: Dict[str, Any]) -> Optional[LogAnalysis]:
        """
        Analyze logs via syslog (placeholder for future implementation).

        Args:
            host: Host to analyze
            config: Log analysis configuration

        Returns:
            LogAnalysis object or None
        """
        logger.warning(f"Syslog analysis not yet implemented for {host.name}")
        return None

    def _analyze_logs_with_llm(
        self,
        host: Host,
        logs: str,
        log_source: str,
        analysis_prompt: str,
    ) -> Optional[LogAnalysis]:
        """
        Analyze logs using LLM.

        Args:
            host: Host being analyzed
            logs: Log content
            log_source: Source description
            analysis_prompt: Analysis prompt for LLM

        Returns:
            LogAnalysis object or None
        """
        # Count lines
        lines_analyzed = len(logs.split("\n"))

        logger.info(f"Analyzing {lines_analyzed} lines for {host.name} with LLM")

        # Call LLM
        result = self.llm_client.analyze_logs(
            logs=logs,
            prompt=analysis_prompt,
        )

        if not result.get("success"):
            logger.error(f"LLM analysis failed: {result.get('error')}")
            return None

        findings = result.get("findings", [])
        model = result.get("model")

        # Determine highest severity
        severity = self._determine_severity(findings)

        logger.info(f"LLM analysis complete: {len(findings)} findings, severity: {severity}")

        # Store in database
        with get_db_context() as db:
            log_analysis = LogAnalysis(
                host_id=host.id,
                log_source=log_source,
                lines_analyzed=lines_analyzed,
                llm_model=model,
                findings=json.dumps(findings),
                severity=severity,
            )
            db.add(log_analysis)
            db.flush()

            # Create alert if there are critical or warning findings
            if severity in ["critical", "warning"] and findings:
                self.alert_service.log_analysis_alert(
                    host=host,
                    findings=findings,
                    severity=severity,
                )

            return log_analysis

    @staticmethod
    def _determine_severity(findings: Optional[List[Dict[str, Any]]]) -> str:
        """
        Determine highest severity from findings.

        Args:
            findings: List of findings

        Returns:
            Highest severity level ('critical', 'warning', 'info', 'none')
        """
        if not findings:
            return "none"

        severities = [f.get("severity", "info") for f in findings]

        if "critical" in severities:
            return "critical"
        elif "warning" in severities:
            return "warning"
        elif "info" in severities:
            return "info"
        else:
            return "none"


def analyze_all_hosts():
    """Analyze logs for all hosts with log analysis enabled."""
    logger.info("Starting log analysis for all enabled hosts")

    analyzer = LogAnalyzerService()

    with get_db_context() as db:
        # Get all hosts with log analysis enabled
        hosts = db.query(Host).filter(Host.log_analysis_config.isnot(None)).all()

        for host in hosts:
            try:
                result = analyzer.analyze_host_logs(host)
                if result:
                    logger.info(f"Log analysis complete for {host.name}: {result.severity}")
                else:
                    logger.warning(f"Log analysis skipped or failed for {host.name}")
            except Exception as e:
                logger.error(f"Error analyzing logs for {host.name}: {e}")

    logger.info("Log analysis batch complete")


def get_log_analyzer() -> LogAnalyzerService:
    """
    Get LogAnalyzerService instance.

    Returns:
        LogAnalyzerService instance
    """
    return LogAnalyzerService()
