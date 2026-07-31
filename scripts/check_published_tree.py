#!/usr/bin/env python3
"""Verify the live tree and every immutable version snapshot before publishing."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_manifest(root: Path, label: str) -> dict:
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        fail(f"{label}: manifest.json is missing")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def check_tree(root: Path, manifest: dict, label: str) -> int:
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

    latest = load_manifest(site, "latest")
    count = check_tree(site, latest, "latest")

    expected = site / f"c{latest['contract_version']}" / f"v{latest['dataset_version']}"
    if not expected.is_dir():
        fail(
            "the immutable snapshot "
            f"c{latest['contract_version']}/v{latest['dataset_version']} is missing"
        )

    snapshots = 0
    for manifest_path in sorted(site.glob("c*/v*/manifest.json")):
        snapshot = manifest_path.parent
        relative = snapshot.relative_to(site).as_posix()
        match = re.fullmatch(r"c(\d+)/v(\d+)", relative)
        if not match:
            fail(f"invalid snapshot path: {relative}")
        manifest = load_manifest(snapshot, relative)
        if int(match.group(1)) != manifest["contract_version"]:
            fail(f"{relative}: path does not match contract_version")
        if int(match.group(2)) != manifest["dataset_version"]:
            fail(f"{relative}: path does not match dataset_version")
        check_tree(snapshot, manifest, relative)
        snapshots += 1

    if snapshots == 0:
        fail("no immutable contract snapshots were assembled")

    print(
        f"Published tree verified: latest contract v{latest['contract_version']}, "
        f"dataset v{latest['dataset_version']}, {count} payload files, "
        f"{snapshots} immutable snapshot(s)."
    )


if __name__ == "__main__":
    main()
