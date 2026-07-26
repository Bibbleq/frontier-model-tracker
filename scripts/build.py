#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "events.yaml"
SCHEMA_PATH = ROOT / "schema" / "events.schema.json"
OUTPUT_DIR = ROOT / "generated"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load() -> dict:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)

    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
    if errors:
        for error in errors:
            location = ".".join(str(p) for p in error.absolute_path) or "root"
            print(f"SCHEMA {location}: {error.message}", file=sys.stderr)
        raise SystemExit(1)
    return data


def validate_semantics(data: dict) -> None:
    ids: set[str] = set()
    for event in data["events"]:
        event_id = event["id"]
        if event_id in ids:
            fail(f"duplicate event id: {event_id}")
        ids.add(event_id)

        for source in event["sources"]:
            parsed = urlparse(source["url"])
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"{event_id}: invalid source URL: {source['url']}")


def write_outputs(data: dict) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    events = sorted(data["events"], key=lambda item: (item["date"], item["id"]))

    with (OUTPUT_DIR / "events.json").open("w", encoding="utf-8") as handle:
        json.dump({**data, "events": events}, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    fields = ["id", "date", "vendor", "model", "platform_owner", "platform_product", "experience", "event_type", "status", "selectable", "confidence", "notes", "sources"]
    with (OUTPUT_DIR / "events.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for event in events:
            writer.writerow({
                "id": event["id"],
                "date": event["date"],
                "vendor": event["vendor"],
                "model": event["model"],
                "platform_owner": event["platform"]["owner"],
                "platform_product": event["platform"]["product"],
                "experience": event["platform"].get("experience") or "",
                "event_type": event["event_type"],
                "status": event["status"],
                "selectable": str(event["selectable"]).lower(),
                "confidence": event["confidence"],
                "notes": event.get("notes", ""),
                "sources": " | ".join(source["url"] for source in event["sources"]),
            })


if __name__ == "__main__":
    dataset = load()
    validate_semantics(dataset)
    write_outputs(dataset)
    print(f"Validated {len(dataset['events'])} events and regenerated outputs.")
