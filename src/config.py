"""Configuration management."""
import os
from typing import Any, Dict, List, Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")
    api_secret_key: str = Field(default="dev-secret-key", alias="API_SECRET_KEY")

    # Database
    database_url: str = Field(default="sqlite:///data/db.sqlite", alias="DATABASE_URL")

    # Discord
    discord_webhook_url: str = Field(..., alias="DISCORD_WEBHOOK_URL")

    # LLM API
    llm_api_url: str = Field(..., alias="LLM_API_URL")
    llm_api_key: str = Field(..., alias="LLM_API_KEY")
    llm_default_model: str = Field(default="claude-sonnet-4.5", alias="LLM_DEFAULT_MODEL")

    # Healthchecks.io
    healthchecks_url: Optional[str] = Field(default=None, alias="HEALTHCHECKS_URL")

    # Business Hours
    business_hours_start: str = Field(default="08:00", alias="BUSINESS_HOURS_START")
    business_hours_end: str = Field(default="18:00", alias="BUSINESS_HOURS_END")
    business_hours_days: str = Field(
        default="1,2,3,4,5", alias="BUSINESS_HOURS_DAYS"
    )  # Monday=1, Sunday=7
    business_hours_timezone: str = Field(
        default="America/New_York", alias="BUSINESS_HOURS_TIMEZONE"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Paths
    config_dir: str = Field(default="/app/config", alias="CONFIG_DIR")
    ssh_key_path: str = Field(default="/root/.ssh", alias="SSH_KEY_PATH")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def load_hosts_config(config_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load host configurations from YAML file.

    Args:
        config_path: Path to hosts.yaml file. If None, uses default location.

    Returns:
        List of host configuration dictionaries.
    """
    if config_path is None:
        settings = get_settings()
        config_path = os.path.join(settings.config_dir, "hosts.yaml")

    if not os.path.exists(config_path):
        # Return empty list if config doesn't exist yet
        return []

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    return data.get("hosts", []) if data else []


def save_hosts_config(hosts: List[Dict[str, Any]], config_path: Optional[str] = None):
    """
    Save host configurations to YAML file.

    Args:
        hosts: List of host configuration dictionaries.
        config_path: Path to hosts.yaml file. If None, uses default location.
    """
    if config_path is None:
        settings = get_settings()
        config_path = os.path.join(settings.config_dir, "hosts.yaml")

    # Ensure directory exists
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, "w") as f:
        yaml.dump({"hosts": hosts}, f, default_flow_style=False, sort_keys=False)
