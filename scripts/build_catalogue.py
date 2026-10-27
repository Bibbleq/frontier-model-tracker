#!/usr/bin/env python3
"""Build the derived catalogue by replaying the observation chain.

The catalogue watcher commits three machine-written folders: `checkpoints/`
(full state, a seed per region and then one a month), `observations/` (one
file per run that saw a change) and `status/` (a status report and the region
reference data). This script replays each region's chain forward from its seed
checkpoint, proves at every file that it reached the state the watcher saw, and
writes the catalogue product the Pages site serves:

  catalogue/intervals.json  derived here: presence windows per region, model
                            and deployment type, and state segments (stage,
                            deprecation dates, capabilities) per region and model
  catalogue/regions.json    the watcher's regions export, copied byte for byte
  catalogue/status.json     the watcher's status export, copied byte for byte
  catalogue/manifest.json   versions, checksums and the licence

The proof is the snapshot hash every file carries. The watcher hashes its
snapshot as

  fingerprint     = sha256( json.dumps(watched, sort_keys=True, separators=(",", ":")) )
  snapshot_sha256 = sha256( json.dumps([[model_key, fingerprint], ...] sorted,
                                       separators=(",", ":")) )

so a replay that lands on the same watched fields for the same keys lands on
the same hash, without the private snapshot ever being published. A chain that
does not replay cleanly fails the build: the map is never drawn from a record
that does not add up.

Like the dataset build, the output carries no build timestamp; the same inputs
give the same bytes. The output is published, not committed (see
docs/catalogue-contract.md and the Pages workflow).
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

try:
    from scripts.build import ATTRIBUTION, BASE_URL
except ModuleNotFoundError:  # run as a script: scripts/ is on sys.path, the package is not
    from build import ATTRIBUTION, BASE_URL

CATALOGUE_CONTRACT_VERSION = 2
INTERVALS_SCHEMA_VERSION = 1

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "generated" / "catalogue"
DOCUMENTATION = "https://github.com/Bibbleq/frontier-model-tracker/blob/main/docs/catalogue-contract.md"

ARRIVAL_KINDS = {"first_seen_present", "region_added", "alias_version_added", "returned"}
FIELD_KINDS = {
    "lifecycle_changed", "deprecation_set", "deprecation_moved", "default_version_changed",
    "fields_changed", "deployment_type_added", "deployment_type_removed",
}
# The watched fields a state segment carries. Capabilities are here, not on the
# model, because the same key lists different capabilities in different regions
# (an `area` flag, `instant`). SKU dates live on the cell rows.
STATE_FIELDS = (
    "lifecycle_status", "lifecycle_portal", "deprecation_inference",
    "deprecation_fine_tune", "is_default_version", "capabilities",
)

PUBLISHED_FILES = {
    "catalogue/intervals.json": (
        "derived",
        "Presence windows per region, model and deployment type, and state segments (stage, "
        "deprecation dates, capabilities) per region and model, replayed from observations/ and checkpoints/",
    ),
    "catalogue/regions.json": (
        "export",
        "Reference data: every polled region with display name, geography and coordinates; "
        "never evidence",
    ),
    "catalogue/status.json": (
        "export",
        "Status report: the watcher's last run per region; never evidence that a model was or "
        "was not available",
    ),
}
EXPORTS = {"catalogue/regions.json": "status/regions.json", "catalogue/status.json": "status/arm.json"}


class ChainError(Exception):
    """The committed record does not replay: a file is malformed or the chain does not add up."""


# -- hashing, exactly the watcher's formulas -------------------------------------------

def fingerprint(watched: dict) -> str:
    return hashlib.sha256(
        json.dumps(watched, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def snapshot_hash(pairs: list[tuple[str, str]]) -> str:
    body = json.dumps([[k, f] for k, f in sorted(pairs)], separators=(",", ":"))
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def file_stamp(timestamp: str) -> str:
    """`2026-10-27T19:30:00Z` -> `2026-10-27T19-30-00Z`, the contract's file-name form."""
    return timestamp.replace(":", "-")


