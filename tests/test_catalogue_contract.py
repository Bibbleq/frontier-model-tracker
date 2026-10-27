"""The catalogue contract: file shapes the catalogue watcher writes to.

The schemas and the lifecycle mapping are owned by this repository. These
tests guard the shapes, their published identifiers and the vocabulary table
the watcher and the replay both read.
"""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts import build

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schema"
FIXTURES = ROOT / "tests" / "fixtures" / "catalogue"

OBSERVATION = "observation.schema.json"
CHECKPOINT = "checkpoint.schema.json"
MAPPING = "lifecycle-mapping.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class CatalogueSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {name: load(SCHEMA / name) for name in (OBSERVATION, CHECKPOINT)}
        cls.validators = {name: Draft202012Validator(schema) for name, schema in cls.schemas.items()}
        cls.observation = load(FIXTURES / "observation.example.json")
        cls.checkpoint = load(FIXTURES / "checkpoint.example.json")

    def test_schemas_are_valid_draft_2020_12(self) -> None:
        for schema in self.schemas.values():
            Draft202012Validator.check_schema(schema)

    def test_schema_ids_are_their_published_urls(self) -> None:
        for name, schema in self.schemas.items():
            self.assertEqual(schema["$id"], build.BASE_URL + "schema/" + name)

    def test_fixtures_validate(self) -> None:
        self.validators[OBSERVATION].validate(self.observation)
        self.validators[CHECKPOINT].validate(self.checkpoint)

    def test_observation_fixture_keys_present_matches_its_changes(self) -> None:
        keys = set(self.observation["keys_present"])
        for change in self.observation["changes"]:
            if change["kind"] == "last_seen_absent":
                self.assertNotIn(change["model_key"], keys)
            else:
                self.assertIn(change["model_key"], keys)

    def test_observation_without_changes_is_rejected(self) -> None:
        document = copy.deepcopy(self.observation)
        document["changes"] = []
        self.assertFalse(self.validators[OBSERVATION].is_valid(document))

    def test_unknown_change_kind_is_rejected(self) -> None:
        document = copy.deepcopy(self.observation)
        document["changes"][0]["kind"] = "reappeared"
        self.assertFalse(self.validators[OBSERVATION].is_valid(document))

    def test_unknown_checkpoint_kind_is_rejected(self) -> None:
        document = copy.deepcopy(self.checkpoint)
        document["kind"] = "weekly"
        self.assertFalse(self.validators[CHECKPOINT].is_valid(document))

    def test_extra_root_property_is_rejected(self) -> None:
        for name, fixture in ((OBSERVATION, self.observation), (CHECKPOINT, self.checkpoint)):
            document = copy.deepcopy(fixture)
            document["surprise"] = True
            self.assertFalse(self.validators[name].is_valid(document), name)

    def test_observation_requires_a_checkpoint(self) -> None:
        document = copy.deepcopy(self.observation)
        document["checkpoint"] = None
        self.assertFalse(self.validators[OBSERVATION].is_valid(document))

    def test_first_file_after_a_checkpoint_may_have_no_previous_file(self) -> None:
        document = copy.deepcopy(self.observation)
        document["previous_file"] = None
        self.validators[OBSERVATION].validate(document)

    def test_timestamps_must_be_utc(self) -> None:
        document = copy.deepcopy(self.observation)
        document["observed_at"] = "2026-10-27T12:30:44+01:00"
        self.assertFalse(self.validators[OBSERVATION].is_valid(document))

    def test_model_key_keeps_the_api_spelling(self) -> None:
        document = copy.deepcopy(self.observation)
        document["keys_present"].append("Muse-Glimmer-30B@1")
        self.validators[OBSERVATION].validate(document)
        document["keys_present"].append("no-version")
        self.assertFalse(self.validators[OBSERVATION].is_valid(document))


class LifecycleMappingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mapping = load(SCHEMA / MAPPING)
        events = load(SCHEMA / "events.schema.json")
        cls.dataset_lifecycles = set(events["$defs"]["event"]["properties"]["lifecycle"]["enum"])

    def test_mapping_loads_at_version_one(self) -> None:
        self.assertEqual(self.mapping["schema_version"], 1)
        self.assertTrue(self.mapping["api_to_portal"])

    def test_dataset_lifecycle_values_exist_in_the_dataset_enum(self) -> None:
        for api_value, row in self.mapping["api_to_portal"].items():
            lifecycle = row["dataset_lifecycle"]
            if lifecycle is not None:
                self.assertIn(lifecycle, self.dataset_lifecycles, api_value)

    def test_mapped_is_false_exactly_where_there_is_no_portal_word(self) -> None:
        for api_value, row in self.mapping["api_to_portal"].items():
            self.assertEqual(row["mapped"], row["portal"] is not None, api_value)
            self.assertEqual(row["mapped"], row["dataset_lifecycle"] is not None, api_value)

    def test_every_rule_names_its_source_quote(self) -> None:
        for rule in self.mapping["rules"]:
            self.assertTrue(rule["id"])
            self.assertTrue(rule["statement"])
            self.assertTrue(rule["source_quote"])


if __name__ == "__main__":
    unittest.main()
