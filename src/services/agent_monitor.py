"""Agent monitoring service for aggregating task files and agent status."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

AGENT_ROOT = Path("/home/sgallant/sync/software-development")
TASK_FILENAMES = ("TASKS.md", "tasks.md")
CLAUDE_PROJECTS_ROOT = Path("/home/sgallant/.claude/projects")
IDLE_THRESHOLD_SECONDS = 15 * 60  # 15 minutes


@dataclass
class AgentProject:
    """Represents a monitored project."""

    name: str
    project_path: Path
    tasks_file: Path
    status: str
    status_updated_at: Optional[float]
    file_mtime: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "project_path": str(self.project_path),
            "tasks_file": str(self.tasks_file),
            "status": self.status,
            "status_updated_at": self.status_updated_at,
            "file_mtime": self.file_mtime,
        }


class AgentMonitorService:
    """Service that discovers agent task files and determines status."""

    def __init__(self,
                 root: Path = AGENT_ROOT,
                 claude_root: Path = CLAUDE_PROJECTS_ROOT,
                 idle_threshold: int = IDLE_THRESHOLD_SECONDS):
        self.root = root
        self.claude_root = claude_root
        self.idle_threshold = idle_threshold

    def list_projects(self) -> List[AgentProject]:
        """List all projects with TASKS.md/tasks.md files."""
        projects: List[AgentProject] = []
        if not self.root.exists():
            return projects

        for project_dir in sorted(self.root.iterdir()):
            if not project_dir.is_dir():
                continue
            docs_dir = project_dir / "docs"
            if not docs_dir.exists():
                continue
            tasks_file = self._find_tasks_file(docs_dir)
            if not tasks_file:
                continue
            status, status_updated_at = self._determine_agent_status(project_dir)
            projects.append(
                AgentProject(
                    name=project_dir.name,
                    project_path=project_dir,
                    tasks_file=tasks_file,
                    status=status,
                    status_updated_at=status_updated_at,
                    file_mtime=tasks_file.stat().st_mtime,
                )
            )
        return projects

    def _find_tasks_file(self, docs_dir: Path) -> Optional[Path]:
        for filename in TASK_FILENAMES:
            file_path = docs_dir / filename
            if file_path.exists():
                return file_path
        return None

    def _determine_agent_status(self, project_dir: Path) -> tuple[str, Optional[float]]:
        # Claude Code encodes project paths with a leading hyphen
        # and converts both slashes and underscores to hyphens
        # e.g., /home/user/my_project -> -home-user-my-project
        claude_dir_name = "-" + str(project_dir).lstrip("/").replace("/", "-").replace("_", "-")
        claude_dir = self.claude_root / claude_dir_name
        if not claude_dir.exists():
            return "not_running", None

        latest_mtime = 0.0
        for child in claude_dir.iterdir():
            try:
                child_mtime = child.stat().st_mtime
            except OSError:
                continue
            latest_mtime = max(latest_mtime, child_mtime)

        if latest_mtime == 0:
            return "not_running", None

        now = time.time()
        if now - latest_mtime <= self.idle_threshold:
            return "active", latest_mtime
        return "idle", latest_mtime

    def read_tasks_file(self, tasks_path: Path) -> str:
        with open(tasks_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_tasks_file(self, tasks_path: Path, contents: str):
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tasks_path, "w", encoding="utf-8") as f:
            f.write(contents)


__all__ = ["AgentMonitorService", "AgentProject"]
