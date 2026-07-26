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
OUTPUT_DIR = ROOT / "generated"

DATE_PATTERNS = {
    "year": re.compile(r"^\d{4}$"),
    "month": re.compile(r"^\d{4}-\d{2}$"),
    "day": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda error: list(error.path))
    if errors:
        for error in errors:
            location = ".".join(str(part) for part in error.absolute_path) or "root"
            print(f"SCHEMA {location}: {error.message}", file=sys.stderr)
        raise SystemExit(1)
    return data


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


def source_urls(event: dict) -> str:
    return " || ".join(source["url"] for source in event["sources"])


def write_outputs(data: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with (OUTPUT_DIR / "events.json").open("w", encoding="utf-8") as handle:
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

    backlog_fields = ["id", "working_claim", "reason", "target"]
    with (OUTPUT_DIR / "validation-backlog.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=backlog_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(data["validation_backlog"])


if __name__ == "__main__":
    dataset = load()
    validate_semantics(dataset)
    write_outputs(dataset)
    print(
        f"Validated {len(dataset['events'])} canonical events and "
        f"{len(dataset['validation_backlog'])} validation items; regenerated outputs."
    )
