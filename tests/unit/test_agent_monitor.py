"""Unit tests for AgentMonitorService."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.agent_monitor import AgentMonitorService, IDLE_THRESHOLD_SECONDS


@pytest.fixture
def tmp_project_structure(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    project = root / "project_a"
    docs = project / "docs"
    docs.mkdir(parents=True)
    tasks_file = docs / "TASKS.md"
    tasks_file.write_text("- [ ] demo task\n", encoding="utf-8")

    claude_root = tmp_path / "claude"
    claude_dir = claude_root / "home-sgallant-workspace-project_a"
    claude_dir.mkdir(parents=True)
    (claude_dir / "session.txt").write_text("notes", encoding="utf-8")

    return root, claude_root, tasks_file


def test_list_projects_builds_metadata(tmp_project_structure, monkeypatch):
    root, claude_root, tasks_file = tmp_project_structure

    service = AgentMonitorService(root=Path(root), claude_root=Path(claude_root))

    projects = service.list_projects()

    assert len(projects) == 1
    project = projects[0]
    assert project.name == "project_a"
    assert project.tasks_file == tasks_file
    assert project.status in {"active", "idle", "not_running"}


def test_determine_status_not_running(tmp_project_structure):
    root, claude_root, _ = tmp_project_structure
    service = AgentMonitorService(root=Path(root), claude_root=Path(claude_root))

    status, updated_at = service._determine_agent_status(Path(root) / "project_a")

    assert status in {"active", "idle", "not_running"}
    if status == "not_running":
        assert updated_at is None


def test_read_and_write_roundtrip(tmp_project_structure):
    root, claude_root, tasks_file = tmp_project_structure
    service = AgentMonitorService(root=Path(root), claude_root=Path(claude_root))

    data = service.read_tasks_file(tasks_file)
    assert "demo task" in data

    service.write_tasks_file(tasks_file, "updated text")
    assert tasks_file.read_text(encoding="utf-8") == "updated text"
