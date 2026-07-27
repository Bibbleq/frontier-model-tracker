#!/usr/bin/env python3
"""One-shot P2 backfill of `archived_url` for drift-prone sources.

Living documentation pages are edited in place, so a citation that reads
correctly today may not attest the same claim next year. This attaches a
Wayback snapshot to the documentation sources, which are the ones most likely
to drift.

Snapshots are looked up separately (archive.org rate-limits aggressively) and
fed in as a TSV of "url<TAB>json". Run once, review the diff, then delete.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from migrate_v3 import emit_backlog, emit_event

ROOT = Path(__file__).resolve().parents[1]


def load_snapshots(tsv: Path) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in tsv.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        url, _, payload = line.partition("\t")
        payload = payload.strip()
        if not payload:
            continue
        try:
            closest = json.loads(payload).get("archived_snapshots", {}).get("closest")
        except json.JSONDecodeError:
            continue
        if closest and closest.get("available"):
            # the API returns http://; the schema requires https://
            found[url] = closest["url"].replace("http://web.archive.org", "https://web.archive.org", 1)
    return found


def main() -> None:
    snapshots = load_snapshots(Path(sys.argv[1]))
    if not snapshots:
        sys.exit("no snapshots available; nothing to backfill")

    path = ROOT / "data/events.yaml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    patched = 0
    records = list(data["events"]) + list(data["validation_backlog"])
    for record in records:
        for source in record.get("sources", []):
            if source["url"] in snapshots and "archived_url" not in source:
                source["archived_url"] = snapshots[source["url"]]
                patched += 1

    lines: list[str] = [text.split("\nevents:\n")[0], "events:"]
    for event in data["events"]:
        emit_event(event, lines)
    lines.append("validation_backlog:")
    for item in data["validation_backlog"]:
        emit_backlog(item, lines)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(snapshots)} snapshots resolved; {patched} sources given an archived_url")


if __name__ == "__main__":
    main()
