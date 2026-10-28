"""The catalogue build: replaying observations/ from checkpoints/ into the derived catalogue.

Each test writes a small synthetic chain into a temporary repository with the
real schemas, runs the build and reads what it published. The chains are
hashed with the watcher's formulas, so a test that passes here is a chain the
watcher could have written.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import build_catalogue as bc

ROOT = Path(__file__).resolve().parents[1]

T0 = "2026-10-27T19:30:00Z"
T1 = "2026-10-28T01:30:00Z"
T2 = "2026-10-28T07:30:00Z"
T3 = "2026-10-28T13:30:00Z"
T4 = "2026-10-28T19:30:00Z"
NOV = "2026-11-01T01:30:00Z"
LABEL = "standard pay-as-you-go subscription"


def watched(name: str, version: str = "1", status: str = "Preview", skus: tuple[str, ...] = ("GlobalStandard",),
            caps: dict | None = None, deprecation: str | None = None) -> dict:
    portal = {"Preview": "Preview", "GenerallyAvailable": "Generally Available",
              "Deprecating": "Deprecated"}[status]
    return {
        "name": name, "version": version, "format": "Example", "lifecycle_status": status,
        "lifecycle_portal": portal, "deprecation_inference": deprecation, "deprecation_fine_tune": None,
        "is_default_version": True, "capabilities": caps or {"chatCompletion": "true"},
        "skus": [{"name": s, "deprecation_date": None} for s in skus],
    }


def key(w: dict) -> str:
    return f"{w['name']}@{w['version']}"


def cell(name: str, at: str, capacity: int | None = None) -> dict:
    return {"deployment_type": name, "first_seen": at, "last_seen": at, "removed_at": None,
            "sku_deprecation_date": None, "capacity": capacity, "capacity_at": at if capacity is not None else None}


def cells_of(w: dict, at: str) -> list[dict]:
    return [cell(s["name"], at) for s in w["skus"]] or [cell("none", at)]


def counts(present: list[dict]) -> dict:
    return {
        "entry_count": len(present),
        "cell_count": sum(max(len(w["skus"]), 1) for w in present),
        "snapshot_sha256": bc.snapshot_hash([(key(w), bc.fingerprint(w)) for w in present]),
    }


def checkpoint(region: str, at: str, present: list[dict], kind: str = "seed",
               capacity: dict | None = None) -> dict:
    entries = []
    for w in sorted(present, key=key):
        cs = cells_of(w, at)
        for c in cs:
            if capacity and (key(w), c["deployment_type"]) in capacity:
                c["capacity"] = capacity[(key(w), c["deployment_type"])]
                c["capacity_at"] = at
        entries.append({"model_key": key(w), "first_seen": at, "last_seen": at,
                        "watched": copy.deepcopy(w), "cells": cs})
    return {"schema_version": 1, "source": "arm", "region": region, "kind": kind, "observed_at": at,
            "observed_from": LABEL, **counts(present), "entries": entries}


def observation(region: str, at: str, previous_run_at: str, previous_file: str | None, cp: str,
                present: list[dict], changes: list[dict], silent: int = 0) -> dict:
    return {
        "schema_version": 1, "source": "arm", "region": region, "observed_at": at,
        "previous_run_at": previous_run_at, "runs_since_previous_file": silent,
        "previous_file": previous_file, "checkpoint": cp, "observed_from": LABEL,
        **counts(present), "keys_present": sorted(key(w) for w in present),
        "changes": sorted(changes, key=lambda c: (c["kind"], c["model_key"])),
    }


def cp_path(region: str, at: str) -> str:
    return f"checkpoints/arm/{region}/{bc.file_stamp(at)}.json"


def obs_path(region: str, at: str) -> str:
    return f"observations/arm/{region}/{at[0:4]}/{at[5:7]}/{bc.file_stamp(at)}.json"


class CatalogueBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        shutil.copytree(ROOT / "schema", self.tmp / "schema")
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "models.yaml").write_text(
            "models:\n  - id: alpha-1\n    aliases: [alpha]\n  - id: other\n", encoding="utf-8")
        (self.tmp / "status").mkdir()
        (self.tmp / "status" / "regions.json").write_text('{"regions": []}\n', encoding="utf-8")
        (self.tmp / "status" / "arm.json").write_text('{"regions": {}}\n', encoding="utf-8")
        self.out = self.tmp / "_site"

    def put(self, path: str, doc: dict) -> str:
        target = self.tmp / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        return path

    def build(self) -> dict:
        return bc.build(self.tmp, self.out)

    def fails(self, fragment: str) -> None:
        with self.assertRaises(bc.ChainError) as caught:
            self.build()
        self.assertIn(fragment, str(caught.exception))

    def rows(self, intervals: dict, model_key: str, region: str = "uksouth") -> list[dict]:
        return [c for c in intervals["cells"] if c["model_key"] == model_key and c["region"] == region]

    def states(self, intervals: dict, model_key: str, region: str = "uksouth") -> list[dict]:
        return [s for s in intervals["states"] if s["model_key"] == model_key and s["region"] == region]

    # -- the seed ------------------------------------------------------------------------

    def test_a_seed_alone_is_present_from_the_first_observation(self) -> None:
        a = watched("alpha", skus=("GlobalStandard", "Standard"))
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        intervals = self.build()
        rows = self.rows(intervals, "alpha@1")
        self.assertEqual([r["deployment_type"] for r in rows], ["GlobalStandard", "Standard"])
        for r in rows:
            self.assertEqual(r["seen_from"], {"after": None, "by": T0})
            self.assertIsNone(r["seen_until"])
        self.assertEqual(intervals["first_observed_at"], T0)
        self.assertEqual(intervals["regions"]["uksouth"]["entries_present"], 1)
        state = self.states(intervals, "alpha@1")[0]
        self.assertEqual((state["lifecycle_portal"], state["dataset_lifecycle"]), ("Preview", "public_preview"))

    def test_an_entry_with_no_skus_is_the_single_cell_none(self) -> None:
        a = watched("alpha", skus=())
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.assertEqual([r["deployment_type"] for r in self.rows(self.build(), "alpha@1")], ["none"])

    def test_models_link_to_the_tracker_only_through_aliases(self) -> None:
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [watched("alpha"), watched("beta")]))
        models = self.build()["models"]
        self.assertEqual(models["alpha@1"]["tracker_model"], "alpha-1")
        self.assertIsNone(models["beta@1"]["tracker_model"])

    def test_a_lookalike_name_is_suggested_never_linked(self) -> None:
        (self.tmp / "data" / "models.yaml").write_text(
            "models:\n  - id: gpt-5-1\n    display_name: GPT-5.1\n  - id: alpha-1\n    aliases: [alpha]\n",
            encoding="utf-8")
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [watched("gpt-5.1"), watched("alpha"),
                                                                     watched("gpt-5.1-mini")]))
        intervals = self.build()
        self.assertIsNone(intervals["models"]["gpt-5.1@1"]["tracker_model"])
        self.assertEqual(bc.unlinked_suggestions(self.tmp, intervals), [("gpt-5.1", "gpt-5-1")])

    def test_the_build_is_reproducible_and_the_manifest_checks_out(self) -> None:
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [watched("alpha")]))
        self.build()
        first = {p.name: p.read_bytes() for p in (self.out / "catalogue").iterdir()}
        self.build()
        second = {p.name: p.read_bytes() for p in (self.out / "catalogue").iterdir()}
        self.assertEqual(first, second)
        manifest = json.loads(first["manifest.json"])
        self.assertEqual(manifest["catalogue_contract_version"], bc.CATALOGUE_CONTRACT_VERSION)
        for entry in manifest["files"]:
            payload = (self.out / entry["path"]).read_bytes()
            self.assertEqual(entry["bytes"], len(payload))
            self.assertEqual(entry["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(first["regions.json"], (self.tmp / "status" / "regions.json").read_bytes())
        self.assertEqual(first["status.json"], (self.tmp / "status" / "arm.json").read_bytes())

    def test_no_catalogue_files_builds_an_empty_catalogue(self) -> None:
        intervals = self.build()
        self.assertEqual((intervals["cells"], intervals["first_observed_at"]), ([], None))

    # -- the replay ----------------------------------------------------------------------

    def test_an_arrival_is_a_window_between_two_runs(self) -> None:
        a, b = watched("alpha"), watched("beta")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(obs_path("uksouth", T2), observation("uksouth", T2, T1, None, cp, [a, b], [
            {"kind": "first_seen_present", "model_key": "beta@1", "window_start": T1, "window_end": T2,
             "after": b, "cells": [cell("GlobalStandard", T2, capacity=250)]},
        ], silent=1))
        row = self.rows(self.build(), "beta@1")[0]
        self.assertEqual(row["seen_from"], {"after": T1, "by": T2})
        self.assertNotIn("capacity", row)

    def test_a_stage_change_opens_a_new_state_segment(self) -> None:
        a = watched("alpha")
        ga = watched("alpha", status="GenerallyAvailable")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [ga], [
            {"kind": "lifecycle_changed", "model_key": "alpha@1", "window_start": T0, "window_end": T1,
             "fields": ["lifecycle_status", "lifecycle_portal"], "before": a, "after": ga},
        ]))
        states = self.states(self.build(), "alpha@1")
        self.assertEqual([s["lifecycle_status"] for s in states], ["Preview", "GenerallyAvailable"])
        self.assertEqual(states[1]["from"], {"after": T0, "by": T1})

    def test_a_capability_change_opens_a_new_state_segment(self) -> None:
        a = watched("alpha")
        more = watched("alpha", caps={"chatCompletion": "true", "responses": "true"})
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [more], [
            {"kind": "fields_changed", "model_key": "alpha@1", "window_start": T0, "window_end": T1,
             "fields": ["capabilities.responses"], "before": a, "after": more},
        ]))
        self.assertEqual(len(self.states(self.build(), "alpha@1")), 2)

    def test_deployment_types_open_and_close_their_own_windows(self) -> None:
        a = watched("alpha")
        wider = watched("alpha", skus=("GlobalStandard", "Standard"))
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        f1 = self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [wider], [
            {"kind": "deployment_type_added", "model_key": "alpha@1", "window_start": T0, "window_end": T1,
             "fields": ["skus"], "before": a, "after": wider, "cells": [cell("Standard", T1)]},
        ]))
        self.put(obs_path("uksouth", T2), observation("uksouth", T2, T1, f1, cp, [a], [
            {"kind": "deployment_type_removed", "model_key": "alpha@1", "window_start": T1, "window_end": T2,
             "fields": ["skus"], "before": wider, "after": a, "cells": [cell("Standard", T1)]},
        ]))
        rows = {r["deployment_type"]: r for r in self.rows(self.build(), "alpha@1")}
        self.assertIsNone(rows["GlobalStandard"]["seen_until"])
        self.assertEqual(rows["Standard"]["seen_from"], {"after": T0, "by": T1})
        self.assertEqual(rows["Standard"]["seen_until"], {"last_seen": T1, "absent_by": T2, "confirmed_at": None})

    def test_an_absence_waits_for_confirmation_then_closes_the_window(self) -> None:
        a, b, c = watched("alpha"), watched("beta"), watched("gamma")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a, b]))
        # beta is missing at T1, but the run reports only gamma's arrival
        f1 = self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [a, c], [
            {"kind": "first_seen_present", "model_key": "gamma@1", "window_start": T0, "window_end": T1,
             "after": c, "cells": [cell("GlobalStandard", T1)]},
        ]))
        pending = self.rows(self.build(), "beta@1")[0]
        self.assertIsNone(pending["seen_until"])
        self.assertEqual(pending["absent_unconfirmed_since"], T1)
        self.put(obs_path("uksouth", T3), observation("uksouth", T3, T2, f1, cp, [a, c], [
            {"kind": "last_seen_absent", "model_key": "beta@1", "window_start": T0, "window_end": T1,
             "confirmed_at": T3, "absence_strength": "weak", "before": b,
             "cells": [cell("GlobalStandard", T0)]},
        ], silent=1))
        intervals = self.build()
        closed = self.rows(intervals, "beta@1")[0]
        self.assertEqual(closed["seen_until"], {"last_seen": T0, "absent_by": T1, "confirmed_at": T3})
        self.assertNotIn("absent_unconfirmed_since", closed)
        self.assertEqual(intervals["regions"]["uksouth"]["entries_present"], 2)

    def test_a_return_after_a_confirmed_absence_opens_a_second_window(self) -> None:
        a, b = watched("alpha"), watched("beta")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a, b]))
        f1 = self.put(obs_path("uksouth", T2), observation("uksouth", T2, T1, None, cp, [a], [
            {"kind": "last_seen_absent", "model_key": "beta@1", "window_start": T0, "window_end": T1,
             "confirmed_at": T2, "absence_strength": "weak", "before": b, "cells": [cell("GlobalStandard", T0)]},
        ], silent=1))
        self.put(obs_path("uksouth", T4), observation("uksouth", T4, T3, f1, cp, [a, b], [
            {"kind": "returned", "model_key": "beta@1", "window_start": T3, "window_end": T4,
             "before": b, "after": b, "cells": [cell("GlobalStandard", T4)],
             "note": "back after 3 absent run(s); an absence event was reported"},
        ], silent=1))
        windows = [(r["seen_from"]["by"], r["seen_until"]) for r in self.rows(self.build(), "beta@1")]
        self.assertEqual(windows, [(T0, {"last_seen": T0, "absent_by": T1, "confirmed_at": T2}), (T4, None)])

    def test_a_flap_before_confirmation_keeps_one_window(self) -> None:
        a, b, c = watched("alpha"), watched("beta"), watched("gamma")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a, b]))
        f1 = self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [a, c], [
            {"kind": "first_seen_present", "model_key": "gamma@1", "window_start": T0, "window_end": T1,
             "after": c, "cells": [cell("GlobalStandard", T1)]},
        ]))
        self.put(obs_path("uksouth", T2), observation("uksouth", T2, T1, f1, cp, [a, b, c], [
            {"kind": "returned", "model_key": "beta@1", "window_start": T1, "window_end": T2,
             "before": b, "after": b, "cells": [cell("GlobalStandard", T2)],
             "note": "back after 1 absent run(s); an absence event was not reported"},
        ]))
        rows = self.rows(self.build(), "beta@1")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["seen_from"]["by"], T0)
        self.assertNotIn("absent_unconfirmed_since", rows[0])

    def test_a_monthly_checkpoint_agrees_and_its_capacity_is_not_published(self) -> None:
        a = watched("alpha")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(cp_path("uksouth", NOV), checkpoint("uksouth", NOV, [a], kind="monthly",
                                                     capacity={("alpha@1", "GlobalStandard"): 500}))
        intervals = self.build()
        row = self.rows(intervals, "alpha@1")[0]
        self.assertEqual(row["seen_from"]["by"], T0)
        self.assertNotIn("capacity", row)
        self.assertNotIn("capacity_at", row)
        self.assertEqual(intervals["regions"]["uksouth"]["checkpoints"], 2)
        self.assertEqual(intervals["observed_through"], NOV)
        self.assertTrue(cp)

    def test_a_committed_capacity_change_changes_nothing_published(self) -> None:
        a = watched("alpha")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [a], [
            {"kind": "capacity_changed", "model_key": "alpha@1", "window_start": T0, "window_end": T1,
             "fields": ["cells[GlobalStandard].capacity"], "note": "GlobalStandard capacity 100 → 250"},
        ]))
        row = self.rows(self.build(), "alpha@1")[0]
        self.assertEqual(row["seen_from"]["by"], T0)
        self.assertNotIn("capacity", row)

    # -- a chain that does not add up fails the build ------------------------------------------

    def test_a_chain_without_a_seed_fails(self) -> None:
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [watched("alpha")], kind="monthly"))
        self.fails("does not start with a seed checkpoint")

    def test_a_wrong_snapshot_hash_fails(self) -> None:
        doc = checkpoint("uksouth", T0, [watched("alpha")])
        doc["snapshot_sha256"] = "0" * 64
        self.put(cp_path("uksouth", T0), doc)
        self.fails("does not hash to snapshot_sha256")

    def test_a_change_the_listing_does_not_show_fails(self) -> None:
        a = watched("alpha")
        ga = watched("alpha", status="GenerallyAvailable")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        doc = observation("uksouth", T1, T0, None, cp, [ga], [
            {"kind": "lifecycle_changed", "model_key": "alpha@1", "window_start": T0, "window_end": T1,
             "fields": ["lifecycle_status"], "before": a, "after": ga},
        ])
        doc["snapshot_sha256"] = counts([a])["snapshot_sha256"]
        self.put(obs_path("uksouth", T1), doc)
        self.fails("does not hash to snapshot_sha256")

    def test_a_broken_previous_file_link_fails(self) -> None:
        a, b = watched("alpha"), watched("beta")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, obs_path("uksouth", T0), cp, [a, b], [
            {"kind": "first_seen_present", "model_key": "beta@1", "window_start": T0, "window_end": T1,
             "after": b, "cells": [cell("GlobalStandard", T1)]},
        ]))
        self.fails("previous_file is")

    def test_a_key_listed_without_an_arrival_fails(self) -> None:
        a, b, c = watched("alpha"), watched("beta"), watched("gamma")
        cp = self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [a]))
        self.put(obs_path("uksouth", T1), observation("uksouth", T1, T0, None, cp, [a, b, c], [
            {"kind": "first_seen_present", "model_key": "beta@1", "window_start": T0, "window_end": T1,
             "after": b, "cells": [cell("GlobalStandard", T1)]},
        ]))
        self.fails("never saw arrive")

    def test_a_monthly_checkpoint_that_disagrees_fails(self) -> None:
        self.put(cp_path("uksouth", T0), checkpoint("uksouth", T0, [watched("alpha")]))
        self.put(cp_path("uksouth", NOV), checkpoint("uksouth", NOV, [watched("alpha", status="GenerallyAvailable")],
                                                     kind="monthly"))
        self.fails("differs from the replayed watched fields")

    def test_a_file_named_for_another_run_fails(self) -> None:
        doc = checkpoint("uksouth", T0, [watched("alpha")])
        self.put(cp_path("uksouth", T1), doc)
        self.fails("file name does not match observed_at")

    def test_a_file_in_another_regions_folder_fails(self) -> None:
        self.put(cp_path("eastus2", T0), checkpoint("uksouth", T0, [watched("alpha")]))
        self.fails("do not match the path")

    def test_a_file_that_breaks_the_schema_fails(self) -> None:
        doc = checkpoint("uksouth", T0, [watched("alpha")])
        doc["surprise"] = True
        self.put(cp_path("uksouth", T0), doc)
        self.fails("schema violation")


class CommittedCatalogueTests(unittest.TestCase):
    def test_the_committed_chain_replays(self) -> None:
        with tempfile.TemporaryDirectory() as out:
            intervals = bc.build(ROOT, Path(out))
        for region, facts in intervals["regions"].items():
            self.assertGreaterEqual(facts["checkpoints"], 1, region)


if __name__ == "__main__":
    unittest.main()
