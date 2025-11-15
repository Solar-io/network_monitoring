"""Host management API endpoints."""
import json
import logging
import secrets
from datetime import datetime
from typing import List

from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import Host, get_db
from src.database.schemas import HostCreate, HostResponse, HostStatus, HostUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


def calculate_frequency_from_cron(cron_expr: str) -> int:
    """
    Calculate average frequency in seconds from a cron expression.

    Args:
        cron_expr: Cron expression (e.g., "*/5 * * * *" for every 5 minutes)

    Returns:
        Estimated frequency in seconds between occurrences
    """
    try:
        base_time = datetime.utcnow()
        cron = croniter(cron_expr, base_time)

        # Get next 3 occurrences to calculate average interval
        times = [cron.get_next(datetime) for _ in range(3)]

        # Calculate intervals
        intervals = [(times[i+1] - times[i]).total_seconds() for i in range(len(times)-1)]

        # Return average interval
        return int(sum(intervals) / len(intervals))
    except Exception as e:
        logger.error(f"Failed to calculate frequency from cron expression '{cron_expr}': {e}")
        return 300  # Default to 5 minutes


@router.get("/hosts", response_model=List[HostStatus])
async def list_hosts(db: Session = Depends(get_db)):
    """
    List all monitored hosts with their current status.

    Args:
        db: Database session

    Returns:
        List of hosts with status information
    """
    hosts = db.query(Host).all()

    return [
        HostStatus(
            id=host.id,
            name=host.name,
            host_id=host.host_id,
            status=host.status,
            last_seen=host.last_seen,
            is_overdue=host.is_overdue(),
        )
        for host in hosts
    ]


@router.get("/hosts/{host_id}", response_model=HostResponse)
async def get_host(host_id: str, db: Session = Depends(get_db)):
    """
    Get details for a specific host.

    Args:
        host_id: Unique host identifier
        db: Database session

    Returns:
        Host details
    """
    host = db.query(Host).filter(Host.host_id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    # Build heartbeat URL
    from src.config import get_settings

    settings = get_settings()
    heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}?token={host.token}"

    return HostResponse(
        id=host.id,
        name=host.name,
        host_id=host.host_id,
        heartbeat_url=heartbeat_url,
        cron_expression=host.cron_expression,
        expected_frequency_seconds=host.expected_frequency_seconds,
        schedule_type=host.schedule_type,
        schedule_config=host.schedule_config,
        grace_period_seconds=host.grace_period_seconds,
        log_analysis_config=host.log_analysis_config,
        last_seen=host.last_seen,
        status=host.status,
        created_at=host.created_at,
        updated_at=host.updated_at,
    )


@router.post("/hosts", response_model=HostResponse, status_code=201)
async def create_host(host_data: HostCreate, db: Session = Depends(get_db)):
    """
    Register a new host for monitoring.

    Args:
        host_data: Host creation data
        db: Database session

    Returns:
        Created host details
    """
    # Check if host_id or name already exists
    existing = (
        db.query(Host)
        .filter((Host.host_id == host_data.host_id) | (Host.name == host_data.name))
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Host with this name or host_id already exists",
        )

    # Calculate frequency from cron if provided
    expected_freq = host_data.expected_frequency_seconds
    if host_data.cron_expression:
        try:
            # Validate cron expression
            croniter(host_data.cron_expression)
            expected_freq = calculate_frequency_from_cron(host_data.cron_expression)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cron expression: {str(e)}"
            )

    # Create host
    host = Host(
        name=host_data.name,
        host_id=host_data.host_id,
        token=host_data.token,
        cron_expression=host_data.cron_expression,
        expected_frequency_seconds=expected_freq,
        schedule_type=host_data.schedule_type,
        schedule_config=host_data.schedule_config,
        grace_period_seconds=host_data.grace_period_seconds,
        log_analysis_config=host_data.log_analysis_config,
        status="unknown",
    )

    db.add(host)
    db.commit()
    db.refresh(host)

    logger.info(f"Created new host: {host.name} ({host.host_id})")

    # Build heartbeat URL
    from src.config import get_settings

    settings = get_settings()
    heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}?token={host.token}"

    return HostResponse(
        id=host.id,
        name=host.name,
        host_id=host.host_id,
        heartbeat_url=heartbeat_url,
        cron_expression=host.cron_expression,
        expected_frequency_seconds=host.expected_frequency_seconds,
        schedule_type=host.schedule_type,
        schedule_config=host.schedule_config,
        grace_period_seconds=host.grace_period_seconds,
        log_analysis_config=host.log_analysis_config,
        last_seen=host.last_seen,
        status=host.status,
        created_at=host.created_at,
        updated_at=host.updated_at,
    )


