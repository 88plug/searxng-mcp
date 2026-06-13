#!/usr/bin/env python3
"""Validate one Claude Code plugin against the failure modes that have actually
shipped to 88plug users. Designed for CI on every push (rolling plugins ship each
commit, so this is the safety net). Hard-errors only on unambiguous breakage;
softer portability/hygiene issues are warnings.

usage: validate_plugin.py [PLUGIN_ROOT]   (default ".")
exit 0 = clean, 1 = errors found.
"""
from __future__ import annotations
import sys, os, re, json, shutil, subprocess
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
errors: list[str] = []
warns: list[str] = []


def err(m): errors.append(m)
def warn(m): warns.append(m)


def rel(p):
    try: return str(Path(p).relative_to(ROOT))
    except Exception: return str(p)


# --- 1. plugin.json: valid JSON + has a name ---------------------------------
man = ROOT / ".claude-plugin" / "plugin.json"
if not man.exists():
    err(".claude-plugin/plugin.json is missing")
else:
    try:
        m = json.loads(man.read_text())
        if not m.get("name"):
            err("plugin.json: required 'name' field missing")
    except Exception as e:
        err(f"plugin.json: invalid JSON — {e}")

# --- 2. bash default-form var in a MANIFEST (Claude Code does not substitute it)
# Only manifests are variable-substituted; the ${VAR:-default} form inside a .sh
# script is legitimate, so scope this to the JSON manifests only.
BAD = re.compile(r'\$\{CLAUDE_PLUGIN_(?:ROOT|DATA):-')
manifests = [man, ROOT / ".mcp.json", ROOT / "hooks" / "hooks.json"]
for p in manifests:
    if p.exists():
        if BAD.search(p.read_text()):
            err(f"{rel(p)}: uses ${{CLAUDE_PLUGIN_*:-default}} — Claude Code substitutes "
                f"only the plain ${{CLAUDE_PLUGIN_ROOT}} form; the :- default is left literal")

# --- 3. skill/command/agent frontmatter must parse (the ': ' YAML break) ------
# Skills & agents REQUIRE name+description (that pair is the trigger surface, and
# the ': ' break silently drops it). Commands derive their name from the filename
# and only carry a description, so for commands we just require a clean parse.
def _frontmatter(md):
    txt = md.read_text()
    if not txt.lstrip().startswith("---"):
        return None, "no YAML frontmatter"
    parts = txt.split("---", 2)
    if len(parts) < 3:
        return None, "unterminated frontmatter"
    if yaml is None:
        return {}, None
    try:
        d = yaml.safe_load(parts[1])
    except Exception as e:
        return None, (f"frontmatter YAML parse error ({e.__class__.__name__}) — "
                      "often an unquoted description containing ': '")
    if not isinstance(d, dict):
        return None, "frontmatter is not a mapping"
    return d, None

for md in list(ROOT.glob("skills/**/SKILL.md")) + list(ROOT.glob("agents/**/*.md")):
    d, e = _frontmatter(md)
    if e:
        err(f"{rel(md)}: {e}")
    elif not d.get("name") or not d.get("description"):
        err(f"{rel(md)}: frontmatter missing name/description (silently dropped by a ': ' break?)")

for md in list(ROOT.glob("commands/**/*.md")):
    d, e = _frontmatter(md)
    if e:
        err(f"{rel(md)}: {e}")
    elif not d.get("description"):
        warn(f"{rel(md)}: command frontmatter has no description")

# --- 4. hooks.json valid + scripts present/executable/parse -------------------
hj = ROOT / "hooks" / "hooks.json"
if hj.exists():
    try:
        json.loads(hj.read_text())
    except Exception as e:
        err(f"hooks/hooks.json: invalid JSON — {e}")

# --- 5. shell scripts: bash -n is a hard error; zsh -n is a portability warning
shells = {s: shutil.which(s) for s in ("bash", "zsh")}
for sh in sorted(set(ROOT.glob("hooks/**/*.sh")) | set(ROOT.glob("scripts/**/*.sh"))):
    if shells["bash"]:
        r = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stderr.strip().splitlines() or ["parse error"])[-1]
            err(f"{rel(sh)}: bash -n syntax error — {tail}")
    if shells["zsh"]:
        r = subprocess.run(["zsh", "-n", str(sh)], capture_output=True, text=True)
        if r.returncode != 0:
            tail = (r.stderr.strip().splitlines() or ["parse error"])[-1]
            warn(f"{rel(sh)}: not zsh-parseable — {tail} "
                 "(breaks if a slash command sources it in a zsh user shell)")
    if "hooks" in sh.parts and not os.access(sh, os.X_OK):
        warn(f"{rel(sh)}: missing executable bit (test -x fails)")

# --- report ------------------------------------------------------------------
for w in warns:
    print(f"::warning:: {w}" if os.environ.get("GITHUB_ACTIONS") else f"WARN  {w}")
for e in errors:
    print(f"::error:: {e}" if os.environ.get("GITHUB_ACTIONS") else f"ERROR {e}")
print(f"\n{rel(ROOT) or '.'}: {len(errors)} error(s), {len(warns)} warning(s)")
sys.exit(1 if errors else 0)
