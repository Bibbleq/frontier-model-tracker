#!/usr/bin/env python3
from __future__ import annotations

import collections
import csv
import json
import re
import sys
from calendar import monthrange
from datetime import date as date_cls
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

warnings: list[dict] = []


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(code: str, subject: str, message: str) -> None:
    """Record a non-fatal finding. Warnings are a work queue, not noise, so
    they are emitted as structured data for the dashboard as well as text."""
    entry = {"code": code, "subject": subject, "message": message}
    if entry not in warnings:
        warnings.append(entry)


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


def validate_registry_semantics(models: dict, platforms: dict) -> None:
    """Check graph and identity rules that JSON Schema cannot express."""
    model_ids = [entry["id"] for entry in models["models"]]
    if len(model_ids) != len(set(model_ids)):
        fail("duplicate model id in models.yaml")
    family_ids_list = [entry["id"] for entry in models["families"]]
    if len(family_ids_list) != len(set(family_ids_list)):
        fail("duplicate family id in models.yaml")
    family_ids = set(family_ids_list)
    known_models = set(model_ids)
    names: dict[str, str] = {}
    for entry in models["models"]:
        if entry.get("family") and entry["family"] not in family_ids:
            fail(f"{entry['id']}: unknown family {entry['family']}")
        for name in [entry["display_name"], *entry.get("aliases", [])]:
            key = name.casefold()
            if key in names and names[key] != entry["id"]:
                fail(f"{entry['id']}: name or alias {name!r} is already used by {names[key]}")
            names[key] = entry["id"]
        for link in ("supersedes", "superseded_by"):
            if entry.get(link) and entry[link] not in known_models:
                fail(f"{entry['id']}: {link} points at unknown model {entry[link]}")

    model_by_id = {entry["id"]: entry for entry in models["models"]}
    for entry in models["models"]:
        if entry.get("supersedes"):
            target = model_by_id[entry["supersedes"]]
            if target.get("superseded_by") != entry["id"]:
                fail(f"{entry['id']}: supersedes link is not reciprocated by {target['id']}")
        if entry.get("superseded_by"):
            target = model_by_id[entry["superseded_by"]]
            if target.get("supersedes") != entry["id"]:
                fail(f"{entry['id']}: superseded_by link is not reciprocated by {target['id']}")

    def reject_cycles(graph: dict[str, set[str]], label: str) -> None:
        colour: dict[str, int] = {}
        stack: list[str] = []

        def visit(node: str) -> None:
            colour[node] = 1
            stack.append(node)
            for nxt in graph.get(node, set()):
                if colour.get(nxt) == 1:
                    cycle = " -> ".join(stack[stack.index(nxt):] + [nxt])
                    fail(f"{label} cycle: {cycle}")
                if colour.get(nxt, 0) == 0:
                    visit(nxt)
            stack.pop()
            colour[node] = 2

        for node in graph:
            if colour.get(node, 0) == 0:
                visit(node)

    reject_cycles(
        {entry["id"]: {entry["supersedes"]} for entry in models["models"] if entry.get("supersedes")},
        "model succession",
    )

    surface_ids = [entry["id"] for entry in platforms["surfaces"]]
    if len(surface_ids) != len(set(surface_ids)):
        fail("duplicate surface id in platforms.yaml")
    known_surfaces = set(surface_ids)
    surface_by_id = {entry["id"]: entry for entry in platforms["surfaces"]}
    rename_graph: dict[str, set[str]] = {surface_id: set() for surface_id in surface_ids}
    for entry in platforms["surfaces"]:
        for link in ("renamed_from", "renamed_to"):
            if entry.get(link) and entry[link] not in known_surfaces:
                fail(f"{entry['id']}: {link} points at unknown surface {entry[link]}")
        if entry.get("renamed_to"):
            rename_graph[entry["id"]].add(entry["renamed_to"])
        if entry.get("renamed_from"):
            rename_graph[entry["renamed_from"]].add(entry["id"])
        if entry.get("vendor_baseline") and entry["counts_as"]:
            fail(f"{entry['id']}: a vendor baseline surface must not declare counts_as tiers")

    # Checked over the completed graph. Doing this while the graph is still
    # being built makes the result depend on declaration order: an edge
    # declared only as `renamed_from` on a later entry is invisible when the
    # earlier entry is processed, so a mismatch in that direction is missed.
    for source_id, targets in rename_graph.items():
        source = surface_by_id[source_id]
        for target_id in targets:
            target = surface_by_id[target_id]
            if source.get("lineage") and target.get("lineage") and source["lineage"] != target["lineage"]:
                fail(f"{source_id}: rename target {target_id} belongs to a different lineage")

    reject_cycles(rename_graph, "surface rename")

    experience_ids = [entry["id"] for entry in platforms["experiences"]]
    if len(experience_ids) != len(set(experience_ids)):
        fail("duplicate experience id in platforms.yaml")
    for entry in platforms["experiences"]:
        if entry["surface"] not in known_surfaces:
            fail(f"{entry['id']}: experience on unknown surface {entry['surface']}")


