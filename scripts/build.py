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


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


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


def validate_semantics(data: dict) -> None:
    events = data["events"]
    event_ids = [event["id"] for event in events]
    if len(event_ids) != len(set(event_ids)):
        duplicate = next(event_id for event_id in event_ids if event_ids.count(event_id) > 1)
        fail(f"duplicate event id: {duplicate}")

    backlog_ids = [item["id"] for item in data["validation_backlog"]]
    if len(backlog_ids) != len(set(backlog_ids)):
        duplicate = next(item_id for item_id in backlog_ids if backlog_ids.count(item_id) > 1)
        fail(f"duplicate validation backlog id: {duplicate}")

    known_event_ids = set(event_ids)
    for event in events:
        event_id = event["id"]
        precision = event["date_precision"]
        if not DATE_PATTERNS[precision].fullmatch(event["date"]):
            fail(f"{event_id}: date {event['date']!r} does not match precision {precision!r}")

        for source in event["sources"]:
            parsed = urlparse(source["url"])
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"{event_id}: invalid source URL: {source['url']}")

        for relation in event.get("related_events", []):
            if relation["id"] not in known_event_ids:
                fail(f"{event_id}: unknown related event: {relation['id']}")

    sorted_ids = [event["id"] for event in sorted(events, key=lambda item: (item["date"], item["id"]))]
    if event_ids != sorted_ids:
        fail("events must be sorted by date and id")


def source_urls(record: dict) -> str:
    return " || ".join(source["url"] for source in record.get("sources", []))


def write_outputs(data: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with (OUTPUT_DIR / "events.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    event_fields = [
        "id", "date", "date_precision", "vendor", "model", "models", "platform_owner", "platform_family",
        "platform_product", "experience", "event_type", "availability", "scope", "selectable", "confidence",
        "evidence_note", "caveat", "sources",
    ]
    with (OUTPUT_DIR / "events.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=event_fields, lineterminator="\n")
        writer.writeheader()
        for event in data["events"]:
            writer.writerow({
                "id": event["id"],
                "date": event["date"],
                "date_precision": event["date_precision"],
                "vendor": event["vendor"],
                "model": event["model"],
                "models": " | ".join(event.get("models", [])),
                "platform_owner": event["platform"]["owner"],
                "platform_family": event["platform"]["family"],
                "platform_product": event["platform"]["product"],
                "experience": event["platform"].get("experience") or "",
                "event_type": event["event"]["type"],
                "availability": event["event"]["availability"],
                "scope": event["event"].get("scope", ""),
                "selectable": "" if event["event"]["selectable"] is None else str(event["event"]["selectable"]).lower(),
                "confidence": event["confidence"],
                "evidence_note": event["evidence_note"],
                "caveat": event.get("caveat", ""),
                "sources": source_urls(event),
            })

    backlog_fields = ["id", "working_claim", "reason", "target", "sources"]
    with (OUTPUT_DIR / "validation-backlog.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=backlog_fields, lineterminator="\n")
        writer.writeheader()
        for item in data["validation_backlog"]:
            writer.writerow({
                "id": item["id"],
                "working_claim": item["working_claim"],
                "reason": item["reason"],
                "target": item["target"],
                "sources": source_urls(item),
            })


if __name__ == "__main__":
    models, platforms = validate_registries()
    dataset = load()
    validate_semantics(dataset)
    write_outputs(dataset)
    print(
        f"Validated {len(models['models'])} models and {len(platforms['surfaces'])} surfaces; "
        f"{len(dataset['events'])} canonical events and "
        f"{len(dataset['validation_backlog'])} validation items; regenerated outputs."
    )
