#!/usr/bin/env python3
"""Assemble the GitHub Pages artifact from generated data and saved snapshots."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"
SCHEMA = ROOT / "schema"
WEB = ROOT / "web"
SNAPSHOTS = ROOT / "published"


def assemble(site: Path) -> None:
    if site.exists():
        raise SystemExit(f"ERROR: {site} already exists; refusing to mix publishing trees")

    data_target = site / "data"
    schema_target = site / "schema"
    data_target.mkdir(parents=True)
    schema_target.mkdir()

    for name in ("index.html", "dashboard.html", "style.css"):
        shutil.copy2(WEB / name, site / name)

    for name in ("events.json", "status.json"):
        shutil.copy2(GENERATED / name, data_target / name)
    for source in GENERATED.glob("*.csv"):
        shutil.copy2(source, data_target / source.name)
    for source in SCHEMA.glob("*.json"):
        shutil.copy2(source, schema_target / source.name)
    shutil.copy2(GENERATED / "manifest.json", site / "manifest.json")

    # Versioned trees are immutable snapshots committed under published/.
    # copytree preserves every retained contract+dataset pair in the artifact.
    if SNAPSHOTS.is_dir():
        shutil.copytree(SNAPSHOTS, site, dirs_exist_ok=True)

    (site / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")


def main() -> None:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    assemble(site)
    print(f"Assembled {site}")


if __name__ == "__main__":
    main()
