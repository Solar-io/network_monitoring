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

    return {
        "webhook_url": db_webhook.value if db_webhook else settings.discord_webhook_url,
        "webhook_source": "database" if db_webhook else "environment",
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
