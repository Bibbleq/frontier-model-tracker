#!/usr/bin/env python3
"""Verify an assembled site against the manifest before it is published.

The data contract promises a set of files at stable paths, each with a byte
length and a SHA-256. That promise is only worth anything if something checks
the assembled tree actually keeps it, so this runs in the publish workflow
between assembling the site and uploading it.

Checks both the latest tree and the pinned version tree, because a consumer
that pins is relying on the pinned copy being identical, not merely present.

Usage: python scripts/check_published_tree.py _site
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def check_tree(root: Path, manifest: dict, label: str) -> int:
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        fail(f"{label}: manifest.json is missing")

    published = json.loads(manifest_path.read_text(encoding="utf-8"))
    if published != manifest:
        fail(f"{label}: manifest.json differs from the generated manifest")

    for entry in manifest["files"]:
        target = root / entry["path"]
        if not target.exists():
            fail(f"{label}: {entry['path']} is promised by the manifest but absent")
        payload = target.read_bytes()
        if len(payload) != entry["bytes"]:
            fail(
                f"{label}: {entry['path']} is {len(payload)} bytes, "
                f"manifest says {entry['bytes']}"
            )
        digest = hashlib.sha256(payload).hexdigest()
        if digest != entry["sha256"]:
            fail(f"{label}: {entry['path']} checksum does not match the manifest")
    return len(manifest["files"])


def main() -> None:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    if not site.is_dir():
        fail(f"{site} is not a directory")

    manifest = json.loads((site / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["dataset_version"]

    count = check_tree(site, manifest, "latest")
    pinned = site / f"v{version}"
    if not pinned.is_dir():
        fail(f"the pinned tree v{version} promised by the contract was not assembled")
    check_tree(pinned, manifest, f"v{version}")

    # The viewer is not part of the contract, but publishing the data without
    # it would still be a broken deploy.
    for page in ("index.html", "dashboard.html", "style.css"):
        if not (site / page).exists():
            fail(f"{page} is missing from the assembled site")

    print(
        f"Published tree verified: contract v{manifest['contract_version']}, "
        f"dataset v{version}, {count} files in both the latest and v{version} trees."
    )


if __name__ == "__main__":
    main()
