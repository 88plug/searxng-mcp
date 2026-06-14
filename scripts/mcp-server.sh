#!/usr/bin/env bash
# mcp-server.sh — launch the searxng-mcp stdio server, resolving uv robustly.
#
# WHY: plugin.json used "command": "uvx", which assumes uv/uvx is on the PATH Claude
# Code spawns MCP servers with — often it is NOT (uv lives under ~/.local/bin, off
# the spawn PATH; or isn't installed; or system python is <3.11). That makes the
# server silently "Failed to connect". This launcher resolves uv (PATH -> ~/.local/bin
# -> plugin data dir -> one-time auto-install), provisions a >=3.11 interpreter, and
# runs the package FROM THE LOCAL INSTALL (no git re-fetch).
set -euo pipefail

if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  PLUGIN_ROOT="$CLAUDE_PLUGIN_ROOT"
else
  PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
fi
DATA_ROOT="${CLAUDE_PLUGIN_DATA:-${HOME}/.claude/plugins/data}/searxng"

_can_run_uv() { [ -x "$1" ] && "$1" --version >/dev/null 2>&1; }
UV=""
if [ -n "${SEARXNG_UV:-}" ] && _can_run_uv "$SEARXNG_UV"; then
  UV="$SEARXNG_UV"
elif command -v uv >/dev/null 2>&1 && _can_run_uv "$(command -v uv)"; then
  UV="$(command -v uv)"
elif _can_run_uv "${HOME}/.local/bin/uv"; then
  UV="${HOME}/.local/bin/uv"
elif _can_run_uv "${DATA_ROOT}/bin/uv"; then
  UV="${DATA_ROOT}/bin/uv"
elif command -v curl >/dev/null 2>&1; then
  dest_bin="${DATA_ROOT}/bin"; mkdir -p "$dest_bin"
  UV_INSTALL_DIR="$dest_bin" UV_UNMANAGED_INSTALL=1 \
    sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh" >/dev/null 2>&1 || true
  _can_run_uv "${dest_bin}/uv" && UV="${dest_bin}/uv"
fi
if [ -z "$UV" ]; then
  echo "searxng-mcp: could not resolve uv — install uv (https://docs.astral.sh/uv/) or set SEARXNG_UV" >&2
  exit 1
fi

cd "$PLUGIN_ROOT"
exec "$UV" run --project "$PLUGIN_ROOT" --python ">=3.11" python -m searxng_mcp "$@"
