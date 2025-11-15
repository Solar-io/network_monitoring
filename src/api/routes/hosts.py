"""Host management API endpoints."""
import json
import logging
import secrets
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import Host, get_db
from src.database.schemas import HostCreate, HostResponse, HostStatus, HostUpdate

logger = logging.getLogger(__name__)

router = APIRouter()


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
    heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}"

    return HostResponse(
        id=host.id,
        name=host.name,
        host_id=host.host_id,
        heartbeat_url=heartbeat_url,
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

    # Create host
    host = Host(
        name=host_data.name,
        host_id=host_data.host_id,
        token=host_data.token,
        expected_frequency_seconds=host_data.expected_frequency_seconds,
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
    heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}"

    return HostResponse(
        id=host.id,
        name=host.name,
        host_id=host.host_id,
        heartbeat_url=heartbeat_url,
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
    heartbeat_url = f"http://{settings.api_host}:{settings.api_port}/api/v1/heartbeat/{host.host_id}"

    return HostResponse(
        id=host.id,
        name=host.name,
        host_id=host.host_id,
        heartbeat_url=heartbeat_url,
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
