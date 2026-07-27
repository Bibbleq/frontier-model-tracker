#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "events.yaml"
SCHEMA_PATH = ROOT / "schema" / "events.schema.json"
MODELS_PATH = ROOT / "data" / "models.yaml"
MODELS_SCHEMA_PATH = ROOT / "schema" / "models.schema.json"
PLATFORMS_PATH = ROOT / "data" / "platforms.yaml"
PLATFORMS_SCHEMA_PATH = ROOT / "schema" / "platforms.schema.json"
OUTPUT_DIR = ROOT / "generated"

DATE_PATTERNS = {
    "year": re.compile(r"^\d{4}$"),
    "month": re.compile(r"^\d{4}-\d{2}$"),
    "day": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
}

# Lifecycle stages that represent a release progression, earliest first. Used
# to detect impossible orderings such as GA before preview on the same surface.
LIFECYCLE_ORDER = ["private_preview", "limited_preview", "public_preview", "ga"]

warnings: list[str] = []


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    if message not in warnings:
        warnings.append(message)


def load_validated(data_path: Path, schema_path: Path) -> dict:
    with data_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    with schema_path.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda error: list(error.path))
    if errors:
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "root"
            print(f"SCHEMA {data_path.name} {location}: {error.message}", file=sys.stderr)
        raise SystemExit(1)
    return data


def load() -> dict:
    return load_validated(DATA_PATH, SCHEMA_PATH)


def validate_registries() -> tuple[dict, dict]:
    """Load and internally check the model and surface registries."""
    models = load_validated(MODELS_PATH, MODELS_SCHEMA_PATH)
    platforms = load_validated(PLATFORMS_PATH, PLATFORMS_SCHEMA_PATH)

    model_ids = [entry["id"] for entry in models["models"]]
    if len(model_ids) != len(set(model_ids)):
        fail("duplicate model id in models.yaml")
    family_ids = {entry["id"] for entry in models["families"]}
    known_models = set(model_ids)
    for entry in models["models"]:
        if entry.get("family") and entry["family"] not in family_ids:
            fail(f"{entry['id']}: unknown family {entry['family']}")
        for link in ("supersedes", "superseded_by"):
            if entry.get(link) and entry[link] not in known_models:
                fail(f"{entry['id']}: {link} points at unknown model {entry[link]}")

    surface_ids = [entry["id"] for entry in platforms["surfaces"]]
    if len(surface_ids) != len(set(surface_ids)):
        fail("duplicate surface id in platforms.yaml")
    known_surfaces = set(surface_ids)
    for entry in platforms["surfaces"]:
        for link in ("renamed_from", "renamed_to"):
            if entry.get(link) and entry[link] not in known_surfaces:
                fail(f"{entry['id']}: {link} points at unknown surface {entry[link]}")
        if entry.get("vendor_baseline") and entry["counts_as"]:
            fail(f"{entry['id']}: a vendor baseline surface must not declare counts_as tiers")
    for entry in platforms["experiences"]:
        if entry["surface"] not in known_surfaces:
            fail(f"{entry['id']}: experience on unknown surface {entry['surface']}")

    return models, platforms


def rename_groups(platforms: dict) -> dict[str, str]:
    """Map each surface to a representative for its rename chain.

    A product that is renamed keeps its history: an experience declared on
    Copilot Studio is still the same experience on Power Virtual Agents.
    """
    parent = {entry["id"]: entry["id"] for entry in platforms["surfaces"]}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for entry in platforms["surfaces"]:
        for link in ("renamed_from", "renamed_to"):
            other = entry.get(link)
            if other and other in parent:
                a, b = find(entry["id"]), find(other)
                if a != b:
                    parent[a] = b
    return {sid: find(sid) for sid in parent}