def validate_registries() -> tuple[dict, dict]:
    """Load and internally check the model and surface registries."""
    models = load_validated(MODELS_PATH, MODELS_SCHEMA_PATH)
    platforms = load_validated(PLATFORMS_PATH, PLATFORMS_SCHEMA_PATH)
    validate_registry_semantics(models, platforms)

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
                warn("selectable_on_vendor_surface", eid, "selectable exposure on a vendor baseline surface")

        # Living documentation is edited in place, so a citation that reads
        # correctly today may not attest the same claim later.
        for source in event["sources"]:
            if source.get("source_type") in ("documentation", "release_notes") and not source.get("archived_url"):
                warn("missing_archive", eid, f"documentation source has no archived_url and may be edited in place: {source['url']}")

        # Warnings: not wrong, but worth a human look.
        if date["precision"] == "day" and date["start"].endswith("-01"):
            warn("suspicious_day_precision", eid, "day precision on the first of the month may be an invented day")
        if event["confidence"] == "confirmed":
            primary = [s for s in event["sources"] if s["primary"]]
            types = {s.get("source_type") for s in primary}
            # A verbatim quote means someone has checked that the page actually
            # attests the date, rather than merely proving current support.
            attested = any(s.get("quote") and "date" in s.get("supports", ["date"]) for s in primary)
            if types == {"documentation"} and not attested:
                warn("unquoted_documentation", eid, "'confirmed' rests only on current documentation with no quoted attestation, which rarely proves a historical first date")

    for item in data["validation_backlog"]:
        for model_id in item.get("model_ids", []):
            if model_id not in known_models:
                fail(f"{item['id']}: backlog names unknown model {model_id}")
        for surface_id in item.get("surface_ids", []):
            if surface_id not in known_surfaces:
                fail(f"{item['id']}: backlog names unknown surface {surface_id}")
        if item.get("promoted_to") and item["promoted_to"] not in known_events:
            fail(f"{item['id']}: promoted_to points at unknown event {item['promoted_to']}")
        if item["state"] == "open" and not item.get("surface_ids"):
            warn("backlog_without_surface", item["id"], "open item names no surface, so it cannot suppress a lag answer")

    # Ordering and cross-event coherence.
    sorted_ids = [e["id"] for e in sorted(events, key=lambda i: (i["date"]["start"], i["id"]))]
    if event_ids != sorted_ids:
        fail("events must be sorted by date.start and id")

    check_semantic_duplicates(events)
    check_lifecycle_ordering(events)
    check_suspension_pairs(events)
    check_vendor_baseline(events, known_models, known_surfaces)
    check_relations(events)


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
    latest: dict[tuple, tuple[int, str, str]] = {}
    for event in _availability(events):
        if event["lifecycle"] not in LIFECYCLE_ORDER:
            continue
        for model_id in event["model_ids"]:
            key = (event["surface_id"], model_id)
            stage = LIFECYCLE_ORDER.index(event["lifecycle"])
            if key in latest:
                prior_stage, prior_date, prior_id = latest[key]
                if stage < prior_stage and event["date"]["start"] > prior_date:
                    fail(
                        f"{event['id']}: {event['lifecycle']} dated after {prior_id} "
                        f"reached a later stage on the same surface"
                    )
            if key not in latest or stage >= latest[key][0]:
                latest[key] = (stage, event["date"]["start"], event["id"])


