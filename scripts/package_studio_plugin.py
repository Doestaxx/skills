#!/usr/bin/env python3
"""Package the Doestaxx Studio plugin as a zip for upload in Claude chat.

Reads the doestaxx-studio entry from .claude-plugin/marketplace.json (so the
zip always matches the marketplace) and writes dist/doestaxx-studio.zip:

  doestaxx-studio/.claude-plugin/plugin.json
  doestaxx-studio/skills/<name>/...   one folder per skill, README.md left out

Usage: python3 scripts/package_studio_plugin.py [--out PATH] [--version X.Y.Z]
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = "doestaxx-studio"
SKIP_DIRS = {"__pycache__", ".pytest_cache"}
SKIP_FILES = {"README.md", ".DS_Store"}


def studio_entry():
    manifest = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    for plugin in manifest["plugins"]:
        if plugin["name"] == PLUGIN:
            return plugin
    raise SystemExit(f"no {PLUGIN} plugin in marketplace.json; run pnpm manifest")


def skill_files(skill_dir):
    for path in sorted(skill_dir.rglob("*")):
        rel = path.relative_to(skill_dir)
        if path.is_dir() or SKIP_DIRS & set(rel.parts) or path.name in SKIP_FILES:
            continue
        if path.suffix == ".pyc":
            continue
        yield path, rel


def build(out, version):
    entry = studio_entry()
    plugin_json = {
        "name": PLUGIN,
        "version": version,
        "description": entry["description"],
        "author": {"name": "Doestaxx", "url": "https://github.com/Doestaxx/skills"},
        "license": "MIT",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{PLUGIN}/.claude-plugin/plugin.json", json.dumps(plugin_json, indent=2) + "\n")
        for rel_skill in entry["skills"]:
            skill_dir = (ROOT / rel_skill).resolve()
            if not (skill_dir / "SKILL.md").is_file():
                raise SystemExit(f"{rel_skill} has no SKILL.md")
            for path, rel in skill_files(skill_dir):
                zf.write(path, f"{PLUGIN}/skills/{skill_dir.name}/{rel.as_posix()}")
                count += 1
    return len(entry["skills"]), count


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", default=str(ROOT / "dist" / f"{PLUGIN}.zip"))
    parser.add_argument("--version", default=(ROOT / "version.txt").read_text().strip())
    args = parser.parse_args(argv)
    skills, files = build(Path(args.out), args.version)
    print(f"wrote {args.out}: {skills} skills, {files} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
