from __future__ import annotations

import copy
import unittest

from scripts import build


def availability(event_id: str, day: str, lifecycle: str, *, surface: str = "surface", model: str = "model") -> dict:
    return {
        "id": event_id,
        "kind": "availability",
        "date": {"start": day, "precision": "day"},
        "surface_id": surface,
        "model_ids": [model],
        "lifecycle": lifecycle,
        "exposure": "selectable",
    }


class DateIntervalTests(unittest.TestCase):
    def test_month_precision_is_an_interval(self) -> None:
        low, high = build.date_interval({"start": "2024-02", "precision": "month"})
        self.assertEqual(low.isoformat(), "2024-02-01")
        self.assertEqual(high.isoformat(), "2024-02-29")

    def test_explicit_end_extends_interval(self) -> None:
        low, high = build.date_interval({"start": "2024-02", "end": "2024-03", "precision": "month"})
        self.assertEqual(low.isoformat(), "2024-02-01")
        self.assertEqual(high.isoformat(), "2024-03-31")


class EventInvariantTests(unittest.TestCase):
    def test_lifecycle_cannot_regress_after_ga(self) -> None:
        events = [
            availability("preview", "2025-01-01", "public_preview"),
            availability("ga", "2025-02-01", "ga"),
            availability("late-preview", "2025-03-01", "limited_preview"),
        ]
        with self.assertRaises(SystemExit):
            build.check_lifecycle_ordering(events)

    def test_restoration_must_follow_suspension(self) -> None:
        events = [
            availability("suspended", "2025-01-01", "suspended"),
            availability("restored", "2025-01-01", "restored"),
        ]
        with self.assertRaises(SystemExit):
            build.check_suspension_pairs(events)

    def test_relation_cycles_are_rejected(self) -> None:
        first = availability("first", "2025-01-01", "ga")
        second = availability("second", "2025-01-01", "ga")
        first["relations"] = [{"type": "part_of", "target": "second"}]
        second["relations"] = [{"type": "part_of", "target": "first"}]
        with self.assertRaises(SystemExit):
            build.check_relations([first, second])


class RegistryInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.models, cls.platforms = build.validate_registries()

    def test_current_registries_pass(self) -> None:
        build.validate_registry_semantics(copy.deepcopy(self.models), copy.deepcopy(self.platforms))

    def test_aliases_must_be_unique_across_models(self) -> None:
        models = copy.deepcopy(self.models)
        models["models"][1].setdefault("aliases", []).append(models["models"][0]["display_name"])
        with self.assertRaises(SystemExit):
            build.validate_registry_semantics(models, copy.deepcopy(self.platforms))

    def test_surface_rename_cycles_are_rejected(self) -> None:
        platforms = copy.deepcopy(self.platforms)
        first, second = platforms["surfaces"][:2]
        first["renamed_to"] = second["id"]
        second["renamed_to"] = first["id"]
        with self.assertRaises(SystemExit):
            build.validate_registry_semantics(copy.deepcopy(self.models), platforms)


class DatasetContractTests(unittest.TestCase):
    def test_readme_count_matches_dataset(self) -> None:
        build.validate_documented_counts(build.load())

    def test_open_backlog_suppresses_missing_lag(self) -> None:
        models = {"models": [{"id": "model", "display_name": "Model", "vendor": "Vendor"}]}
        platforms = {
            "surfaces": [
                {"id": "vendor", "display_name": "Vendor", "vendor_baseline": True, "counts_as": []},
                {"id": "product", "display_name": "Product", "counts_as": ["microsoft"]},
            ]
        }
        baseline = availability("vendor-release", "2025-01-01", "ga", surface="vendor")
        data = {
            "events": [baseline],
            "validation_backlog": [
                {"id": "question", "state": "open", "model_ids": ["model"], "surface_ids": ["product"]}
            ],
        }
        rows = build.derive_lag(data, models, platforms)
        microsoft = [row for row in rows if row["tier"] == "microsoft"]
        self.assertTrue(microsoft)
        self.assertTrue(all(row["certainty"] == "unknown_open_research" for row in microsoft))


if __name__ == "__main__":
    unittest.main()
