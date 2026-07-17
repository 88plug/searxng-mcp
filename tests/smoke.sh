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

# Thin PATH (simulates Claude GUI MCP spawn): only /usr/bin + /bin. Launcher must
# still resolve uv via abs paths / vendor bundle — never depend on interactive PATH.
echo "=== smoke: thin-PATH uv resolve (T2) ==="
_thin_resolve_uv() {
  # Mirror scripts/mcp-server.sh resolve order (resolve only — do not exec server).
  env -i HOME="$HOME" PATH="/usr/bin:/bin" \
    CLAUDE_PLUGIN_ROOT="$REPO_ROOT" \
    SEARXNG_UV="${SEARXNG_UV:-}" \
    bash -c '
      set -euo pipefail
      PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT}"
      DATA_ROOT="${HOME}/.claude/plugins/data/searxng"
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
      else
        vend="${PLUGIN_ROOT}/vendor/uv"
        if [ -d "$vend" ]; then
          os="$(uname -s 2>/dev/null)"; arch="$(uname -m 2>/dev/null)"
          case "$os" in
            Linux)
              case "$arch" in x86_64|amd64) arch=x86_64 ;; aarch64|arm64) arch=aarch64 ;; *) arch="" ;; esac
              libc=gnu
              if (ldd --version 2>&1 | grep -qi musl) || ls /lib/ld-musl-* >/dev/null 2>&1; then libc=musl; fi
              target="${arch:+${arch}-unknown-linux-${libc}}" ;;
            Darwin)
              case "$arch" in x86_64) arch=x86_64 ;; arm64|aarch64) arch=aarch64 ;; *) arch="" ;; esac
              target="${arch:+${arch}-apple-darwin}" ;;
            *) target="" ;;
          esac
          if [ -n "${target:-}" ]; then
            tb="${vend}/uv-${target}.tar.gz"
            if [ -f "$tb" ]; then
              dest="${DATA_ROOT}/bin"; mkdir -p "$dest"
              tar xzf "$tb" --strip-components=1 -C "$dest" >/dev/null 2>&1 || true
              chmod +x "$dest/uv" "$dest/uvx" 2>/dev/null || true
              _can_run_uv "$dest/uv" && UV="$dest/uv"
            fi
          fi
        fi
      fi
      [ -n "$UV" ] || { echo "FAIL: no uv under thin PATH" >&2; exit 1; }
      printf "%s\n" "$UV"
    '
}
THIN_UV="$(_thin_resolve_uv)" || {
  echo "  FAIL: thin-PATH uv resolve" >&2
  exit 1
}
echo "  ok: thin PATH resolved uv=$THIN_UV"

# Override must win even under thin PATH (and even if PATH has no uv).
if [ -x "$THIN_UV" ]; then
  OVR_UV="$(SEARXNG_UV="$THIN_UV" env -i HOME="$HOME" PATH="/usr/bin:/bin" \
    CLAUDE_PLUGIN_ROOT="$REPO_ROOT" SEARXNG_UV="$THIN_UV" \
    bash -c '
      set -euo pipefail
      _can_run_uv() { [ -x "$1" ] && "$1" --version >/dev/null 2>&1; }
      if [ -n "${SEARXNG_UV:-}" ] && _can_run_uv "$SEARXNG_UV"; then printf "%s\n" "$SEARXNG_UV"; exit 0; fi
      exit 1
    ')" || {
    echo "  FAIL: SEARXNG_UV override under thin PATH" >&2
    exit 1
  }
  [ "$OVR_UV" = "$THIN_UV" ] || {
    echo "  FAIL: SEARXNG_UV override mismatch (got $OVR_UV)" >&2
    exit 1
  }
  echo "  ok: SEARXNG_UV override under thin PATH"
fi

echo "=== smoke: all good ==="