def validate_semantics(data: dict, models: dict, platforms: dict) -> None:
    events = data["events"]
    event_ids = [event["id"] for event in events]
    if len(event_ids) != len(set(event_ids)):
        duplicate = next(eid for eid in event_ids if event_ids.count(eid) > 1)
        fail(f"duplicate event id: {duplicate}")

    backlog_ids = [item["id"] for item in data["validation_backlog"]]
    if len(backlog_ids) != len(set(backlog_ids)):
        duplicate = next(bid for bid in backlog_ids if backlog_ids.count(bid) > 1)
        fail(f"duplicate validation backlog id: {duplicate}")
    overlap = set(event_ids) & set(backlog_ids)
    if overlap:
        fail(f"id used by both an event and a backlog item: {sorted(overlap)[0]}")

    known_models = {entry["id"]: entry for entry in models["models"]}
    known_surfaces = {entry["id"]: entry for entry in platforms["surfaces"]}
    known_experiences = {entry["id"]: entry for entry in platforms["experiences"]}
    known_events = set(event_ids)
    groups = rename_groups(platforms)

    for event in events:
        eid = event["id"]
        date = event["date"]
        if not DATE_PATTERNS[date["precision"]].fullmatch(date["start"]):
            fail(f"{eid}: date.start {date['start']!r} does not match precision {date['precision']!r}")
        if date.get("end"):
            if not DATE_PATTERNS[date["precision"]].fullmatch(date["end"]):
                fail(f"{eid}: date.end {date['end']!r} does not match precision {date['precision']!r}")
            if date["end"] < date["start"]:
                fail(f"{eid}: date.end precedes date.start")

        if event["surface_id"] not in known_surfaces:
            fail(f"{eid}: unknown surface_id {event['surface_id']}")
        surface = known_surfaces[event["surface_id"]]

        for experience_id in event.get("experience_ids", []):
            if experience_id not in known_experiences:
                fail(f"{eid}: unknown experience_id {experience_id}")
            declared = known_experiences[experience_id]["surface"]
            if groups[declared] != groups[event["surface_id"]]:
                fail(f"{eid}: experience {experience_id} does not belong to surface {event['surface_id']}")

        for model_id in event["model_ids"]:
            if model_id not in known_models:
                fail(f"{eid}: unknown model_id {model_id}")

        applies = event.get("applies_to", {})
        for surface_id in applies.get("surfaces", []):
            if surface_id not in known_surfaces:
                fail(f"{eid}: applies_to names unknown surface {surface_id}")
        for experience_id in applies.get("experiences", []):
            if experience_id not in known_experiences:
                fail(f"{eid}: applies_to names unknown experience {experience_id}")
            declared = known_experiences[experience_id]["surface"]
            targets = applies.get("surfaces", [])
            if targets and all(groups[declared] != groups[t] for t in targets):
                fail(f"{eid}: applies_to experience {experience_id} is not on any named surface")

        for relation in event.get("relations", []):
            if relation["target"] not in known_events:
                fail(f"{eid}: relation points at unknown event {relation['target']}")
            if relation["target"] == eid:
                fail(f"{eid}: event relates to itself")

        if event["confidence"] == "confirmed" and not any(s["primary"] for s in event["sources"]):
            fail(f"{eid}: confidence 'confirmed' requires at least one primary source")

        detail = event.get("confidence_detail")
        if detail and event["confidence"] == "confirmed" and "supported" in detail.values():
            fail(f"{eid}: confidence 'confirmed' is stronger than its weakest confidence_detail")

        if event["kind"] == "availability" and event["exposure"] in ("selectable", "default"):
            if surface.get("vendor_baseline"):
                warn(f"{eid}: selectable exposure on a vendor baseline surface")

        # Warnings: not wrong, but worth a human look.
        if date["precision"] == "day" and date["start"].endswith("-01"):
            warn(f"{eid}: day precision on the first of the month may be an invented day")
        if event["confidence"] == "confirmed":
            types = {s.get("source_type") for s in event["sources"] if s["primary"]}
            if types == {"documentation"}:
                warn(f"{eid}: 'confirmed' rests only on current documentation, which rarely proves a historical first date")

    # Ordering and cross-event coherence.
    sorted_ids = [e["id"] for e in sorted(events, key=lambda i: (i["date"]["start"], i["id"]))]
    if event_ids != sorted_ids:
        fail("events must be sorted by date.start and id")

    check_semantic_duplicates(events)
    check_lifecycle_ordering(events)
    check_suspension_pairs(events)
    check_vendor_baseline(events, known_models, known_surfaces)


def _availability(events: list[dict]) -> list[dict]:
    return [e for e in events if e["kind"] == "availability"]


def check_semantic_duplicates(events: list[dict]) -> None:
    seen: dict[tuple, str] = {}
    for event in _availability(events):
        for model_id in event["model_ids"]:
            key = (event["surface_id"], model_id, event["lifecycle"], event["date"]["start"])
            if key in seen:
                fail(f"{event['id']}: duplicates {seen[key]} (same surface, model, lifecycle and date)")
            seen[key] = event["id"]


def check_lifecycle_ordering(events: list[dict]) -> None:
    first: dict[tuple, tuple[str, str]] = {}
    for event in _availability(events):
        if event["lifecycle"] not in LIFECYCLE_ORDER:
            continue
        for model_id in event["model_ids"]:
            key = (event["surface_id"], model_id)
            stage = LIFECYCLE_ORDER.index(event["lifecycle"])
            if key in first:
                prior_stage, prior_date, prior_id = first[key]
                if stage < prior_stage and event["date"]["start"] > prior_date:
                    fail(
                        f"{event['id']}: {event['lifecycle']} dated after {prior_id} "
                        f"reached a later stage on the same surface"
                    )
                if stage > prior_stage:
                    continue
            else:
                first[key] = (stage, event["date"]["start"], event["id"])


