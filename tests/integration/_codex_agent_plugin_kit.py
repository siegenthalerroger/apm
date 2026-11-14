"""Shared fixture project for the Agent Plugin bundle plus Codex catalog route."""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from tests.integration._marketplace_pack_kit import evidence
from tests.utils.apm_lifecycle_runner import ApmLifecycleRunner, CommandResult
from tests.utils.isolated_apm_environment import IsolatedApmEnvironment

FIXTURE = Path(__file__).parents[1] / "fixtures" / "codex_agent_plugin"
PLUGIN = "codex-demo"
SKILL = "demo"
MCP_SERVER = "codex-demo-server"
CATALOG = Path(".agents/plugins/marketplace.json")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class CodexAgentPluginWorld:
    """A copy of the committed fixture and an APM runner that inherits no user state."""

    root: Path
    project: Path
    runner: ApmLifecycleRunner
    env: dict[str, str]

    @classmethod
    def create(cls, tmp_path: Path) -> CodexAgentPluginWorld:
        isolated = IsolatedApmEnvironment.create(tmp_path / "w", base_env=dict(os.environ))
        project = isolated.work_root / "producer"
        shutil.copytree(FIXTURE, project)
        return cls(
            root=isolated.root,
            project=project,
            runner=ApmLifecycleRunner((sys.executable, "-m", "apm_cli.entrypoint")),
            env=isolated.subprocess_env(),
        )

    def apm(self, *args: str) -> CommandResult:
        return self.runner.run(args, cwd=self.project, env=self.env, scenario_id=" ".join(args))

    def install(self) -> None:
        """Let APM write the lockfile that carries the MCP server into the bundle."""
        result = self.apm("install", "--target", "codex")
        assert result.returncode == 0, evidence(result)

    def pack(self, *args: str) -> CommandResult:
        return self.apm("pack", "--format", "agent-plugin", *args)

    def catalog_entry(self) -> dict:
        (entry,) = read_json(self.project / CATALOG)["plugins"]
        return entry

    def catalog_source_dir(self) -> Path:
        return (self.project / self.catalog_entry()["source"]["path"]).resolve()
