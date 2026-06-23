#!/usr/bin/env bash
# Lightweight wiring check: confirms the plugin manifest, launcher, and package
# entry point are intact. Kept dependency-free so it runs in bare CI without
# provisioning the full uv environment.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== smoke: plugin manifest is valid JSON with a name ==="
python3 - <<'PY'
import json, pathlib, sys
m = json.loads(pathlib.Path(".claude-plugin/plugin.json").read_text())
assert m.get("name"), "plugin.json missing 'name'"
assert len(m.get("keywords", [])) == 20, f"expected 20 keywords, got {len(m.get('keywords', []))}"
print("  ok: name =", m["name"], "keywords =", len(m["keywords"]))
PY

echo "=== smoke: no root-level plugin.json ==="
if [ -f plugin.json ]; then
    echo "  FAIL: root plugin.json must not exist" >&2
    exit 1
fi
echo "  ok: single manifest at .claude-plugin/plugin.json"

echo "=== smoke: MCP launcher bash syntax ==="
bash -n scripts/mcp-server.sh && echo "  ok: scripts/mcp-server.sh"

echo "=== smoke: package entry point parses ==="
python3 -m compileall -q src/searxng_mcp >/dev/null && echo "  ok: src/searxng_mcp compiles"

echo "=== smoke: all good ==="