def check_suspension_pairs(events: list[dict]) -> None:
    suspended: dict[tuple, str] = {}
    for event in _availability(events):
        for model_id in event["model_ids"]:
            key = (event["surface_id"], model_id)
            if event["lifecycle"] == "suspended":
                suspended[key] = event["date"]["start"]
            elif event["lifecycle"] == "restored":
                if key not in suspended:
                    fail(f"{event['id']}: restoration without a prior suspension on the same surface")
                if event["date"]["start"] < suspended[key]:
                    fail(f"{event['id']}: restoration dated before its suspension")


def check_vendor_baseline(events: list[dict], models: dict, surfaces: dict) -> None:
    """A model cannot reach a Microsoft surface before its vendor released it."""
    baseline: dict[str, str] = {}
    for event in _availability(events):
        if surfaces[event["surface_id"]].get("vendor_baseline"):
            for model_id in event["model_ids"]:
                if model_id not in baseline or event["date"]["start"] < baseline[model_id]:
                    baseline[model_id] = event["date"]["start"]

    for event in _availability(events):
        if surfaces[event["surface_id"]].get("vendor_baseline"):
            continue
        for model_id in event["model_ids"]:
            if model_id in baseline and event["date"]["start"] < baseline[model_id]:
                fail(
                    f"{event['id']}: dated {event['date']['start']}, before {model_id} "
                    f"was released by its vendor on {baseline[model_id]}"
                )

    missing = {
        model_id
        for event in _availability(events)
        for model_id in event["model_ids"]
        if model_id not in baseline
    }
    for model_id in sorted(missing):
        warn(f"{model_id}: no vendor release event, so lag cannot be derived")


def source_urls(record: dict) -> str:
    return " || ".join(source["url"] for source in record.get("sources", []))


def write_outputs(data: dict, models: dict, platforms: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    model_names = {entry["id"]: entry["display_name"] for entry in models["models"]}
    surface_names = {entry["id"]: entry["display_name"] for entry in platforms["surfaces"]}
    experience_names = {entry["id"]: entry["display_name"] for entry in platforms["experiences"]}

    with (OUTPUT_DIR / "events.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    event_fields = [
        "id", "kind", "date_start", "date_precision", "date_end", "surface_id", "surface",
        "experiences", "model_ids", "models", "model_claim", "lifecycle", "exposure",
        "selectable", "confidence", "evidence_note", "caveat", "sources",
    ]
    with (OUTPUT_DIR / "events.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=event_fields, lineterminator="\n")
        writer.writeheader()
        for event in data["events"]:
            exposure = event.get("exposure")
            writer.writerow({
                "id": event["id"],
                "kind": event["kind"],
                "date_start": event["date"]["start"],
                "date_precision": event["date"]["precision"],
                "date_end": event["date"].get("end", ""),
                "surface_id": event["surface_id"],
                "surface": surface_names[event["surface_id"]],
                "experiences": " | ".join(experience_names[x] for x in event.get("experience_ids", [])),
                "model_ids": " | ".join(event["model_ids"]),
                "models": " | ".join(model_names[m] for m in event["model_ids"]),
                "model_claim": event.get("model_claim", ""),
                "lifecycle": event.get("lifecycle", ""),
                "exposure": exposure or "",
                # derived, never authored, so it cannot contradict exposure
                "selectable": "" if exposure is None else str(exposure in ("selectable", "default")).lower(),
                "confidence": event["confidence"],
                "evidence_note": event["evidence_note"],
                "caveat": event.get("caveat", ""),
                "sources": source_urls(event),
            })

    backlog_fields = ["id", "state", "working_claim", "reason", "target", "resolution", "sources"]
    with (OUTPUT_DIR / "validation-backlog.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=backlog_fields, lineterminator="\n")
        writer.writeheader()
        for item in data["validation_backlog"]:
            writer.writerow({
                "id": item["id"],
                "state": item["state"],
                "working_claim": item["working_claim"],
                "reason": item["reason"],
                "target": item["target"],
                "resolution": item.get("resolution", ""),
                "sources": source_urls(item),
            })


if __name__ == "__main__":
    registry_models, registry_platforms = validate_registries()
    dataset = load()
    validate_semantics(dataset, registry_models, registry_platforms)
    write_outputs(dataset, registry_models, registry_platforms)

    for message in warnings:
        print(f"WARNING: {message}", file=sys.stderr)
    print(
        f"Validated {len(registry_models['models'])} models and "
        f"{len(registry_platforms['surfaces'])} surfaces; "
        f"{len(dataset['events'])} canonical events and "
        f"{len(dataset['validation_backlog'])} validation items; "
        f"{len(warnings)} warning(s); regenerated outputs."
    )
