#!/usr/bin/env python3
"""Database migration script for M8.5 project service monitoring."""

import sys
from pathlib import Path

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.database import Base, engine, ProjectService, ServiceHealthCheck, Alert
from sqlalchemy import inspect, Column, Integer, ForeignKey


def table_exists(inspector, table_name: str) -> bool:
    """Check if a table exists in the database."""
    return table_name in inspector.get_table_names()


def column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Check if a column exists in the specified table."""
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def add_service_id_to_alerts(connection):
    """Add service_id column to alerts table if missing."""
    inspector = inspect(connection)

    if not column_exists(inspector, "alerts", "service_id"):
        print("Adding service_id column to alerts table...")
        connection.execute("ALTER TABLE alerts ADD COLUMN service_id INTEGER")
    else:
        print("service_id column already exists on alerts table")


def migrate():
    """Run migration steps for M8.5."""
    print("Running M8.5 migration...")

    inspector = inspect(engine)

    # Create project_services table if missing
    if not table_exists(inspector, "project_services"):
        print("Creating project_services table...")
        ProjectService.__table__.create(bind=engine)
    else:
        print("project_services table already exists")

    inspector = inspect(engine)
    # Create service_health_checks table if missing
    if not table_exists(inspector, "service_health_checks"):
        print("Creating service_health_checks table...")
        ServiceHealthCheck.__table__.create(bind=engine)
    else:
        print("service_health_checks table already exists")

    # Add service_id column to alerts table
    with engine.connect() as connection:
        add_service_id_to_alerts(connection)

    print("M8.5 migration complete!")


if __name__ == "__main__":
    migrate()