@router.put("/hosts/{host_id}", response_model=HostResponse)
async def update_host(
    host_id: str,
    host_data: HostUpdate,
    db: Session = Depends(get_db),
):
    """
    Update host configuration.

    Args:
        host_id: Unique host identifier
        host_data: Update data
        db: Database session

    Returns:
        Updated host details
    """
    host = db.query(Host).filter(Host.host_id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    # Update fields
    if host_data.name is not None:
        host.name = host_data.name
    if host_data.cron_expression is not None:
        try:
            # Validate cron expression
            croniter(host_data.cron_expression)
            host.cron_expression = host_data.cron_expression
            # Recalculate frequency from cron
            host.expected_frequency_seconds = calculate_frequency_from_cron(host_data.cron_expression)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cron expression: {str(e)}"
            )
    if host_data.expected_frequency_seconds is not None:
        host.expected_frequency_seconds = host_data.expected_frequency_seconds
    if host_data.schedule_type is not None:
        host.schedule_type = host_data.schedule_type
    if host_data.schedule_config is not None:
        host.schedule_config = host_data.schedule_config
    if host_data.grace_period_seconds is not None:
        host.grace_period_seconds = host_data.grace_period_seconds
    if host_data.log_analysis_config is not None:
        host.log_analysis_config = host_data.log_analysis_config

    host.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(host)

    logger.info(f"Updated host: {host.name} ({host.host_id})")

    # Build heartbeat URL
    from src.config import get_settings

    settings = get_settings()
    heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}?token={host.token}"

    return HostResponse(
        id=host.id,
        name=host.name,
        host_id=host.host_id,
        heartbeat_url=heartbeat_url,
        cron_expression=host.cron_expression,
        expected_frequency_seconds=host.expected_frequency_seconds,
        schedule_type=host.schedule_type,
        schedule_config=host.schedule_config,
        grace_period_seconds=host.grace_period_seconds,
        log_analysis_config=host.log_analysis_config,
        last_seen=host.last_seen,
        status=host.status,
        created_at=host.created_at,
        updated_at=host.updated_at,
    )