# -- replay state -----------------------------------------------------------------------

@dataclass
class Cell:
    deployment_type: str
    seen_after: str | None          # last run known without it; None when present at the seed
    seen_by: str                    # first run that saw it
    sku_deprecation_date: str | None = None


@dataclass
class Entry:
    model_key: str
    watched: dict
    cells: dict[str, Cell] = field(default_factory=dict)
    absent_since: str | None = None  # first run whose listing lacked it, before a confirmed absence


@dataclass
class RegionReplay:
    region: str
    source: str
    observed_from: str = ""
    first_observed_at: str = ""
    last_observed_at: str = ""
    files: int = 0
    checkpoints: int = 0
    entries: dict[str, Entry] = field(default_factory=dict)
    cell_rows: list[dict] = field(default_factory=list)
    state_rows: list[dict] = field(default_factory=list)
    open_state: dict[str, dict] = field(default_factory=dict)
    models: dict[str, dict] = field(default_factory=dict)

    # -- states and cells

    def state(self, key: str, watched: dict, after: str | None, by: str, mapping: dict) -> None:
        values = {name: copy.deepcopy(watched.get(name)) for name in STATE_FIELDS}
        values["capabilities"] = values["capabilities"] or {}
        current = self.open_state.get(key)
        if current is not None and all(current[name] == values[name] for name in STATE_FIELDS):
            return
        status = values["lifecycle_status"]
        row = {
            "region": self.region,
            "model_key": key,
            "from": {"after": after, "by": by},
            **values,
            "dataset_lifecycle": mapping.get(status, {}).get("dataset_lifecycle") if status else None,
        }
        self.state_rows.append(row)
        self.open_state[key] = row

    def note_model(self, key: str, watched: dict) -> None:
        self.models[key] = watched

    def open_cell(self, entry: Entry, cell: dict | None, deployment_type: str,
                  after: str | None, by: str, watched: dict) -> None:
        if deployment_type in entry.cells:
            return
        c = Cell(deployment_type, after, by, sku_deprecation_date=sku_date(watched, deployment_type))
        if cell is not None:
            absorb(c, cell)
        entry.cells[deployment_type] = c

    def close_cell(self, key: str, c: Cell, last_seen: str, absent_by: str,
                   confirmed_at: str | None) -> None:
        self.cell_rows.append(cell_row(self.region, key, c, {
            "last_seen": last_seen, "absent_by": absent_by, "confirmed_at": confirmed_at,
        }))


def sku_date(watched: dict, deployment_type: str) -> str | None:
    for sku in watched.get("skus") or []:
        if sku.get("name") == deployment_type:
            return sku.get("deprecation_date")
    return None


def sku_names(watched: dict | None) -> list[str]:
    """The deployment types a watched entry lists; an entry with no SKUs is the single cell `none`."""
    names = [s["name"] for s in (watched or {}).get("skus") or [] if s.get("name")]
    return sorted(set(names)) or ["none"]


def absorb(c: Cell, cell: dict) -> None:
    """Take a committed cell's SKU deprecation date. Capacity, which the seed checkpoints still
    carry as null, is the watcher's subscription quota, not a fact about the region, and is
    never published."""
    if "sku_deprecation_date" in cell:
        c.sku_deprecation_date = cell["sku_deprecation_date"]


def cell_row(region: str, key: str, c: Cell, until: dict | None) -> dict:
    return {
        "region": region,
        "model_key": key,
        "deployment_type": c.deployment_type,
        "seen_from": {"after": c.seen_after, "by": c.seen_by},
        "seen_until": until,
        "sku_deprecation_date": c.sku_deprecation_date,
    }


# -- loading and validating --------------------------------------------------------------

def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ChainError(f"{path.as_posix()}: unreadable JSON ({exc})") from exc


