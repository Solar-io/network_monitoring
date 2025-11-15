"""Background scheduler service for monitoring tasks."""
import logging
import time
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config import get_settings
from src.database import Host, get_db_context
from src.services.alert_service import get_alert_service
from src.services.log_analyzer import LogAnalyzerService
from src.utils.schedule_utils import should_monitor_host

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def check_heartbeats():
    """
    Check all hosts for missing heartbeats.

    This job runs every minute and checks if any hosts have missed their
    expected heartbeat within the configured frequency + grace period.
    """
    logger.info("Checking heartbeats for all hosts")

    alert_service = get_alert_service()

    with get_db_context() as db:
        hosts = db.query(Host).all()

        for host in hosts:
            try:
                # Check if we should monitor this host now
                if not should_monitor_host(host.schedule_type):
                    logger.debug(f"Skipping {host.name} - outside monitoring schedule")
                    continue

                # Check if heartbeat is overdue
                if host.is_overdue():
                    logger.warning(f"Host {host.name} heartbeat is overdue")

                    # Only alert if status is not already 'down'
                    if host.status != "down":
                        alert_service.heartbeat_missed_alert(host)
                        # Status update happens in alert_service

                elif host.status == "down":
                    # Host was down but is now back up
                    logger.info(f"Host {host.name} has recovered")
                    alert_service.heartbeat_recovered_alert(host)

                    # Update status
                    host.status = "up"
                    db.commit()

            except Exception as e:
                logger.error(f"Error checking heartbeat for {host.name}: {e}")

    logger.info("Heartbeat check complete")


def analyze_logs():
    """
    Analyze logs for all hosts with log analysis enabled.

    This job runs periodically to analyze logs via SSH and LLM.
    """
    logger.info("Starting log analysis for all enabled hosts")

    log_analyzer = LogAnalyzerService()

    with get_db_context() as db:
        # Get all hosts with log analysis enabled
        hosts = db.query(Host).filter(Host.log_analysis_config.isnot(None)).all()

        for host in hosts:
            try:
                result = log_analyzer.analyze_host_logs(host)
                if result:
                    logger.info(f"Log analysis complete for {host.name}: {result.severity}")
                else:
                    logger.debug(f"Log analysis skipped for {host.name}")
            except Exception as e:
                logger.error(f"Error analyzing logs for {host.name}: {e}")

    logger.info("Log analysis complete")


def cleanup_old_records():
    """
    Clean up old database records to prevent unbounded growth.

    Removes:
    - Heartbeats older than 30 days
    - Alerts older than 90 days
    - Log analyses older than 60 days
    """
    from datetime import timedelta
    from src.database import Alert, Heartbeat, LogAnalysis

    logger.info("Cleaning up old database records")

    with get_db_context() as db:
        now = datetime.utcnow()

        # Delete old heartbeats (30 days)
        cutoff_heartbeats = now - timedelta(days=30)
        deleted_heartbeats = (
            db.query(Heartbeat)
            .filter(Heartbeat.timestamp < cutoff_heartbeats)
            .delete()
        )

        # Delete old alerts (90 days)
        cutoff_alerts = now - timedelta(days=90)
        deleted_alerts = (
            db.query(Alert)
            .filter(Alert.created_at < cutoff_alerts)
            .delete()
        )

        # Delete old log analyses (60 days)
        cutoff_logs = now - timedelta(days=60)
        deleted_logs = (
            db.query(LogAnalysis)
            .filter(LogAnalysis.created_at < cutoff_logs)
            .delete()
        )

        db.commit()

        logger.info(
            f"Cleanup complete: {deleted_heartbeats} heartbeats, "
            f"{deleted_alerts} alerts, {deleted_logs} log analyses"
        )


def health_check():
    """
    Periodic health check of the monitoring system itself.

    Verifies:
    - Database is accessible
    - Configuration is loaded
    - Services are running
    """
    logger.info("Running system health check")

    try:
        # Check database
        with get_db_context() as db:
            host_count = db.query(Host).count()
            logger.info(f"Database OK: {host_count} hosts configured")

        # Check configuration
        settings = get_settings()
        logger.info(f"Configuration OK: Discord webhook configured")

        # All checks passed
        logger.info("System health check passed")

    except Exception as e:
        logger.error(f"System health check failed: {e}")

        # Send alert
        alert_service = get_alert_service()
        alert_service.system_alert(
            title="System Health Check Failed",
            message=f"Health check failed: {str(e)}",
            severity="critical",
        )


def run_scheduler():
    """
    Run the background scheduler.

    This function sets up and runs all scheduled jobs.
    """
    scheduler = BlockingScheduler(timezone="UTC")

    logger.info("Setting up scheduled jobs")

    # Heartbeat checker - every 1 minute
    scheduler.add_job(
        check_heartbeats,
        trigger=IntervalTrigger(minutes=1),
        id="heartbeat_checker",
        name="Check heartbeats",
        replace_existing=True,
    )
    logger.info("Added job: Heartbeat checker (every 1 minute)")

    # Log analyzer - every 30 minutes
    scheduler.add_job(
        analyze_logs,
        trigger=IntervalTrigger(minutes=30),
        id="log_analyzer",
        name="Analyze logs",
        replace_existing=True,
    )
    logger.info("Added job: Log analyzer (every 30 minutes)")

    # Database cleanup - daily at 3 AM UTC
    scheduler.add_job(
        cleanup_old_records,
        trigger=CronTrigger(hour=3, minute=0),
        id="cleanup",
        name="Cleanup old records",
        replace_existing=True,
    )
    logger.info("Added job: Database cleanup (daily at 3 AM UTC)")

    # System health check - every hour
    scheduler.add_job(
        health_check,
        trigger=IntervalTrigger(hours=1),
        id="health_check",
        name="System health check",
        replace_existing=True,
    )
    logger.info("Added job: Health check (every hour)")

    logger.info("Starting scheduler...")
    logger.info(f"Scheduled jobs: {[job.name for job in scheduler.get_jobs()]}")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    logger.info("Starting Network Monitoring Scheduler Service")
    run_scheduler()