@router.delete("/hosts/{host_id}")
async def delete_host(host_id: str, db: Session = Depends(get_db)):
    """
    Delete a host from monitoring.

    Args:
        host_id: Unique host identifier
        db: Database session

    Returns:
        Success message
    """
    host = db.query(Host).filter(Host.host_id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    host_name = host.name
    db.delete(host)
    db.commit()

    logger.info(f"Deleted host: {host_name} ({host_id})")

    return {
        "status": "success",
        "message": f"Host {host_id} deleted",
    }


@router.post("/hosts/generate-token")
async def generate_token():
    """
    Generate a secure random token for host authentication.

    Returns:
        Generated token
    """
    token = secrets.token_urlsafe(32)

    return {
        "token": token,
    }


@router.get("/hosts/config/all")
async def get_all_configurations(db: Session = Depends(get_db)):
    """
    Get all host configurations in a simplified format for easy viewing.

    Returns:
        List of host configurations with key settings
    """
    hosts = db.query(Host).all()

    configs = []
    for host in hosts:
        # Parse log analysis config if present
        log_analysis_enabled = False
        if host.log_analysis_config:
            try:
                log_config = json.loads(host.log_analysis_config)
                log_analysis_enabled = log_config.get("enabled", False)
            except json.JSONDecodeError:
                log_analysis_enabled = False

        # Build heartbeat URL
        from src.config import get_settings
        settings = get_settings()
        heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}?token={host.token}"

        configs.append({
            "host_id": host.host_id,
            "name": host.name,
            "status": host.status,
            "heartbeat_url": heartbeat_url,
            "cron_expression": host.cron_expression,
            "heartbeat_frequency_seconds": host.expected_frequency_seconds,
            "heartbeat_frequency_minutes": host.expected_frequency_seconds // 60,
            "grace_period_seconds": host.grace_period_seconds,
            "schedule_type": host.schedule_type,
            "log_analysis_enabled": log_analysis_enabled,
            "last_seen": host.last_seen.isoformat() if host.last_seen else None,
            "created_at": host.created_at.isoformat(),
            "updated_at": host.updated_at.isoformat(),
        })

    return {
        "total": len(configs),
        "hosts": configs
    }


@router.patch("/hosts/{host_id}/config")
async def update_host_config(
    host_id: str,
    cron_expression: str = None,
    frequency_seconds: int = None,
    grace_period_seconds: int = None,
    schedule_type: str = None,
    db: Session = Depends(get_db),
):
    """
    Quick update of host configuration (frequency and schedule).

    Args:
        host_id: Unique host identifier
        cron_expression: Cron expression for heartbeat frequency (optional, overrides frequency_seconds)
        frequency_seconds: New heartbeat frequency (optional)
        grace_period_seconds: New grace period (optional)
        schedule_type: New schedule type (optional): 'always' or 'business_hours'
        db: Database session

    Returns:
        Updated configuration
    """
    host = db.query(Host).filter(Host.host_id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    # Track what was updated
    updates = []

    if cron_expression is not None:
        try:
            # Validate cron expression
            croniter(cron_expression)
            host.cron_expression = cron_expression
            # Calculate frequency from cron
            calculated_freq = calculate_frequency_from_cron(cron_expression)
            host.expected_frequency_seconds = calculated_freq
            updates.append(f"cron expression to '{cron_expression}' (calculated frequency: {calculated_freq}s)")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cron expression: {str(e)}"
            )
    elif frequency_seconds is not None:
        if frequency_seconds < 10:
            raise HTTPException(
                status_code=400,
                detail="Frequency must be at least 10 seconds"
            )
        host.expected_frequency_seconds = frequency_seconds
        updates.append(f"frequency to {frequency_seconds}s ({frequency_seconds // 60}m)")

    if grace_period_seconds is not None:
        if grace_period_seconds < 0:
            raise HTTPException(
                status_code=400,
                detail="Grace period must be positive"
            )
        host.grace_period_seconds = grace_period_seconds
        updates.append(f"grace period to {grace_period_seconds}s")

    if schedule_type is not None:
        if schedule_type not in ["always", "business_hours", "custom"]:
            raise HTTPException(
                status_code=400,
                detail="Schedule type must be 'always', 'business_hours', or 'custom'"
            )
        host.schedule_type = schedule_type
        updates.append(f"schedule to {schedule_type}")

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No updates provided"
        )

    host.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(host)

    logger.info(f"Updated {host.name} ({host_id}): {', '.join(updates)}")

    return {
        "status": "success",
        "host_id": host_id,
        "name": host.name,
        "updates": updates,
        "current_config": {
            "cron_expression": host.cron_expression,
            "frequency_seconds": host.expected_frequency_seconds,
            "frequency_minutes": host.expected_frequency_seconds // 60,
            "grace_period_seconds": host.grace_period_seconds,
            "schedule_type": host.schedule_type,
        }
    }
