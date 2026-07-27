#!/usr/bin/env python3
"""One-shot P1 backfill of the validation backlog.

Adds `state`, `model_ids` and `surface_ids` to every backlog item, merges a
duplicate introduced during the v3 migration, and restores the three items
that were deleted in earlier rounds when they were resolved. A resolved
question should stay on the record as `promoted`, not vanish, so it is not
reopened and answered differently later.

Run once, review the diff, then delete.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from migrate_v3 import emit_backlog, emit_event, q

ROOT = Path(__file__).resolve().parents[1]

# id -> (model_ids, surface_ids)
TARGETS: dict[str, tuple[list[str], list[str]]] = {
    "azure-chatgpt-preview-2023-03-09": (["gpt-3-5"], ["azure-openai"]),
    "azure-gpt4-turbo-first-availability-2023": (["gpt-4-turbo"], ["azure-openai"]),
    "deepseek-r1-vendor-2025-01-20": (["deepseek-r1"], ["deepseek"]),
    "deepseek-v3-first-microsoft-availability-2024": (["deepseek-v3"], []),
    "deepseek-v3-vendor-2024-12-26": (["deepseek-v3"], ["deepseek"]),
    "foundry-fable5-restoration-2026": (["claude-fable-5"], ["microsoft-foundry"]),
    "foundry-gpt5-5-first-availability-2026-04-24": (["gpt-5-5"], ["microsoft-foundry"]),
    "foundry-kimi-k2-7-first-availability-2026-07": (["kimi-k2-7-code"], ["microsoft-foundry"]),
    "foundry-o3-o4-mini-2025-04-16": (["o3", "o4-mini"], ["azure-ai-foundry"]),
    "foundry-opus4-5-first-availability-2025-11-24": (["claude-opus-4-5"], ["microsoft-foundry"]),
    "gemini1-5-pro-public-preview-ga-2024": (["gemini-1-5-pro"], ["google-gemini"]),
    "github-copilot-chat-gpt3-5-start-2023": (["gpt-3-5"], ["github-copilot"]),
    "github-copilot-chat-gpt4-transition-2023-11": (["gpt-4"], ["github-copilot"]),
    "github-foundry-opus4-7-2026-04-16": (["claude-opus-4-7"], ["github-copilot", "microsoft-foundry"]),
    "github-gemini1-5-pro-first-picker-date-2024": (["gemini-1-5-pro"], ["github-copilot"]),
    "github-gpt4-1-first-availability-2025": (["gpt-4-1"], ["github-copilot", "github-models"]),
    "github-o3-mini-claude3-7-ga-2025-04-04": (["o3-mini", "claude-3-7-sonnet"], ["github-copilot"]),
    "github-opus4-5-preview-ga-2025": (["claude-opus-4-5"], ["github-copilot"]),
    "google-gemini2-5-pro-github-2025-04-11": (["gemini-2-5-pro"], ["github-copilot"]),
    "gpt5-6-copilot-studio-2026": (["gpt-5-6-sol", "gpt-5-6-terra", "gpt-5-6-luna"], ["copilot-studio"]),
    "kimi-k2-7-vendor-release-2026": (["kimi-k2-7-code"], ["moonshot"]),
    "m365-gpt5-1-first-availability-2025": (["gpt-5-1"], ["m365-copilot"]),
    "m365-o1-first-availability-2024": (["o1"], ["m365-copilot"]),
    "m365-opus4-7-core-chat-picker-2026-05": (["claude-opus-4-7"], ["m365-copilot"]),
    "m365-researcher-first-availability-2025": (["openai-deep-research"], ["m365-copilot"]),
    "meta-cohere-flux-mai-foundry-history": ([], ["microsoft-foundry"]),
    "microsoft-foundry-branding-2025-11-18": ([], ["microsoft-foundry"]),
    "openai-codex-public-release-2021-08-10": (["codex"], ["openai"]),
    "openai-gpt5-1-vendor-2025-11": (["gpt-5-1"], ["openai", "openai-api"]),
    "openai-o3-o4mini-vendor-2025-04-16": (["o3", "o4-mini"], ["openai"]),
    "opus5-m365-studio-2026-07-24": (["claude-opus-5"], ["m365-copilot", "copilot-studio"]),
    "studio-gpt4-1-first-availability-2025": (["gpt-4-1"], ["copilot-studio"]),
    "studio-gpt4o-default-2024-09": (["gpt-4o"], ["copilot-studio"]),
    "studio-sonnet5-first-date-2026": (["claude-sonnet-5"], ["copilot-studio"]),
    "xai-github-copilot-picker": (["grok-3", "grok-4"], ["github-copilot"]),
}

# The v3 migration added a Gemini 1.5 Pro item without noticing an equivalent
# question already existed. Keep the original id and fold in the new reason.
DROP = {"github-gemini-1-5-pro-first-availability-2024"}

MERGE_REASON = {
    "github-gemini1-5-pro-first-picker-date-2024":
        "The 29 October 2024 GitHub Universe keynote is recorded as an announcement rather than "
        "availability, because treating it as availability placed a GA before a later public "
        "preview on the same surface. That leaves Gemini 1.5 Pro with no GitHub Copilot "
        "availability date at all.",
}

# Questions resolved in earlier rounds. They were deleted at the time; a
# promoted item belongs on the record so the question is not reopened.
RESTORED = [
    {
        "id": "m365-anthropic-eu-setting-2026-04",
        "state": "promoted",
        "working_claim": "A new EU/EFTA/UK Anthropic admin setting arrived around early April 2026.",
        "reason": "Current Microsoft Learn documentation proved the setting and the 1 May transition, but the 3 April date was not revalidated at import time.",
        "target": "Use Microsoft Learn page history or Message Center evidence to establish the exact date.",
        "model_ids": [],
        "surface_ids": ["m365-admin"],
        "resolution": "Microsoft Learn states the date verbatim: 'On April 3, 2026, Microsoft introduced a new Microsoft 365 admin center setting Copilot in M365 apps with Anthropic models in EU/EFTA and UK.'",
        "resolved_on": "2026-07-27",
        "promoted_to": "m365-anthropic-eu-apps-setting-2026-04-03",
    },
    {
        "id": "foundry-sonnet5-2026-06-30",
        "state": "promoted",
        "working_claim": "Claude Sonnet 5 was available through Foundry around its 30 June release.",
        "reason": "Likely after Claude Foundry GA on 29 June, but current catalogue presence did not prove the first date.",
        "target": "Locate a dated Microsoft Foundry Sonnet 5 release record.",
        "model_ids": ["claude-sonnet-5"],
        "surface_ids": ["microsoft-foundry"],
        "resolution": "Microsoft's Foundry announcement carries a 30 June 2026 publication date and opens by referring back to the 29 June Claude GA post, which pins the date.",
        "resolved_on": "2026-07-27",
        "promoted_to": "foundry-sonnet5-ga-2026-06-30",
    },
    {
        "id": "foundry-fable5-suspension-2026",
        "state": "promoted",
        "working_claim": "Fable 5 availability in Microsoft Foundry was suspended alongside the vendor-level action on 12 June 2026.",
        "reason": "Anthropic's directive statement is global and does not name Foundry, so Microsoft-side evidence was required before recording a Foundry state change.",
        "target": "Locate dated Microsoft Foundry suspension evidence.",
        "model_ids": ["claude-fable-5"],
        "surface_ids": ["microsoft-foundry"],
        "resolution": "CNBC's report that Anthropic would re-enable Fable 5 'on Amazon Web Services, Google Cloud and Microsoft Foundry' establishes retrospectively that Foundry distribution had been suspended. Promoted at 'supported' confidence because no Microsoft-issued notice exists. The restoration half remains open as foundry-fable5-restoration-2026.",
        "resolved_on": "2026-07-27",
        "promoted_to": "foundry-fable5-suspension-2026-06-12",
    },
]


def main() -> None:
    path = ROOT / "data/events.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    backlog = []
    for item in data["validation_backlog"]:
        if item["id"] in DROP:
            continue
        item.setdefault("state", "open")
        if item["id"] in MERGE_REASON:
            item["reason"] = f"{item['reason']} {MERGE_REASON[item['id']]}"
        if item["id"] in TARGETS:
            model_ids, surface_ids = TARGETS[item["id"]]
            item["model_ids"] = model_ids
            if surface_ids:
                item["surface_ids"] = surface_ids
            else:
                item.pop("surface_ids", None)
        item.pop("surface_id", None)
        backlog.append(item)

    backlog.extend(RESTORED)
    backlog.sort(key=lambda i: i["id"])

    lines: list[str] = []
    text = path.read_text(encoding="utf-8")
    head = text.split("\nvalidation_backlog:\n")[0]
    lines.append(head)
    lines.append("validation_backlog:")
    for item in backlog:
        emit_backlog(item, lines)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"backfilled {len(backlog)} backlog items "
          f"({sum(1 for b in backlog if b['state'] == 'promoted')} promoted, "
          f"{sum(1 for b in backlog if b['state'] == 'open')} open)")


if __name__ == "__main__":
    main()