def validator(root: Path, name: str) -> Draft202012Validator:
    return Draft202012Validator(load_json(root / "schema" / name))


def check(validator_: Draft202012Validator, document: dict, label: str) -> None:
    errors = sorted(validator_.iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        first = errors[0]
        where = "/".join(str(p) for p in first.absolute_path) or "(root)"
        raise ChainError(f"{label}: schema violation at {where}: {first.message}")


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def collect(root: Path) -> dict[tuple[str, str], dict[str, list[Path]]]:
    """(source, region) -> {"checkpoints": [...], "observations": [...]} from the folder layout."""
    chains: dict[tuple[str, str], dict[str, list[Path]]] = {}
    for path in sorted((root / "checkpoints").glob("*/*/*.json")):
        source, region = path.parts[-3], path.parts[-2]
        chains.setdefault((source, region), {"checkpoints": [], "observations": []})["checkpoints"].append(path)
    for path in sorted((root / "observations").glob("*/*/*/*/*.json")):
        source, region = path.parts[-5], path.parts[-4]
        chains.setdefault((source, region), {"checkpoints": [], "observations": []})["observations"].append(path)
    return chains


def check_placement(root: Path, path: Path, doc: dict, folder: str) -> None:
    rel = relative(root, path)
    parts = rel.split("/")
    if doc["source"] != parts[1] or doc["region"] != parts[2]:
        raise ChainError(f"{rel}: source/region {doc['source']}/{doc['region']} do not match the path")
    if path.stem != file_stamp(doc["observed_at"]):
        raise ChainError(f"{rel}: file name does not match observed_at {doc['observed_at']}")
    if folder == "observations" and (parts[3], parts[4]) != (doc["observed_at"][0:4], doc["observed_at"][5:7]):
        raise ChainError(f"{rel}: year/month folder does not match observed_at {doc['observed_at']}")


# -- the replay ---------------------------------------------------------------------------

def present_keys(state: RegionReplay) -> set[str]:
    return {k for k, e in state.entries.items() if e.absent_since is None}


def verify(state: RegionReplay, keys: set[str], doc: dict, label: str) -> None:
    missing = keys - set(state.entries)
    if missing:
        raise ChainError(f"{label}: lists {len(missing)} key(s) the replay never saw arrive, "
                         f"for example {sorted(missing)[0]}")
    pairs = [(k, fingerprint(state.entries[k].watched)) for k in keys]
    if snapshot_hash(pairs) != doc["snapshot_sha256"]:
        raise ChainError(f"{label}: the replayed state does not hash to snapshot_sha256")
    if len(keys) != doc["entry_count"]:
        raise ChainError(f"{label}: {len(keys)} keys present, entry_count says {doc['entry_count']}")
    cells = sum(len(state.entries[k].cells) for k in keys)
    if cells != doc["cell_count"]:
        raise ChainError(f"{label}: {cells} cells present, cell_count says {doc['cell_count']}")


def seed(state: RegionReplay, doc: dict, mapping: dict) -> None:
    at = doc["observed_at"]
    state.first_observed_at = at
    for e in doc["entries"]:
        entry = Entry(e["model_key"], copy.deepcopy(e["watched"]))
        for cell in e["cells"]:
            state.open_cell(entry, cell, cell["deployment_type"], None, at, entry.watched)
        state.entries[entry.model_key] = entry
        state.state(entry.model_key, entry.watched, None, at, mapping)
        state.note_model(entry.model_key, entry.watched)


def apply_checkpoint(state: RegionReplay, doc: dict, label: str) -> None:
    """A later checkpoint restates the full state: prove the replay agrees, then take its moment facts."""
    at = doc["observed_at"]
    listed = {e["model_key"]: e for e in doc["entries"]}
    # A key the replay holds but the checkpoint lacks went absent in a run with no file;
    # its absence is confirmed by a later file, so here it only starts waiting.
    for key in present_keys(state) - set(listed):
        state.entries[key].absent_since = at
    for key, e in listed.items():
        entry = state.entries.get(key)
        if entry is None:
            raise ChainError(f"{label}: lists {key}, which the replay never saw arrive")
        if fingerprint(entry.watched) != fingerprint(e["watched"]):
            raise ChainError(f"{label}: {key} differs from the replayed watched fields")
        names = {c["deployment_type"] for c in e["cells"]}
        if names != set(entry.cells):
            raise ChainError(f"{label}: {key} cells {sorted(names)} differ from the replayed "
                             f"{sorted(entry.cells)}")
        entry.absent_since = None
        for cell in e["cells"]:
            absorb(entry.cells[cell["deployment_type"]], cell)
    verify(state, set(listed), doc, label)


def apply_change(state: RegionReplay, ch: dict, mapping: dict, label: str) -> None:
    kind, key = ch["kind"], ch["model_key"]
    after, by = ch["window_start"], ch["window_end"]
    entry = state.entries.get(key)

    if kind in ARRIVAL_KINDS:
        watched = ch.get("after")
        if watched is None:
            raise ChainError(f"{label}: {kind} {key} carries no after")
        if entry is None:
            entry = Entry(key, copy.deepcopy(watched))
            state.entries[key] = entry
        else:
            if kind != "returned":
                raise ChainError(f"{label}: {kind} {key}, but the replay already holds it")
            # Back before the absence was confirmed: the watcher calls it a flap, not an
            # ending undone, so the presence window carries on unbroken.
            entry.watched = copy.deepcopy(watched)
        entry.absent_since = None
        cells = ch.get("cells") or []
        by_name = {c["deployment_type"]: c for c in cells}
        for name in sorted(by_name) or sku_names(watched):
            state.open_cell(entry, by_name.get(name), name, after, by, entry.watched)
        state.state(key, entry.watched, after, by, mapping)
        state.note_model(key, entry.watched)
        return

    if entry is None:
        raise ChainError(f"{label}: {kind} {key}, which the replay does not hold")

    if kind == "last_seen_absent":
        confirmed = ch.get("confirmed_at")
        for c in sorted(entry.cells.values(), key=lambda c: c.deployment_type):
            state.close_cell(key, c, after, by, confirmed)
        del state.entries[key]
        state.open_state.pop(key, None)
        return

    if kind == "capacity_changed":
        # Capacity is the watcher's subscription quota, never published; the watcher no longer
        # writes this kind, and a committed one changes nothing the catalogue shows.
        return

    if kind in FIELD_KINDS:
        before_names = set(entry.cells)
        watched = ch.get("after")
        if watched is None:
            raise ChainError(f"{label}: {kind} {key} carries no after")
        entry.watched = copy.deepcopy(watched)
        cells = {c["deployment_type"]: c for c in ch.get("cells") or []}
        if kind == "deployment_type_added":
            for name in sorted(cells) or sorted(set(sku_names(watched)) - before_names):
                state.open_cell(entry, cells.get(name), name, after, by, entry.watched)
        elif kind == "deployment_type_removed":
            for name in sorted(cells) or sorted(before_names - set(sku_names(watched))):
                c = entry.cells.pop(name, None)
                if c is None:
                    raise ChainError(f"{label}: removes {key} {name}, which the replay does not hold")
                state.close_cell(key, c, after, by, None)
        for name, c in entry.cells.items():
            c.sku_deprecation_date = sku_date(entry.watched, name)
        state.state(key, entry.watched, after, by, mapping)
        state.note_model(key, entry.watched)
        return

    raise ChainError(f"{label}: unknown change kind {kind}")


def apply_observation(state: RegionReplay, doc: dict, mapping: dict, label: str) -> None:
    for ch in doc["changes"]:
        apply_change(state, ch, mapping, label)
    keys = set(doc["keys_present"])
    for key, entry in state.entries.items():
        if key not in keys and entry.absent_since is None:
            entry.absent_since = doc["observed_at"]
        elif key in keys:
            entry.absent_since = None
    verify(state, keys, doc, label)


def replay_region(root: Path, source: str, region: str, paths: dict[str, list[Path]],
                  validators: dict[str, Draft202012Validator], mapping: dict) -> RegionReplay:
    state = RegionReplay(region=region, source=source)
    docs: list[tuple[str, int, str, dict]] = []
    for path in paths["checkpoints"]:
        doc = load_json(path)
        label = relative(root, path)
        check(validators["checkpoint"], doc, label)
        check_placement(root, path, doc, "checkpoints")
        docs.append((doc["observed_at"], 1, label, doc))
    for path in paths["observations"]:
        doc = load_json(path)
        label = relative(root, path)
        check(validators["observation"], doc, label)
        check_placement(root, path, doc, "observations")
        docs.append((doc["observed_at"], 0, label, doc))
    # At one run the observation file comes before the checkpoint the same run wrote.
    docs.sort(key=lambda d: (d[0], d[1]))

    if not docs or docs[0][1] != 1 or docs[0][3]["kind"] != "seed":
        raise ChainError(f"{source}/{region}: the chain does not start with a seed checkpoint")
    seeds = [label for _at, is_cp, label, doc in docs if is_cp and doc["kind"] == "seed"]
    if len(seeds) != 1:
        raise ChainError(f"{source}/{region}: {len(seeds)} seed checkpoints, expected one")

    last_checkpoint: str | None = None
    last_file: str | None = None
    last_run: str | None = None
    for at, is_cp, label, doc in docs:
        if last_run is not None and at < last_run:
            raise ChainError(f"{label}: observed_at goes backwards")
        if is_cp:
            if doc["kind"] == "seed":
                seed(state, doc, mapping)
                verify(state, {e["model_key"] for e in doc["entries"]}, doc, label)
            else:
                apply_checkpoint(state, doc, label)
            last_checkpoint = label
            state.checkpoints += 1
        else:
            if doc["previous_file"] != last_file:
                raise ChainError(f"{label}: previous_file is {doc['previous_file']}, the chain says {last_file}")
            if doc["checkpoint"] != last_checkpoint:
                raise ChainError(f"{label}: checkpoint is {doc['checkpoint']}, the chain says {last_checkpoint}")
            if doc["previous_run_at"] < (last_run or "") or doc["previous_run_at"] >= at:
                raise ChainError(f"{label}: previous_run_at {doc['previous_run_at']} is outside the chain")
            apply_observation(state, doc, mapping, label)
            last_file = label
            state.files += 1
        state.observed_from = doc["observed_from"]
        state.last_observed_at = at
        last_run = at
    return state


# -- output ---------------------------------------------------------------------------------

def tracker_links(root: Path) -> dict[str, str]:
    """ARM spelling -> tracker model id, only where data/models.yaml lists it in `aliases` (ruling 35)."""
    registry = yaml.safe_load((root / "data" / "models.yaml").read_text(encoding="utf-8"))
    links: dict[str, str] = {}
    for model in registry.get("models") or []:
        for alias in model.get("aliases") or []:
            links.setdefault(alias, model["id"])
    return links


def build_intervals(states: list[RegionReplay], links: dict[str, str]) -> dict:
    cells: list[dict] = []
    segments: list[dict] = []
    models: dict[str, dict] = {}
    regions: dict[str, dict] = {}
    for state in states:
        cells.extend(state.cell_rows)
        for key, entry in state.entries.items():
            for c in entry.cells.values():
                row = cell_row(state.region, key, c, None)
                if entry.absent_since is not None:
                    row["absent_unconfirmed_since"] = entry.absent_since
                cells.append(row)
        segments.extend(state.state_rows)
        for key, watched in state.models.items():
            name = watched.get("name") or key.split("@", 1)[0]
            models[key] = {
                "name": name,
                "version": watched.get("version") or key.split("@", 1)[1],
                "format": watched.get("format"),
                "tracker_model": links.get(key) or links.get(name),
            }
        regions[state.region] = {
            "first_observed_at": state.first_observed_at,
            "last_observed_at": state.last_observed_at,
            "observed_from": state.observed_from,
            "observation_files": state.files,
            "checkpoints": state.checkpoints,
            "entries_present": len(present_keys(state)),
        }
    cells.sort(key=lambda r: (r["region"], r["model_key"], r["deployment_type"], r["seen_from"]["by"]))
    segments.sort(key=lambda r: (r["region"], r["model_key"], r["from"]["by"]))
    first = min((r["first_observed_at"] for r in regions.values()), default=None)
    through = max((r["last_observed_at"] for r in regions.values()), default=None)
    return {
        "schema_version": INTERVALS_SCHEMA_VERSION,
        "source": "arm",
        "note": (
            "Derived by replaying observations/ from checkpoints/. Observed, not confirmed: a listing "
            "is one subscription's view, absence is weak evidence, and every edge is a window between "
            "two runs. Nothing before first_observed_at was observed."
        ),
        "first_observed_at": first,
        "observed_through": through,
        "regions": dict(sorted(regions.items())),
        "models": dict(sorted(models.items())),
        "cells": cells,
        "states": segments,
    }


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")


def write_manifest(site: Path, intervals: dict) -> None:
    files = []
    for published, (origin, description) in PUBLISHED_FILES.items():
        payload = (site / published).read_bytes()
        files.append({
            "path": published,
            "media_type": "application/json",
            "origin": origin,
            "description": description,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        })
    manifest = {
        "catalogue_contract_version": CATALOGUE_CONTRACT_VERSION,
        "first_observed_at": intervals["first_observed_at"],
        "observed_through": intervals["observed_through"],
        "base_url": BASE_URL,
        "documentation": DOCUMENTATION,
        "licence": {
            "data": "CC-BY-4.0",
            "code": "MIT",
            "attribution": ATTRIBUTION,
            "notice": (
                "A sourced research project, not official product documentation. "
                "Not affiliated with Microsoft, OpenAI, Anthropic or GitHub."
            ),
        },
        "files": files,
    }
    with (site / "catalogue" / "manifest.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def build(root: Path, out: Path) -> dict:
    """Replay every chain under root and write the catalogue into out/catalogue/. Returns the intervals."""
    validators = {"observation": validator(root, "observation.schema.json"),
                  "checkpoint": validator(root, "checkpoint.schema.json")}
    mapping = load_json(root / "schema" / "lifecycle-mapping.json")["api_to_portal"]
    states = [replay_region(root, source, region, paths, validators, mapping)
              for (source, region), paths in sorted(collect(root).items())]
    intervals = build_intervals(states, tracker_links(root))
    target = out / "catalogue"
    if target.exists():
        shutil.rmtree(target)
    write_json(target / "intervals.json", intervals)
    for published, committed in EXPORTS.items():
        source = root / committed
        if not source.exists():
            raise ChainError(f"{committed} is missing; the catalogue promises {published}")
        shutil.copyfile(source, out / published)
    write_manifest(out, intervals)
    return intervals


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT.parent
    try:
        intervals = build(ROOT, out)
    except ChainError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
    open_cells = sum(1 for c in intervals["cells"] if c["seen_until"] is None)
    print(
        f"Replayed {len(intervals['regions'])} region(s) through {intervals['observed_through']}: "
        f"{len(intervals['models'])} model keys, {open_cells} cells present, "
        f"{len(intervals['cells']) - open_cells} closed, {len(intervals['states'])} state segments; "
        f"wrote {(out / 'catalogue').as_posix()}."
    )


if __name__ == "__main__":
    main()
