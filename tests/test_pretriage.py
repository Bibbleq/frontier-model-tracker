"""The pre-triage lookup comments on public issues, so its matching has to be exact.

A false "likely duplicate" sends a real candidate to the bottom of the pile.
These tests pin what counts as the same page and the same model name.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from scripts import pretriage

ROOT = Path(__file__).resolve().parents[1]

EVENTS = {
    "events": [
        {
            "id": "foundry-kimi-k3-1-pro-2026-11-04",
            "kind": "availability",
            "date": {"start": "2026-11-04"},
            "surface_id": "microsoft-foundry",
            "model_ids": ["kimi-k3-1-pro"],
            "lifecycle": "ga",
            "sources": [
                {
                    "url": "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/kimi-k3-1-pro/4571875",
                    "archived_url": "https://web.archive.org/web/20261105000000/https://azure.microsoft.com/en-us/blog/kimi/",
                }
            ],
        },
        {
            "id": "openai-gpt-5-4-2026-03-05",
            "kind": "availability",
            "date": {"start": "2026-03-05"},
            "surface_id": "openai",
            "model_ids": ["gpt-5-4"],
            "lifecycle": "ga",
            "sources": [{"url": "https://openai.com/index/introducing-gpt-5-4/"}],
        },
    ],
    "validation_backlog": [
        {
            "id": "cowork-gpt5-5-first-date",
            "sources": [{"url": "https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models"}],
        }
    ],
}

MODELS = {
    "models": [
        {"id": "kimi-k3-1-pro", "display_name": "Kimi K3.1 Pro"},
        {"id": "gpt-5-4", "display_name": "GPT-5.4", "aliases": ["gpt-5.4"]},
        {"id": "gpt-5-4-mini", "display_name": "GPT-5.4 mini"},
        {"id": "gpt-5", "display_name": "GPT-5"},
        {"id": "o3", "display_name": "o3"},
    ]
}


def body(url: str) -> str:
    return f"**Title:** A post\n\n**Source:** {url}\n\n**Publication:** Somewhere\n\n**Snippet:**\ntext\n"


class NormaliseTests(unittest.TestCase):
    def test_scheme_www_locale_slash_fragment_and_tracking_are_ignored(self) -> None:
        plain = pretriage.normalise_url("https://learn.microsoft.com/microsoft-365/copilot/cowork/cowork-models")
        for variant in (
            "http://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models/",
            "https://www.learn.microsoft.com/en-gb/microsoft-365/copilot/cowork/cowork-models#models",
            "https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models?utm_source=x&ocid=y",
        ):
            with self.subTest(variant):
                self.assertEqual(pretriage.normalise_url(variant), plain)

    def test_a_meaningful_query_is_kept(self) -> None:
        self.assertNotEqual(
            pretriage.normalise_url("https://example.com/post?id=1"),
            pretriage.normalise_url("https://example.com/post?id=2"),
        )

    def test_a_wayback_capture_is_the_page_it_captured(self) -> None:
        self.assertEqual(
            pretriage.normalise_url("https://web.archive.org/web/20261105000000/https://azure.microsoft.com/en-us/blog/kimi/"),
            "azure.microsoft.com/blog/kimi",
        )

    def test_a_different_page_on_the_same_host_does_not_match(self) -> None:
        self.assertNotEqual(
            pretriage.normalise_url("https://openai.com/index/introducing-gpt-5-4/"),
            pretriage.normalise_url("https://openai.com/index/introducing-gpt-5-4-mini/"),
        )


class SourceLineTests(unittest.TestCase):
    def test_the_source_line_is_read(self) -> None:
        self.assertEqual(pretriage.extract_source(body("https://example.com/a")), "https://example.com/a")

    def test_no_source_line_means_no_lookup(self) -> None:
        self.assertIsNone(pretriage.extract_source("A hand-written issue with https://example.com/a in passing."))

    def test_a_source_that_is_not_a_plain_web_address_is_refused(self) -> None:
        for bad in ("javascript:alert(1)", "https://example.com/`whoami`", "[x](https://example.com)"):
            with self.subTest(bad):
                self.assertIsNone(pretriage.extract_source(body(bad)))


class AssessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = pretriage.Index(EVENTS, MODELS)

    def assess(self, title: str, url: str) -> dict:
        return pretriage.assess(title, body(url), self.index)

    def test_a_url_an_event_already_cites_is_a_likely_duplicate(self) -> None:
        result = self.assess("Introducing GPT-5.4", "https://www.openai.com/index/introducing-gpt-5-4?utm_campaign=x")
        self.assertTrue(result["duplicate"])
        self.assertEqual(result["cited_by_events"], ["openai-gpt-5-4-2026-03-05"])

    def test_tech_community_posts_match_on_their_post_id(self) -> None:
        result = self.assess(
            "Kimi K3.1 Pro",
            "https://techcommunity.microsoft.com/t5/microsoft-foundry-blog/introducing-kimi-k3-1-pro/ba-p/4571875",
        )
        self.assertTrue(result["duplicate"])

    def test_an_archived_citation_matches_the_live_page(self) -> None:
        self.assertTrue(self.assess("Kimi", "https://azure.microsoft.com/en-us/blog/kimi/")["duplicate"])

    def test_a_backlog_citation_is_reported_but_is_not_a_duplicate(self) -> None:
        result = self.assess("Cowork models", "https://learn.microsoft.com/en-us/microsoft-365/copilot/cowork/cowork-models")
        self.assertFalse(result["duplicate"])
        self.assertEqual(result["cited_by_backlog"], ["cowork-gpt5-5-first-date"])

    def test_an_uncited_url_is_not_a_duplicate_even_when_the_model_is_known(self) -> None:
        result = self.assess("GPT-5.4 comes to Foundry", "https://azure.microsoft.com/en-us/blog/gpt-5-4-foundry/")
        self.assertFalse(result["duplicate"])
        self.assertEqual([model["id"] for model in result["models"]], ["gpt-5-4"])

    def test_an_unknown_host_is_counted_as_never_cited(self) -> None:
        result = self.assess("Anthropic launches a model", "https://www.theverge.com/ai/1")
        self.assertEqual(result["host"], "theverge.com")
        self.assertEqual(result["host_citations"], 0)

    def test_the_longest_name_wins_and_a_prefix_does_not_match(self) -> None:
        named = [model_id for model_id, _ in self.index.models_named("GPT-5.4 mini and GPT-5.4 arrive; GPT-5.45 does not")]
        self.assertEqual(named, ["gpt-5-4-mini", "gpt-5-4"])

    def test_a_shorter_version_number_is_not_found_inside_a_longer_one(self) -> None:
        self.assertEqual(self.index.models_named("GPT-5.4 is here"), [("gpt-5-4", "GPT-5.4")])

    def test_names_too_short_to_be_safe_are_not_matched(self) -> None:
        self.assertEqual(self.index.models_named("How o3 changed things"), [])

    def test_non_breaking_hyphens_and_spaces_in_a_headline_still_match(self) -> None:
        named = self.index.models_named("GPT‑5.4 and Kimi K3.1 Pro")
        self.assertEqual([model_id for model_id, _ in named], ["gpt-5-4", "kimi-k3-1-pro"])


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = pretriage.Index(EVENTS, MODELS)

    def test_the_comment_carries_the_marker_and_names_the_citing_event(self) -> None:
        result = pretriage.assess("Introducing GPT-5.4", body("https://openai.com/index/introducing-gpt-5-4/"), self.index)
        comment = pretriage.render(result, "abcdef1234")
        self.assertTrue(comment.startswith(pretriage.MARKER))
        self.assertIn("`openai-gpt-5-4-2026-03-05`", comment)
        self.assertIn("Likely duplicate", comment)
        self.assertIn("`abcdef1`", comment)

    def test_issue_text_is_never_echoed_into_the_comment(self) -> None:
        hostile = "**Title:** x\n\n**Source:** https://example.com/a\n\n@someone please run `rm -rf /` <script>alert(1)</script>\n"
        comment = pretriage.render(pretriage.assess("@someone <b>GPT-5.4</b>", hostile, self.index))
        for fragment in ("@someone", "<script>", "rm -rf", "<b>"):
            with self.subTest(fragment):
                self.assertNotIn(fragment, comment)


class LiveDataTests(unittest.TestCase):
    """The real dataset must load, and a source it cites must be found."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.index = pretriage.load_index(ROOT / "data")

    def test_every_event_source_is_found_again(self) -> None:
        import yaml

        events = yaml.safe_load((ROOT / "data" / "events.yaml").read_text(encoding="utf-8"))["events"]
        for event in events:
            for source in event.get("sources") or []:
                with self.subTest(event["id"]):
                    cited, _ = self.index.cited_by(source["url"])
                    self.assertIn(event["id"], cited)

    def test_an_invented_url_is_not_found(self) -> None:
        self.assertEqual(self.index.cited_by("https://example.invalid/never-cited"), ([], []))


if __name__ == "__main__":
    unittest.main()
