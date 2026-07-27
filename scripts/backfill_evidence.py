#!/usr/bin/env python3
"""One-shot P1 backfill of evidence granularity.

Adds `confidence_detail` to events whose parts differ in evidential strength,
classifies every source with a `source_type`, and records `supports` where a
source underwrites a specific part of a claim rather than the whole record.

Run once, review the diff, then delete.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from migrate_v3 import emit_backlog, emit_event

ROOT = Path(__file__).resolve().parents[1]

# Which part of each soft claim is actually soft. In most cases the model
# attribution is first-party and certain while the first date rests on
# retrospective documentation.
CONFIDENCE_DETAIL = {
    "m365-analyst-frontier-2025-04": {"model": "confirmed", "date": "supported"},
    "foundry-grok3-2025-05-19": {"model": "confirmed", "date": "supported"},
    "foundry-grok3-mini-2025-05-19": {"model": "confirmed", "date": "supported"},
    "studio-gpt4-1-default-2025-10": {"model": "confirmed", "date": "supported", "exposure": "confirmed"},
    "m365-anthropic-admin-control-2025-12-08": {"date": "supported"},
    "google-gemini3-6-flash-2026-07-21": {"model": "confirmed", "date": "supported"},
    "m365-openai-operated-policy-2026-07-24": {"date": "supported"},
    # Inverts the usual pattern: Anthropic dates the suspension precisely, but
    # that it reached Foundry rests on a later secondary report.
    "foundry-fable5-suspension-2026-06-12": {
        "model": "confirmed", "date": "confirmed", "lifecycle": "confirmed", "exposure": "supported",
    },
}

# Which source underwrites which part, where the sources differ.
SUPPORTS = {
    ("foundry-fable5-suspension-2026-06-12", "https://www.anthropic.com/news/fable-mythos-access"):
        ["date", "model", "lifecycle"],
    ("foundry-fable5-suspension-2026-06-12",
     "https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html"):
        ["exposure"],
    ("m365-anthropic-eu-apps-setting-2026-04-03",
     "https://learn.microsoft.com/en-us/microsoft-365/copilot/connect-to-ai-subprocessor"):
        ["date", "policy"],
    ("m365-anthropic-eu-apps-setting-2026-04-03",
     "https://learn.microsoft.com/en-us/microsoft-365/copilot/copilot-anthropic-apps"):
        ["policy"],
    ("foundry-opus5-availability-2026-07-24",
     "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/claude-opus-5-is-available-today-in-microsoft-foundry/4535068"):
        ["date", "model", "lifecycle"],
    ("foundry-opus5-availability-2026-07-24",
     "https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/claude-models"):
        ["exposure"],
    ("foundry-sonnet5-ga-2026-06-30",
     "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/claude-sonnet-5-is-now-generally-available-in-microsoft-foundry/4530737"):
        ["date", "model", "lifecycle"],
}


# Verbatim attesting sentences. These were previously carried in `note`,
# which is for commentary; `quote` is for the words the source actually uses.
QUOTES = {
    ("m365-anthropic-eu-apps-setting-2026-04-03",
     "https://learn.microsoft.com/en-us/microsoft-365/copilot/connect-to-ai-subprocessor"):
        "On April 3, 2026, Microsoft introduced a new Microsoft 365 admin center setting "
        "Copilot in M365 apps with Anthropic models in EU/EFTA and UK to enable Anthropic as "
        "the default model for Copilot in Microsoft 365 apps.",
    ("foundry-fable5-suspension-2026-06-12", "https://www.anthropic.com/news/fable-mythos-access"):
        "The net effect of this order is that we must abruptly disable Fable 5 and Mythos 5 "
        "for all our customers.",
    ("foundry-fable5-suspension-2026-06-12",
     "https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html"):
        "Anthropic will also re-enable access to Fable 5 on Amazon Web Services, Google Cloud "
        "and Microsoft Foundry as soon as possible.",
    ("anthropic-fable5-restoration-2026-07-01",
     "https://www.cnbc.com/2026/06/30/anthropic-says-trump-admin-has-lifted-export-controls-on-claude-fable-5-and-mythos-5.html"):
        "Anthropic also said it has restored access to Mythos 5 for some U.S. organizations, "
        "following government approval granted on June 26.",
    ("foundry-opus5-availability-2026-07-24",
     "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/claude-opus-5-is-available-today-in-microsoft-foundry/4535068"):
        "Claude Opus 5 is Zero Data Retention compatible.",
    ("foundry-sonnet5-ga-2026-06-30",
     "https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/claude-sonnet-5-is-now-generally-available-in-microsoft-foundry/4530737"):
        "On June 29, 2026, we announced the general availability of Claude in Microsoft Foundry, "
        "giving enterprises a production-ready path to build with Claude models in the Azure "
        "ecosystem. Today, we're continuing that momentum with the general availability of "
        "Claude Sonnet 5 in Microsoft Foundry.",
}


def classify(url: str, publisher: str) -> str:
    """Infer source_type from the URL shape. Deliberately conservative."""
    if "learn.microsoft.com" in url or "/docs/" in url or "developers.googleblog" in url:
        return "documentation"
    if "/changelog/" in url:
        return "changelog"
    if "release-notes" in url or "whats-new" in url or "release-planner" in url:
        return "release_notes"
    if publisher in {"CNBC", "Fortune", "Reuters", "The Verge", "Bloomberg"}:
        return "news"
    if any(host in url for host in (
        "openai.com", "anthropic.com", "blogs.microsoft.com", "azure.microsoft.com",
        "techcommunity.microsoft.com", "github.blog", "ai.meta.com", "x.ai",
        "deepseek.com", "mistral.ai", "moonshot", "blog.google", "microsoft.com/en-us/microsoft-365",
    )):
        return "announcement"
    return "other"


def main() -> None:
    path = ROOT / "data/events.yaml"
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    detailed = typed = supported = quoted = 0
    for event in data["events"]:
        if event["id"] in CONFIDENCE_DETAIL:
            event["confidence_detail"] = CONFIDENCE_DETAIL[event["id"]]
            detailed += 1
        for source in event["sources"]:
            if "source_type" not in source:
                source["source_type"] = classify(source["url"], source["publisher"])
                typed += 1
            key = (event["id"], source["url"])
            if key in SUPPORTS:
                source["supports"] = SUPPORTS[key]
                supported += 1
            if key in QUOTES:
                source["quote"] = QUOTES[key]
                # the note was a stand-in for the quote; drop it if it merely
                # paraphrased what the quote now states verbatim
                if source.get("note", "").startswith(("States", "Records", "Opens", "Reports")):
                    source.pop("note", None)
                quoted += 1

    for item in data["validation_backlog"]:
        for source in item.get("sources", []):
            if "source_type" not in source:
                source["source_type"] = classify(source["url"], source["publisher"])
                typed += 1

    lines: list[str] = [text.split("\nevents:\n")[0], "events:"]
    for event in data["events"]:
        emit_event(event, lines)
    lines.append("validation_backlog:")
    for item in data["validation_backlog"]:
        emit_backlog(item, lines)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"{detailed} events given confidence_detail, {typed} sources classified, "
          f"{supported} sources given supports, {quoted} sources given a verbatim quote")


if __name__ == "__main__":
    main()
