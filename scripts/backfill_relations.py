#!/usr/bin/env python3
"""One-shot P1 backfill of event relationships.

Adds the preview/GA and suspension/restoration links that were implicit in the
data, and repairs two relations that the v3 migration mapped onto the wrong
verb because v2 had only a generic "other".

Run once, review the diff, then delete.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from migrate_v3 import emit_backlog, emit_event

ROOT = Path(__file__).resolve().parents[1]

# preview -> the GA it previews, same surface and model
PREVIEWS_FOR = {
    "github-copilot-preview-codex-2021-06-29": "github-copilot-ga-2022-06-21",
    "m365-copilot-preview-gpt4-2023-03-16": "m365-copilot-ga-2023-11-01",
    "github-gpt5-preview-2025-08-07": "github-gpt5-ga-2025-09-09",
    "github-sonnet4-5-preview-2025-09-29": "github-sonnet4-5-ga-2025-10-13",
    "m365-analyst-frontier-2025-04": "m365-analyst-ga-2025-06-02",
    "openai-gpt5-6-preview-2026-06-26": "openai-gpt5-6-2026-07-09",
}

# restoration -> the suspension it reverses
RESTORES = {
    "anthropic-fable5-restoration-2026-07-01": "anthropic-fable5-suspension-2026-06-12",
    "github-fable5-restoration-2026-07-01": "github-fable5-suspension-2026-06-12",
}

# The v3 migration mapped v2's generic "other" onto announced_by. Two of those
# were wrong. Opus 5 on Foundry and on GitHub Copilot pointed at each other,
# forming a cycle: neither announced the other, the vendor release announced
# both. The EU/EFTA/UK apps setting does not announce anything either; it
# depends on the global subprocessor control.
REPLACE = {
    ("github-opus5-2026-07-24", "foundry-opus5-availability-2026-07-24"):
        {"type": "announced_by", "target": "anthropic-opus5-2026-07-24"},
    ("m365-anthropic-eu-apps-setting-2026-04-03", "m365-anthropic-subprocessor-2026-01-07"):
        {"type": "depends_on", "target": "m365-anthropic-subprocessor-2026-01-07"},
}

# Drop entirely: the reverse half of the Opus 5 cycle.
DROP = {("foundry-opus5-availability-2026-07-24", "github-opus5-2026-07-24")}


def main() -> None:
    path = ROOT / "data/events.yaml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    added = repaired = dropped = 0
    for event in data["events"]:
        eid = event["id"]
        relations = event.get("relations", [])

        kept = []
        for relation in relations:
            key = (eid, relation["target"])
            if key in DROP:
                dropped += 1
                continue
            if key in REPLACE:
                kept.append(REPLACE[key])
                repaired += 1
                continue
            kept.append(relation)
        relations = kept

        for mapping, verb in ((PREVIEWS_FOR, "previews_for"), (RESTORES, "restores")):
            if eid in mapping:
                target = mapping[eid]
                if not any(r["type"] == verb and r["target"] == target for r in relations):
                    relations.append({"type": verb, "target": target})
                    added += 1

        if relations:
            event["relations"] = relations
        else:
            event.pop("relations", None)

    lines: list[str] = [text.split("\nevents:\n")[0], "events:"]
    for event in data["events"]:
        emit_event(event, lines)
    lines.append("validation_backlog:")
    for item in data["validation_backlog"]:
        emit_backlog(item, lines)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"relations: {added} added, {repaired} repaired, {dropped} dropped")


if __name__ == "__main__":
    main()
