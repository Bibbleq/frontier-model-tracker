"""The published data contract is a promise to consumers in other repositories.

These tests guard the parts a display layer depends on. A change that breaks
one of them is a breaking change under docs/data-contract.md and needs a
version bump, not a green build.
"""
from __future__ import annotations

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
            "deprecated", "retired", "suspended", "restored",
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


if __name__ == "__main__":
    unittest.main()