def check_suspension_pairs(events: list[dict]) -> None:
    """A restoration must reverse a suspension that could have preceded it.

    Dates are compared as intervals rather than as strings, because the project
    records the precision the evidence supports. A suspension and a restoration
    both known only to the same month, or both recorded on the same day, are
    legitimate: a short outage is real, and padding either date to force a
    strict ordering would invent precision the sources do not have. Only a
    restoration that must have ended before its suspension began is impossible.

    Suspensions are collected first so that same-date pairs are not rejected
    because "restored" happens to sort before "suspended" within a date.
    """
    suspensions: dict[tuple, list[dict]] = {}
    for event in _availability(events):
        if event["lifecycle"] != "suspended":
            continue
        for model_id in event["model_ids"]:
            suspensions.setdefault((event["surface_id"], model_id), []).append(event)

    for event in _availability(events):
        if event["lifecycle"] != "restored":
            continue
        _, restored_end = date_interval(event["date"])
        for model_id in event["model_ids"]:
            candidates = suspensions.get((event["surface_id"], model_id), [])
            if not candidates:
                fail(f"{event['id']}: restoration without a suspension on the same surface")
            if all(restored_end < date_interval(s["date"])[0] for s in candidates):
                earliest = min(candidates, key=lambda s: date_interval(s["date"])[0])
                fail(
                    f"{event['id']}: restoration ends before its suspension "
                    f"({earliest['id']}) could have begun"
                )


# Each relation implies an ordering between the two events. "target_earlier"
# means the target must not be dated after this event, and vice versa.
RELATION_ORDER = {
    "supersedes": "target_earlier",
    "announced_by": "target_earlier",
    "part_of": "target_earlier",
    "depends_on": "target_earlier",
    "restores": "target_strictly_earlier",
    "previews_for": "target_later",
}


def check_relations(events: list[dict]) -> None:
    """Relations must be acyclic and consistent with the dates they imply."""
    by_id = {event["id"]: event for event in events}

    for event in events:
        for relation in event.get("relations", []):
            target = by_id[relation["target"]]
            here, there = event["date"]["start"], target["date"]["start"]
            rule = RELATION_ORDER[relation["type"]]
            if rule == "target_earlier" and there > here:
                fail(f"{event['id']}: {relation['type']} target {target['id']} is dated later ({there} > {here})")
            if rule == "target_strictly_earlier" and there >= here:
                fail(f"{event['id']}: {relation['type']} target {target['id']} must be strictly earlier ({there} >= {here})")
            if rule == "target_later" and there < here:
                fail(f"{event['id']}: {relation['type']} target {target['id']} is dated earlier ({there} < {here})")

    # Cycle detection over the whole relation graph. A cycle means the dataset
    # asserts two events each precede the other, which cannot be true and makes
    # any derived traversal non-terminating.
    colour: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        colour[node] = 1
        stack.append(node)
        for relation in by_id[node].get("relations", []):
            nxt = relation["target"]
            if colour.get(nxt) == 1:
                cycle = " -> ".join(stack[stack.index(nxt):] + [nxt])
                fail(f"relation cycle: {cycle}")
            if colour.get(nxt, 0) == 0:
                visit(nxt)
        stack.pop()
        colour[node] = 2

    for event in events:
        if colour.get(event["id"], 0) == 0:
            visit(event["id"])


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
        warn("no_vendor_baseline", model_id, "no vendor release event, so lag cannot be derived")


def source_urls(record: dict) -> str:
    return " || ".join(source["url"] for source in record.get("sources", []))


# --------------------------------------------------------------------------
# Derived lag. Never stored in canonical data; recomputed on every build.
# The rules are documented in docs/methodology.md.
# --------------------------------------------------------------------------
TIERS = ["microsoft", "copilot", "m365", "studio", "github_copilot", "foundry"]
MEASURES = {
    # "how soon could anyone use it here at all", including underlying and
    # specialist use that a user cannot select
    "any_exposure": {"underlying", "specialist", "catalogue", "selectable", "default"},
    # "how soon could a user actually choose it here"
    "selectable_or_default": {"selectable", "default"},
}


def date_interval(date: dict) -> tuple[date_cls, date_cls]:
    """Widen a partial date into the interval of days it could mean."""
    start, precision = date["start"], date["precision"]
    if precision == "day":
        low = date_cls.fromisoformat(start)
        high = low
    elif precision == "month":
        year, month = (int(part) for part in start.split("-"))
        low = date_cls(year, month, 1)
        high = date_cls(year, month, monthrange(year, month)[1])
    else:
        year = int(start)
        low = date_cls(year, 1, 1)
        high = date_cls(year, 12, 31)

    if date.get("end"):
        high = date_interval({"start": date["end"], "precision": precision})[1]
    return low, high


