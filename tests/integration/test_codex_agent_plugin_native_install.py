"""Real Codex CLI installs an APM-packed Agent Plugin; no agent turn or MCP process runs."""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import pytest

from tests.integration._codex_agent_plugin_kit import (
    MCP_SERVER,
    PLUGIN,
    SKILL,
    CodexAgentPluginWorld,
)
from tests.integration._marketplace_pack_kit import evidence
from tests.utils.apm_lifecycle_runner import ApmLifecycleRunner, CommandResult

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.integration,
    pytest.mark.requires_runtime_codex(min_version="0.163.0"),
]


def _codex(world: CodexAgentPluginWorld, consumer: Path, label: str, *args: str) -> CommandResult:
    """Run Codex signed out, outside the producer project, and keep the transcript."""
    result = ApmLifecycleRunner((shutil.which("codex"),)).run(
        args,
        cwd=consumer,
        env={**world.env, "CODEX_HOME": str(consumer / "codex-home")},
        scenario_id=label,
    )
    (world.root / f"{label}-evidence.json").write_text(
        json.dumps(asdict(result), default=str, indent=2), encoding="utf-8"
    )
    assert result.returncode == 0, evidence(result)
    return result


def test_codex_cli_discovers_installs_and_loads_packed_agent_plugin(tmp_path):
    world = CodexAgentPluginWorld.create(tmp_path)
    world.install()
    packed = world.pack()
    assert packed.returncode == 0, evidence(packed)
    consumer = world.root / "consumer"
    (consumer / "codex-home").mkdir(parents=True)
    plugin_id = f"{PLUGIN}@{PLUGIN}"

    _codex(
        world, consumer, "codex-marketplace-add", "plugin", "marketplace", "add", str(world.project)
    )
    listed = json.loads(
        _codex(world, consumer, "codex-discover", "plugin", "list", "--json", "--available").stdout
    )
    _codex(world, consumer, "codex-plugin-add", "plugin", "add", plugin_id)
    installed = json.loads(
        _codex(world, consumer, "codex-installed", "plugin", "list", "--json").stdout
    )
    servers = json.loads(_codex(world, consumer, "codex-mcp-list", "mcp", "list", "--json").stdout)
    prompt = _codex(world, consumer, "codex-prompt-input", "debug", "prompt-input", "hello").stdout

    assert [plugin["pluginId"] for plugin in listed["available"]] == [plugin_id]
    (plugin,) = installed["installed"]
    assert (plugin["pluginId"], plugin["version"], plugin["enabled"]) == (plugin_id, "1.0.0", True)
    assert Path(plugin["source"]["path"]).resolve() == world.catalog_source_dir()
    (server,) = servers
    assert (server["name"], server["enabled"]) == (MCP_SERVER, True)
    assert server["transport"]["command"] == MCP_SERVER
    assert Path(server["transport"]["cwd"]).is_relative_to(consumer / "codex-home" / "plugins")
    assert f"{PLUGIN}:{SKILL}: " in prompt
