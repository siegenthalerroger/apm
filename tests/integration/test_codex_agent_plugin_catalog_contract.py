"""One ``apm pack --format agent-plugin`` run yields a bundle its Codex catalog entry points at."""

from __future__ import annotations

import pytest

from tests.integration._codex_agent_plugin_kit import (
    MCP_SERVER,
    PLUGIN,
    SKILL,
    CodexAgentPluginWorld,
    read_json,
)
from tests.integration._marketplace_pack_kit import evidence

pytestmark = [pytest.mark.integration, pytest.mark.component]


def test_codex_catalog_entry_matches_generated_agent_plugin_bundle(tmp_path):
    world = CodexAgentPluginWorld.create(tmp_path)
    world.install()

    result = world.pack()

    assert result.returncode == 0, evidence(result)
    entry = world.catalog_entry()
    bundle = world.catalog_source_dir()
    manifest = read_json(bundle / "plugin.json")
    assert entry["name"] == manifest["name"] == PLUGIN
    assert entry["source"]["source"] == "local"
    assert bundle == (world.project / "build" / f"{PLUGIN}-{manifest['version']}").resolve()
    assert bundle.is_relative_to(world.project.resolve())
    assert list(read_json(bundle / "mcp.json")["mcpServers"]) == [MCP_SERVER]
    assert (bundle / "skills" / SKILL / "SKILL.md").is_file()
    assert not (bundle / ".codex-plugin").exists()


def test_codex_catalog_source_is_declared_not_derived_from_pack_output(tmp_path):
    world = CodexAgentPluginWorld.create(tmp_path)
    world.install()

    result = world.pack("--output", "dist")

    assert result.returncode == 0, evidence(result)
    assert (world.project / "dist" / f"{PLUGIN}-1.0.0" / "plugin.json").is_file()
    assert world.catalog_entry()["source"]["path"] == f"./build/{PLUGIN}-1.0.0"
    assert not world.catalog_source_dir().exists()


def test_hooks_still_fail_the_agent_plugin_pack_before_any_write(tmp_path):
    world = CodexAgentPluginWorld.create(tmp_path)
    world.install()
    hooks = world.project / ".apm" / "hooks" / "hooks.json"
    hooks.parent.mkdir(parents=True)
    hooks.write_text('{"preCommit": [{"command": "lint"}]}', encoding="utf-8")

    result = world.pack()

    assert result.returncode == 1, evidence(result)
    assert "non-portable primitives would be discarded" in " ".join(
        (result.stdout + result.stderr).split()
    )
    assert not (world.project / "build").exists()
