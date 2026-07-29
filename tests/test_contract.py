"""The published data contract is a promise to consumers in other repositories.

These tests guard the parts a display layer depends on. A change that breaks
one of them is a breaking change under docs/data-contract.md and needs a
version bump, not a green build.
"""
from __future__ import annotations

import csv
import hashlib
import json
import unittest
from pathlib import Path

from scripts import build

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "generated"


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads((GENERATED / "manifest.json").read_text(encoding="utf-8"))
        cls.events = json.loads((GENERATED / "events.json").read_text(encoding="utf-8"))

    def test_manifest_declares_both_versions(self) -> None:
        self.assertEqual(self.manifest["contract_version"], build.CONTRACT_VERSION)
        self.assertEqual(self.manifest["dataset_version"], self.events["version"])

    def test_manifest_lists_every_promised_file(self) -> None:
        listed = [entry["path"] for entry in self.manifest["files"]]
        self.assertEqual(listed, list(build.PUBLISHED_FILES))

    def test_every_promised_file_exists_with_a_matching_checksum(self) -> None:
        source = {"data": GENERATED, "schema": ROOT / "schema"}
        for entry in self.manifest["files"]:
            with self.subTest(entry["path"]):
                prefix, _, name = entry["path"].partition("/")
                payload = (source[prefix] / name).read_bytes()
                self.assertEqual(len(payload), entry["bytes"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), entry["sha256"])

    def test_manifest_carries_attribution_for_cc_by(self) -> None:
        """CC BY requires attribution, so the string a consumer should display
        is published rather than left for them to invent."""
        licence = self.manifest["licence"]
        self.assertEqual(licence["data"], "CC-BY-4.0")
        self.assertTrue(licence["attribution"])
        self.assertIn("not official product documentation", licence["notice"])

    def test_manifest_has_no_build_timestamp(self) -> None:
        """A timestamp would make the build irreproducible, which CI enforces
        with `git diff --exit-code`. Only data dates belong here."""
        flat = json.dumps(self.manifest)
        self.assertNotIn("generated_at", flat)
        self.assertNotIn("built_at", flat)
        self.assertEqual(self.manifest["updated"], self.events["updated"])


