# Codex CLI route fixture

A portable plugin (one skill, one stdio MCP server) and the Codex catalog
entry that points at its packed bundle. Nothing here is generated output.

```bash
apm install --target codex
apm pack --format agent-plugin
```

This writes `build/codex-demo-1.0.0/` and `.agents/plugins/marketplace.json`.
To load the result in Codex CLI 0.163.0 or later:

```bash
codex plugin marketplace add .
codex plugin add codex-demo@codex-demo
codex plugin list
codex mcp list
```

`tests/integration/test_codex_agent_plugin_catalog_contract.py` checks the
generated files; `tests/integration/test_codex_agent_plugin_native_install.py`
runs the Codex commands when `codex` is on `PATH`.
