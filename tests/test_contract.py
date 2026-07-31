"""The published data contract is a promise to consumers in other repositories.

These tests guard the parts external consumers depend on. A change that breaks
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

    def test_schema_ids_are_their_published_urls(self) -> None:
        for entry in self.manifest["files"]:
            if not entry["path"].startswith("schema/"):
                continue
            with self.subTest(entry["path"]):
                schema = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
                self.assertEqual(schema["$id"], self.manifest["base_url"] + entry["path"])

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


class PreReleaseAccessTests(unittest.TestCase):
    """A partner surface dated before the vendor release is almost always an
    error, but not always. GitHub ran Copilot on Codex six weeks before OpenAI
    released Codex. The guard therefore stays fatal by default and the
    exception has to be declared in the data."""

    def _fixture(self, tags: list[str]) -> tuple[dict, dict, dict]:
        models = {"models": [{"id": "m", "display_name": "M", "vendor": "V"}]}
        platforms = {"surfaces": [
            {"id": "vendor", "display_name": "V", "vendor_baseline": True, "counts_as": []},
            {"id": "partner", "display_name": "P", "counts_as": ["microsoft"]},
        ]}
        events = [
            {"id": "vendor-release", "kind": "availability",
             "date": {"start": "2021-08-10", "precision": "day"}, "surface_id": "vendor",
             "model_ids": ["m"], "lifecycle": "private_preview", "exposure": "not_applicable"},
            {"id": "partner-first", "kind": "availability",
             "date": {"start": "2021-06-29", "precision": "day"}, "surface_id": "partner",
             "model_ids": ["m"], "lifecycle": "public_preview", "exposure": "underlying",
             "tags": tags},
        ]
        return events, models, platforms

    def _surfaces(self, platforms: dict) -> dict:
        return {s["id"]: s for s in platforms["surfaces"]}

    def test_undeclared_precedence_is_fatal(self) -> None:
        events, models, platforms = self._fixture(tags=[])
        with self.assertRaises(SystemExit):
            build.check_vendor_baseline(events, models, self._surfaces(platforms))

    def test_declared_precedence_warns_instead_of_failing(self) -> None:
        events, models, platforms = self._fixture(tags=["pre_release_access"])
        before = len(build.warnings)
        build.check_vendor_baseline(events, models, self._surfaces(platforms))
        raised = build.warnings[before:]
        self.assertTrue(any(w["code"] == "pre_release_access" for w in raised),
                        f"expected a pre_release_access warning, got {raised}")

    def test_the_exception_is_not_used_casually(self) -> None:
        """If this list grows, check each one is genuine partner pre-release
        access and not a date error being waved through."""
        events = json.loads((GENERATED / "events.json").read_text(encoding="utf-8"))
        tagged = [e["id"] for e in events["events"]
                  if "pre_release_access" in e.get("tags", [])]
        self.assertEqual(tagged, ["github-copilot-preview-codex-2021-06-29"])


class DayPrecisionTests(unittest.TestCase):
    """A day-precision date on the first of a month is the shape a padded month
    takes, so it is flagged. The flag clears only on evidence, never on age."""

    def _attested(self, *sources: dict) -> bool:
        return build.day_precision_is_attested(
            {"date": {"start": "2024-05-01", "precision": "day"}, "sources": list(sources)}
        )

    def test_a_bare_first_of_month_is_not_attested(self) -> None:
        self.assertFalse(self._attested({"url": "u"}))

    def test_a_source_published_that_day_attests_it(self) -> None:
        self.assertTrue(self._attested({"url": "u", "published_at": "2024-05-01"}))

    def test_a_source_published_another_day_does_not(self) -> None:
        self.assertFalse(self._attested({"url": "u", "published_at": "2024-05-14"}))

    def test_a_quote_must_claim_to_support_the_date(self) -> None:
        """A quote alone is not enough. Someone has to have asserted that the
        quote attests the date, which is what `supports` records."""
        self.assertFalse(self._attested({"url": "u", "quote": "q", "supports": ["model"]}))
        self.assertTrue(self._attested({"url": "u", "quote": "q", "supports": ["date"]}))

    def test_any_one_source_is_enough(self) -> None:
        self.assertTrue(self._attested({"url": "a"}, {"url": "b", "published_at": "2024-05-01"}))

    def test_every_remaining_first_of_month_date_is_attested(self) -> None:
        """If this fails, a first-of-month date has been added without either a
        same-day source or a quote asserted to support it."""
        events = json.loads((GENERATED / "events.json").read_text(encoding="utf-8"))
        unattested = [
            e["id"] for e in events["events"]
            if e["date"]["precision"] == "day" and e["date"]["start"].endswith("-01")
            and not any(
                s.get("published_at") == e["date"]["start"]
                or (s.get("quote") and "date" in s.get("supports", []))
                for s in e["sources"]
            )
        ]
        self.assertEqual(unattested, [])


class ConsumerContractTests(unittest.TestCase):
    """Guarantees docs/data-contract.md makes to external consumers."""

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
        """The contract promises this ordering; a consumer may rely on it."""
        ids = [event["id"] for event in self.events["events"]]
        expected = [
            event["id"]
            for event in sorted(self.events["events"], key=lambda e: (e["date"]["start"], e["id"]))
        ]
        self.assertEqual(ids, expected)

    def test_every_event_date_declares_its_precision(self) -> None:
        """A consumer interprets precision. Without it, a month-only date
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
    """current-state.csv exists so consumers do not each re-derive "is it still
    available" and each get it wrong the same way."""

    @classmethod
    def setUpClass(cls) -> None:
        with (GENERATED / "current-state.csv").open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.events = json.loads((GENERATED / "events.json").read_text(encoding="utf-8"))

    def test_covers_every_model_and_product_with_an_availability_event(self) -> None:
        """Rows are one per model and *product*, not per surface name: a
        product keeps one row across a rename."""
        platforms = build.load_validated(build.PLATFORMS_PATH, build.PLATFORMS_SCHEMA_PATH)
        groups = build.rename_groups(platforms)
        expected = {
            (model_id, groups[event["surface_id"]])
            for event in self.events["events"]
            if event["kind"] == "availability"
            for model_id in event["model_ids"]
        }
        actual = {(r["model_id"], groups[r["surface_id"]]) for r in self.rows}
        self.assertEqual(actual, expected)

    def test_a_rename_does_not_split_a_product_into_two_rows(self) -> None:
        platforms = build.load_validated(build.PLATFORMS_PATH, build.PLATFORMS_SCHEMA_PATH)
        groups = build.rename_groups(platforms)
        keys = [(r["model_id"], groups[r["surface_id"]]) for r in self.rows]
        self.assertEqual(len(keys), len(set(keys)), "a product appears twice under different names")

    def test_surface_shown_is_the_one_the_latest_event_used(self) -> None:
        """Not the rename group's representative, which would label current
        Copilot Studio rows with the Power Virtual Agents name."""
        by_id = {e["id"]: e for e in self.events["events"]}
        for row in self.rows:
            with self.subTest(row["last_event"]):
                self.assertEqual(row["surface_id"], by_id[row["last_event"]]["surface_id"])

    def test_terminal_flag_agrees_with_the_lifecycle(self) -> None:
        for row in self.rows:
            with self.subTest(row["last_event"]):
                self.assertEqual(
                    row["state_is_terminal"] == "true",
                    row["lifecycle"] in build.TERMINAL_LIFECYCLES,
                )

    def test_named_event_is_the_latest_for_that_pair(self) -> None:
        platforms = build.load_validated(build.PLATFORMS_PATH, build.PLATFORMS_SCHEMA_PATH)
        groups = build.rename_groups(platforms)
        by_id = {e["id"]: e for e in self.events["events"]}
        for row in self.rows:
            with self.subTest(f'{row["model_id"]}/{row["surface_id"]}'):
                named = by_id[row["last_event"]]
                latest = max(
                    (
                        e for e in self.events["events"]
                        if e["kind"] == "availability"
                        and row["model_id"] in e["model_ids"]
                        and groups[e["surface_id"]] == groups[row["surface_id"]]
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