def derive_lag(data: dict, models: dict, platforms: dict) -> list[dict]:
    events = [e for e in data["events"] if e["kind"] == "availability"]
    surfaces = {entry["id"]: entry for entry in platforms["surfaces"]}
    model_names = {entry["id"]: entry for entry in models["models"]}

    # Open research questions suppress a lag answer: an unresearched gap must
    # not render as evidence that a model never arrived.
    open_questions: set[tuple[str, str]] = set()
    for item in data["validation_backlog"]:
        if item["state"] not in ("open", "blocked"):
            continue
        for surface_id in item.get("surface_ids", []):
            for model_id in item.get("model_ids", []):
                for tier in surfaces[surface_id]["counts_as"]:
                    open_questions.add((model_id, tier))

    baseline: dict[str, dict] = {}
    for event in events:
        if not surfaces[event["surface_id"]].get("vendor_baseline"):
            continue
        low, _ = date_interval(event["date"])
        for model_id in event["model_ids"]:
            if model_id not in baseline or low < baseline[model_id]["low"]:
                baseline[model_id] = {"low": low, "high": date_interval(event["date"])[1],
                                      "event": event["id"], "lifecycle": event["lifecycle"]}

    rows: list[dict] = []
    for model_id in sorted(model_names):
        base = baseline.get(model_id)
        for tier in TIERS:
            for measure, exposures in MEASURES.items():
                candidates = [
                    e for e in events
                    if model_id in e["model_ids"]
                    and tier in surfaces[e["surface_id"]]["counts_as"]
                    and e["exposure"] in exposures
                ]
                row = {
                    "model_id": model_id,
                    "model": model_names[model_id]["display_name"],
                    "vendor": model_names[model_id]["vendor"],
                    "tier": tier,
                    "measure": measure,
                    "baseline_event": base["event"] if base else "",
                    "baseline_date": base["low"].isoformat() if base else "",
                    "baseline_lifecycle": base["lifecycle"] if base else "",
                    "first_event": "", "first_date": "", "first_surface": "",
                    "first_exposure": "", "first_lifecycle": "",
                    "lag_days_min": "", "lag_days_max": "", "certainty": "",
                }
                if not candidates:
                    if (model_id, tier) in open_questions:
                        row["certainty"] = "unknown_open_research"
                    elif base:
                        row["certainty"] = "not_recorded"
                    else:
                        row["certainty"] = "unknown_no_baseline"
                    rows.append(row)
                    continue

                first = min(candidates, key=lambda e: (date_interval(e["date"])[0], e["id"]))
                low, high = date_interval(first["date"])
                row.update({
                    "first_event": first["id"],
                    "first_date": first["date"]["start"],
                    "first_surface": first["surface_id"],
                    "first_exposure": first["exposure"],
                    "first_lifecycle": first["lifecycle"],
                })
                if not base:
                    row["certainty"] = "unknown_no_baseline"
                else:
                    lag_min = (low - base["high"]).days
                    lag_max = (high - base["low"]).days
                    row["lag_days_min"] = lag_min
                    row["lag_days_max"] = lag_max
                    row["certainty"] = "exact" if lag_min == lag_max else "range"
                rows.append(row)
    return rows


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
        "selectable", "confidence", "confidence_detail", "evidence_note", "caveat",
        "source_types", "sources",
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
                "confidence_detail": " | ".join(
                    f"{part}={value}" for part, value in sorted(event.get("confidence_detail", {}).items())
                ),
                "evidence_note": event["evidence_note"],
                "caveat": event.get("caveat", ""),
                "source_types": " | ".join(
                    dict.fromkeys(s.get("source_type", "other") for s in event["sources"])
                ),
                "sources": source_urls(event),
            })

    # Registry exports, so a consumer can resolve ids and tiers without
    # parsing YAML or hardcoding the vocabulary.
    model_fields = ["id", "display_name", "vendor", "family", "aliases", "supersedes", "superseded_by", "event_count"]
    model_use = collections.Counter(m for event in data["events"] for m in event["model_ids"])
    with (OUTPUT_DIR / "models.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=model_fields, lineterminator="\n")
        writer.writeheader()
        for entry in models["models"]:
            writer.writerow({
                "id": entry["id"],
                "display_name": entry["display_name"],
                "vendor": entry["vendor"],
                "family": entry.get("family", ""),
                "aliases": " | ".join(entry.get("aliases", [])),
                "supersedes": entry.get("supersedes", ""),
                "superseded_by": entry.get("superseded_by", ""),
                "event_count": model_use.get(entry["id"], 0),
            })

    surface_fields = ["id", "display_name", "owner", "family", "lineage", "vendor_baseline",
                      "counts_as", "renamed_from", "renamed_to", "renamed_on", "event_count"]
    surface_use = collections.Counter(event["surface_id"] for event in data["events"])
    with (OUTPUT_DIR / "surfaces.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=surface_fields, lineterminator="\n")
        writer.writeheader()
        for entry in platforms["surfaces"]:
            writer.writerow({
                "id": entry["id"],
                "display_name": entry["display_name"],
                "owner": entry["owner"],
                "family": entry.get("family", ""),
                "lineage": entry.get("lineage", ""),
                "vendor_baseline": str(entry.get("vendor_baseline", False)).lower(),
                "counts_as": " | ".join(entry["counts_as"]),
                "renamed_from": entry.get("renamed_from", ""),
                "renamed_to": entry.get("renamed_to", ""),
                "renamed_on": entry.get("renamed_on", ""),
                "event_count": surface_use.get(entry["id"], 0),
            })

    # A single document the editorial dashboard can read. Deliberately carries
    # no timestamp: generated output must stay byte-identical on rebuild so the
    # CI check that generated files are committed keeps working.
    lag_rows = derive_lag(data, models, platforms)
    status = {
        "totals": {
            "events": len(data["events"]),
            "backlog": len(data["validation_backlog"]),
            "sources": sum(len(e["sources"]) for e in data["events"])
            + sum(len(b.get("sources", [])) for b in data["validation_backlog"]),
            "models": len(models["models"]),
            "surfaces": len(platforms["surfaces"]),
            "confirmed": sum(1 for e in data["events"] if e["confidence"] == "confirmed"),
            "supported": sum(1 for e in data["events"] if e["confidence"] == "supported"),
        },
        "kinds": dict(sorted(collections.Counter(e["kind"] for e in data["events"]).items())),
        "backlog_states": dict(sorted(collections.Counter(b["state"] for b in data["validation_backlog"]).items())),
        "warnings": sorted(warnings, key=lambda w: (w["code"], w["subject"])),
        "warning_counts": dict(sorted(collections.Counter(w["code"] for w in warnings).items())),
        "coverage": {
            "models_without_events": sorted(
                entry["id"] for entry in models["models"] if not model_use.get(entry["id"])
            ),
            "surfaces_without_events": sorted(
                entry["id"] for entry in platforms["surfaces"] if not surface_use.get(entry["id"])
            ),
        },
        "lag_certainty": dict(sorted(collections.Counter(r["certainty"] for r in lag_rows).items())),
    }
    with (OUTPUT_DIR / "status.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(status, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    lag_fields = [
        "model_id", "model", "vendor", "tier", "measure",
        "baseline_event", "baseline_date", "baseline_lifecycle",
        "first_event", "first_date", "first_surface", "first_exposure", "first_lifecycle",
        "lag_days_min", "lag_days_max", "certainty",
    ]
    with (OUTPUT_DIR / "lag.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=lag_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(lag_rows)

    backlog_fields = [
        "id", "state", "model_ids", "models", "surface_ids", "working_claim",
        "reason", "target", "resolution", "resolved_on", "promoted_to", "sources",
    ]
    with (OUTPUT_DIR / "validation-backlog.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=backlog_fields, lineterminator="\n")
        writer.writeheader()
        for item in data["validation_backlog"]:
            writer.writerow({
                "id": item["id"],
                "state": item["state"],
                "model_ids": " | ".join(item.get("model_ids", [])),
                "models": " | ".join(model_names[m] for m in item.get("model_ids", [])),
                "surface_ids": " | ".join(item.get("surface_ids", [])),
                "working_claim": item["working_claim"],
                "reason": item["reason"],
                "target": item["target"],
                "resolution": item.get("resolution", ""),
                "resolved_on": item.get("resolved_on", ""),
                "promoted_to": item.get("promoted_to", ""),
                "sources": source_urls(item),
            })


if __name__ == "__main__":
    registry_models, registry_platforms = validate_registries()
    dataset = load()
    validate_semantics(dataset, registry_models, registry_platforms)
    write_outputs(dataset, registry_models, registry_platforms)

    for entry in sorted(warnings, key=lambda w: (w["code"], w["subject"])):
        print(f"WARNING [{entry['code']}] {entry['subject']}: {entry['message']}", file=sys.stderr)
    print(
        f"Validated {len(registry_models['models'])} models and "
        f"{len(registry_platforms['surfaces'])} surfaces; "
        f"{len(dataset['events'])} canonical events and "
        f"{len(dataset['validation_backlog'])} validation items; "
        f"{len(warnings)} warning(s); regenerated outputs."
    )