class LagBaselineTests(unittest.TestCase):
    """A shutdown is an availability event but not an arrival. Treating one as
    the vendor release would date a model's launch to the day it was switched
    off, and every platform event would then look like it predates the model."""

    def test_a_retirement_is_not_an_arrival(self) -> None:
        self.assertNotIn("retired", build.ARRIVAL_LIFECYCLES)
        self.assertNotIn("deprecated", build.ARRIVAL_LIFECYCLES)
        self.assertNotIn("legacy", build.ARRIVAL_LIFECYCLES)
        self.assertNotIn("suspended", build.ARRIVAL_LIFECYCLES)

    def test_no_published_lag_row_is_anchored_to_a_shutdown(self) -> None:
        with (GENERATED / "lag.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        anchored = {r["baseline_lifecycle"] for r in rows if r["baseline_lifecycle"]}
        self.assertTrue(anchored <= build.ARRIVAL_LIFECYCLES, f"anchored to {anchored}")

    def test_retirement_only_vendor_record_yields_no_baseline(self) -> None:
        """DALL-E 2's only OpenAI record is its shutdown. Its lag must be
        unknown, not measured from the day it stopped working."""
        models = {"models": [{"id": "m", "display_name": "M", "vendor": "V"}]}
        platforms = {"surfaces": [
            {"id": "vendor", "display_name": "V", "vendor_baseline": True, "counts_as": []},
            {"id": "product", "display_name": "P", "counts_as": ["microsoft"]},
        ]}
        data = {"events": [
            {"id": "gone", "kind": "availability", "date": {"start": "2026-05-12", "precision": "day"},
             "surface_id": "vendor", "model_ids": ["m"], "lifecycle": "retired", "exposure": "not_applicable"},
            {"id": "on-product", "kind": "availability", "date": {"start": "2023-01-17", "precision": "day"},
             "surface_id": "product", "model_ids": ["m"], "lifecycle": "ga", "exposure": "catalogue"},
        ], "validation_backlog": []}
        rows = build.derive_lag(data, models, platforms)
        microsoft = [r for r in rows if r["tier"] == "microsoft" and r["measure"] == "any_exposure"]
        self.assertTrue(microsoft)
        self.assertEqual(microsoft[0]["certainty"], "unknown_no_baseline")


class ConsumerContractTests(unittest.TestCase):
    """Guarantees docs/data-contract.md makes to display layers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.events = json.loads((GENERATED / "events.json").read_text(encoding="utf-8"))

    def test_only_availability_events_carry_lifecycle_and_exposure(self) -> None:
        """Consumers filter on `kind` to keep announcements off a timeline. The
        absence of lifecycle/exposure is the structural backstop for that."""
        for event in self.events["events"]:
            with self.subTest(event["id"]):
                if event["kind"] == "availability":
                    self.assertIn("lifecycle", event)
                    self.assertIn("exposure", event)
                else:
                    self.assertNotIn("lifecycle", event)
                    self.assertNotIn("exposure", event)

    def test_policy_events_name_no_model(self) -> None:
        for event in self.events["events"]:
            if event["kind"] == "policy":
                with self.subTest(event["id"]):
                    self.assertEqual(event["model_ids"], [])

    def test_events_are_sorted_by_date_then_id(self) -> None:
        """The contract promises this ordering; a renderer may rely on it."""
        ids = [event["id"] for event in self.events["events"]]
        expected = [
            event["id"]
            for event in sorted(self.events["events"], key=lambda e: (e["date"]["start"], e["id"]))
        ]
        self.assertEqual(ids, expected)

    def test_every_event_date_declares_its_precision(self) -> None:
        """A renderer formats from precision. Without it, a month-only date
        gets displayed as an exact day."""
        for event in self.events["events"]:
            with self.subTest(event["id"]):
                self.assertIn(event["date"]["precision"], {"day", "month", "year"})

    def test_closed_enums_hold_only_documented_values(self) -> None:
        kinds = {"availability", "announcement", "policy", "milestone"}
        lifecycles = {
            "private_preview", "limited_preview", "public_preview", "ga",
            "legacy", "deprecated", "retired", "suspended", "restored",
        }
        exposures = {
            "underlying", "specialist", "catalogue", "selectable", "default", "not_applicable",
        }
        for event in self.events["events"]:
            with self.subTest(event["id"]):
                self.assertIn(event["kind"], kinds)
                self.assertIn(event["confidence"], {"confirmed", "supported"})
                if event["kind"] == "availability":
                    self.assertIn(event["lifecycle"], lifecycles)
                    self.assertIn(event["exposure"], exposures)

    def test_backlog_states_are_documented(self) -> None:
        for item in self.events["validation_backlog"]:
            with self.subTest(item["id"]):
                self.assertIn(item["state"], {"open", "promoted", "rejected", "blocked"})

    def test_surface_tiers_keep_the_distinctions_the_contract_promises(self) -> None:
        surfaces = {
            entry["id"]: entry
            for entry in build.load_validated(build.PLATFORMS_PATH, build.PLATFORMS_SCHEMA_PATH)["surfaces"]
        }
        self.assertNotIn("copilot", surfaces["github-models"]["counts_as"])
        self.assertIn("microsoft", surfaces["github-models"]["counts_as"])
        self.assertNotIn("copilot", surfaces["microsoft-foundry"]["counts_as"])
        self.assertNotIn("copilot", surfaces["m365-admin"]["counts_as"])


class CurrentStateTests(unittest.TestCase):
    """current-state.csv exists so renderers do not each re-derive "is it still
    available" and each get it wrong the same way."""

    @classmethod
    def setUpClass(cls) -> None:
        with (GENERATED / "current-state.csv").open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.events = json.loads((GENERATED / "events.json").read_text(encoding="utf-8"))

    def test_covers_every_model_and_surface_with_an_availability_event(self) -> None:
        expected = {
            (model_id, event["surface_id"])
            for event in self.events["events"]
            if event["kind"] == "availability"
            for model_id in event["model_ids"]
        }
        self.assertEqual({(r["model_id"], r["surface_id"]) for r in self.rows}, expected)

    def test_terminal_flag_agrees_with_the_lifecycle(self) -> None:
        for row in self.rows:
            with self.subTest(row["last_event"]):
                self.assertEqual(
                    row["state_is_terminal"] == "true",
                    row["lifecycle"] in build.TERMINAL_LIFECYCLES,
                )

    def test_named_event_is_the_latest_for_that_pair(self) -> None:
        by_id = {e["id"]: e for e in self.events["events"]}
        for row in self.rows:
            with self.subTest(f'{row["model_id"]}/{row["surface_id"]}'):
                named = by_id[row["last_event"]]
                latest = max(
                    (
                        e for e in self.events["events"]
                        if e["kind"] == "availability"
                        and row["model_id"] in e["model_ids"]
                        and e["surface_id"] == row["surface_id"]
                    ),
                    key=lambda e: build.date_interval(e["date"])[0],
                )
                self.assertEqual(
                    build.date_interval(named["date"])[0],
                    build.date_interval(latest["date"])[0],
                )

    def test_carries_the_research_cutoff_so_staleness_is_computable(self) -> None:
        """No build timestamp is available, so a consumer needs the cutoff to
        judge how old a non-terminal state is."""
        for row in self.rows:
            self.assertEqual(row["known_as_of"], self.events["research_cutoff"])


class LifecycleOrderTests(unittest.TestCase):
    def test_progression_includes_the_end_of_life_stages(self) -> None:
        """Ordering has to cover the terminal stages, or a return to GA after
        retirement would not be detected as a regression."""
        self.assertEqual(
            build.LIFECYCLE_ORDER,
            ["private_preview", "limited_preview", "public_preview",
             "ga", "legacy", "deprecated", "retired"],
        )

    def test_ga_after_retirement_is_rejected(self) -> None:
        events = [
            {"id": "retired", "kind": "availability", "date": {"start": "2025-01-01", "precision": "day"},
             "surface_id": "s", "model_ids": ["m"], "lifecycle": "retired", "exposure": "catalogue"},
            {"id": "back", "kind": "availability", "date": {"start": "2025-06-01", "precision": "day"},
             "surface_id": "s", "model_ids": ["m"], "lifecycle": "ga", "exposure": "catalogue"},
        ]
        with self.assertRaises(SystemExit):
            build.check_lifecycle_ordering(events)

    def test_suspension_is_not_a_stage(self) -> None:
        """A suspension is a reversible interruption, so a later GA is not a
        regression and must not be rejected."""
        events = [
            {"id": "ga", "kind": "availability", "date": {"start": "2025-01-01", "precision": "day"},
             "surface_id": "s", "model_ids": ["m"], "lifecycle": "ga", "exposure": "catalogue"},
            {"id": "susp", "kind": "availability", "date": {"start": "2025-02-01", "precision": "day"},
             "surface_id": "s", "model_ids": ["m"], "lifecycle": "suspended", "exposure": "catalogue"},
            {"id": "rest", "kind": "availability", "date": {"start": "2025-03-01", "precision": "day"},
             "surface_id": "s", "model_ids": ["m"], "lifecycle": "ga", "exposure": "catalogue"},
        ]
        build.check_lifecycle_ordering(events)


if __name__ == "__main__":
    unittest.main()
