"""Heartbeat API endpoints."""
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from src.database import Heartbeat, Host, get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/heartbeat/{host_id}")
async def receive_heartbeat(
    host_id: str,
    request: Request,
    authorization: Optional[str] = Header(None),
    token: Optional[str] = None,  # Accept token as query parameter
    db: Session = Depends(get_db),
):
    """
    Receive heartbeat from a host.

    Token can be provided in two ways:
    1. As Authorization header: "Bearer <token>"
    2. As query parameter: ?token=<token>

    Args:
        host_id: Unique host identifier
        request: FastAPI request object
        authorization: Bearer token from header
        token: Token from query parameter
        db: Database session

    Returns:
        Success message
    """
    # Find host by host_id
    host = db.query(Host).filter(Host.host_id == host_id).first()

    if not host:
        logger.warning(f"Heartbeat from unknown host: {host_id}")
        raise HTTPException(status_code=404, detail="Host not found")

    # Verify token - check header first, then query parameter
    provided_token = None
    if authorization and authorization.startswith("Bearer "):
        provided_token = authorization[7:]
    elif token:
        provided_token = token

    if provided_token != host.token:
        logger.warning(f"Invalid token for host: {host_id}")
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get source IP
    source_ip = request.client.host if request.client else None

    # Create heartbeat record
    heartbeat = Heartbeat(
        host_id=host.id,
        timestamp=datetime.utcnow(),
        source_ip=source_ip,
    )
    db.add(heartbeat)

    # Update host last_seen and status
    host.last_seen = datetime.utcnow()

    # Update status to 'up' if it was down
    if host.status != "up":
        logger.info(f"Host {host.name} status changed: {host.status} -> up")
        host.status = "up"

    db.commit()

    logger.debug(f"Heartbeat received from {host.name} ({host_id}) at {source_ip}")

    return {
        "status": "success",
        "message": "Heartbeat received",
        "host_id": host_id,
        "timestamp": heartbeat.timestamp.isoformat(),
    }


@router.get("/heartbeat/{host_id}/history")
async def get_heartbeat_history(
    host_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get heartbeat history for a host.

    Args:
        host_id: Unique host identifier
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of heartbeat records
    """
    # Find host
    host = db.query(Host).filter(Host.host_id == host_id).first()

    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    # Get heartbeats
    heartbeats = (
        db.query(Heartbeat)
        .filter(Heartbeat.host_id == host.id)
        .order_by(Heartbeat.timestamp.desc())
        .limit(limit)
        .all()
    )

    return {
        "host_id": host_id,
        "host_name": host.name,
        "count": len(heartbeats),
        "heartbeats": [
            {
                "timestamp": hb.timestamp.isoformat(),
                "source_ip": hb.source_ip,
            }
            for hb in heartbeats
        ],
    }
