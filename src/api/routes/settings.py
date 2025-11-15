"""System settings API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.database import Config, get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class SettingResponse(BaseModel):
    """Schema for setting response."""

    key: str
    value: str
    updated_at: str


class WebhookConfigUpdate(BaseModel):
    """Schema for updating webhook configuration."""

    webhook_url: str


class UpstreamMonitoringConfig(BaseModel):
    """Schema for upstream monitoring configuration."""

    enabled: bool
    url: str
    frequency_seconds: int = 300  # Default 5 minutes


@router.get("/settings/webhook")
async def get_webhook_config(db: Session = Depends(get_db)):
    """
    Get webhook configuration.

    Returns:
        Current webhook URL from database or environment
    """
    # Try to get from database first
    db_config = db.query(Config).filter(Config.key == "discord_webhook_url").first()

    if db_config:
        return {
            "webhook_url": db_config.value,
            "source": "database",
            "updated_at": db_config.updated_at.isoformat(),
        }

    # Fallback to environment variable
    from src.config import get_settings

    try:
        settings = get_settings()
        return {
            "webhook_url": settings.discord_webhook_url,
            "source": "environment",
            "updated_at": None,
        }
    except Exception:
        return {
            "webhook_url": "",
            "source": "none",
            "updated_at": None,
        }


@router.put("/settings/webhook")
async def update_webhook_config(
    config: WebhookConfigUpdate, db: Session = Depends(get_db)
):
    """
    Update webhook configuration.

    Args:
        config: New webhook configuration
        db: Database session

    Returns:
        Updated configuration
    """
    from datetime import datetime

    # Check if config exists
    db_config = db.query(Config).filter(Config.key == "discord_webhook_url").first()

    if db_config:
        # Update existing
        db_config.value = config.webhook_url
        db_config.updated_at = datetime.utcnow()
    else:
        # Create new
        db_config = Config(
            key="discord_webhook_url",
            value=config.webhook_url,
            updated_at=datetime.utcnow(),
        )
        db.add(db_config)

    db.commit()
    db.refresh(db_config)

    logger.info(f"Updated webhook URL configuration")

    return {
        "status": "success",
        "webhook_url": db_config.value,
        "updated_at": db_config.updated_at.isoformat(),
    }


@router.get("/settings/upstream")
async def get_upstream_config(db: Session = Depends(get_db)):
    """
    Get upstream monitoring configuration.

    Returns:
        Current upstream monitoring settings
    """
    import json

    # Get from database
    db_enabled = db.query(Config).filter(Config.key == "upstream_monitoring_enabled").first()
    db_url = db.query(Config).filter(Config.key == "upstream_monitoring_url").first()
    db_freq = db.query(Config).filter(Config.key == "upstream_monitoring_frequency").first()

    # Get defaults from environment if not in database
    from src.config import get_settings
    settings = get_settings()

    return {
        "enabled": db_enabled.value == "true" if db_enabled else False,
        "url": db_url.value if db_url else (settings.healthchecks_url or ""),
        "frequency_seconds": int(db_freq.value) if db_freq else 300,
        "source": "database" if db_url else "environment",
    }


@router.put("/settings/upstream")
async def update_upstream_config(
    config: UpstreamMonitoringConfig, db: Session = Depends(get_db)
):
    """
    Update upstream monitoring configuration.

    Args:
        config: New upstream monitoring configuration
        db: Database session

    Returns:
        Updated configuration
    """
    from datetime import datetime

    # Update enabled flag
    db_enabled = db.query(Config).filter(Config.key == "upstream_monitoring_enabled").first()
    if db_enabled:
        db_enabled.value = "true" if config.enabled else "false"
        db_enabled.updated_at = datetime.utcnow()
    else:
        db_enabled = Config(
            key="upstream_monitoring_enabled",
            value="true" if config.enabled else "false",
            updated_at=datetime.utcnow(),
        )
        db.add(db_enabled)

    # Update URL
    db_url = db.query(Config).filter(Config.key == "upstream_monitoring_url").first()
    if db_url:
        db_url.value = config.url
        db_url.updated_at = datetime.utcnow()
    else:
        db_url = Config(
            key="upstream_monitoring_url",
            value=config.url,
            updated_at=datetime.utcnow(),
        )
        db.add(db_url)

    # Update frequency
    db_freq = db.query(Config).filter(Config.key == "upstream_monitoring_frequency").first()
    if db_freq:
        db_freq.value = str(config.frequency_seconds)
        db_freq.updated_at = datetime.utcnow()
    else:
        db_freq = Config(
            key="upstream_monitoring_frequency",
            value=str(config.frequency_seconds),
            updated_at=datetime.utcnow(),
        )
        db.add(db_freq)

    db.commit()

    logger.info(
        f"Updated upstream monitoring: enabled={config.enabled}, url={config.url}, freq={config.frequency_seconds}s"
    )

    return {
        "status": "success",
        "enabled": config.enabled,
        "url": config.url,
        "frequency_seconds": config.frequency_seconds,
    }


@router.get("/settings/all")
async def get_all_settings(db: Session = Depends(get_db)):
    """
    Get all system settings.

    Returns:
        All system configuration settings
    """
    from src.config import get_settings

    settings = get_settings()

    # Get database-stored settings
    db_webhook = db.query(Config).filter(Config.key == "discord_webhook_url").first()
    db_upstream_enabled = db.query(Config).filter(Config.key == "upstream_monitoring_enabled").first()
    db_upstream_url = db.query(Config).filter(Config.key == "upstream_monitoring_url").first()
    db_upstream_freq = db.query(Config).filter(Config.key == "upstream_monitoring_frequency").first()

    return {
        "webhook_url": db_webhook.value if db_webhook else settings.discord_webhook_url,
        "webhook_source": "database" if db_webhook else "environment",
        "upstream_monitoring": {
            "enabled": db_upstream_enabled.value == "true" if db_upstream_enabled else False,
            "url": db_upstream_url.value if db_upstream_url else (settings.healthchecks_url or ""),
            "frequency_seconds": int(db_upstream_freq.value) if db_upstream_freq else 300,
            "source": "database" if db_upstream_url else "environment",
        },
        "business_hours": {
            "start": settings.business_hours_start,
            "end": settings.business_hours_end,
            "days": settings.business_hours_days,
            "timezone": settings.business_hours_timezone,
        },
        "llm": {
            "api_url": settings.llm_api_url,
            "default_model": settings.llm_default_model,
        },
    }
