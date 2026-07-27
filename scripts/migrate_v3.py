#!/usr/bin/env python3
"""One-shot migration of data/events.yaml from schema v2 to schema v3.

v2 encoded event semantics in four partly-overlapping fields
(type / availability / scope / selectable) plus free-text model and platform
strings. v3 replaces those with three orthogonal axes (kind / lifecycle /
exposure) and registry references (model_ids / surface_id / experience_ids).

Every decision is an explicit table entry rather than a heuristic, so the
migration is reviewable. Run once, review the diff, then delete this script.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# --------------------------------------------------------------------------
# kind: is this an availability fact at all?
# Keyed by event id where the answer is not "availability".
# --------------------------------------------------------------------------
KIND_OVERRIDE = {
    # Announcements of future availability. These must never enter lag maths.
    "m365-o1-announced-2024-09-16": "announcement",
    "m365-analyst-announced-2025-03-25": "announcement",
    "m365-researcher-announced-2025-03-25": "announcement",
    # GitHub Universe keynote announcing multi-model choice. Individual models
    # arrived on their own dates; treating this as availability made a "GA"
    # precede Claude 3.5 Sonnet's public preview three days later.
    "github-multimodel-announcement-2024-10-29": "announcement",
    # Product/strategy milestones, not model availability.
    "microsoft-openai-gpt3-license-2020-09-22": "milestone",
    "copilot-studio-launch-2023-11-15": "milestone",
    "azure-ai-studio-preview-2023-11-15": "milestone",
    "azure-ai-foundry-announced-2024-11-19": "milestone",
    "m365-wave3-frontier-2026-03-09": "milestone",
    "pva-generative-ai-preview-2023-03-06": "milestone",
}

# --------------------------------------------------------------------------
# lifecycle: where in the release cycle. Keyed by the v2 availability value,
# with per-type overrides where the same word meant different things.
# --------------------------------------------------------------------------
LIFECYCLE_BY_AVAILABILITY = {
    "release": "ga",
    "launch": "ga",
    "stable": "ga",
    "family_launch": "ga",
    "ga": "ga",
    "ga_rollout": "ga",
    "available": "ga",
    "production": "ga",
    "rollout": "ga",
    "announced_rollout": "ga",
    "business_enterprise": "ga",
    "frontier": "limited_preview",
    "frontier_rollout": "ga",
    "frontier_preview": "limited_preview",
    "early_release": "public_preview",
    "experimental": "public_preview",
    "beta": "public_preview",
    "preview": "public_preview",
    "public_preview": "public_preview",
    "technical_preview": "public_preview",
    "limited_preview": "limited_preview",
    "restricted_preview": "limited_preview",
    "invite_only_preview": "limited_preview",
    "waitlist": "limited_preview",
    "private_preview": "private_preview",
    "suspended": "suspended",
    "restored": "restored",
    "announced": "ga",  # only reached by events left as kind=availability
}

# --------------------------------------------------------------------------
# exposure: how the model is exposed on the surface. Keyed by v2 scope.
# --------------------------------------------------------------------------
EXPOSURE_BY_SCOPE = {
    "model_picker": "selectable",
    "default_model": "default",
    "catalogue_availability": "catalogue",
    "underlying_model": "underlying",
    "embedded_agent": "specialist",
    "experience_availability": "specialist",
    "availability_state": None,  # resolved per event below
    "platform_availability": "catalogue",
    "product_availability": "underlying",
    "product_strategy": "not_applicable",
    "governance": "not_applicable",
    "announced_future_availability": "not_applicable",
}

# experience_availability with a model picker really is selection, not a
# specialist embedded agent.
EXPOSURE_OVERRIDE = {
    "m365-gpt5-6-2026-07-09": "selectable",
    "m365-researcher-opus4-1-2025-09-24": "selectable",
    "m365-opus4-7-2026-04-16": "selectable",
    "m365-opus4-8-2026-05-28": "selectable",
    "m365-fable5-preview-2026-06-10": "selectable",
    "m365-sonnet5-2026-07-02": "selectable",
    # suspension/restoration inherit the exposure of what was suspended
    "anthropic-fable5-suspension-2026-06-12": "catalogue",
    "anthropic-fable5-restoration-2026-07-01": "catalogue",
    "github-fable5-suspension-2026-06-12": "selectable",
    "github-fable5-restoration-2026-07-01": "selectable",
    "foundry-fable5-suspension-2026-06-12": "catalogue",
    # product GA events: the model is underlying the product
    "github-copilot-ga-2022-06-21": "underlying",
    "m365-copilot-ga-2023-11-01": "underlying",
    "claude-foundry-ga-2026-06-29": "catalogue",
}

# --------------------------------------------------------------------------
# surfaces: (family, product) -> surface id
# --------------------------------------------------------------------------
SURFACE = {
    ("Vendor", "OpenAI"): "openai",
    ("Vendor", "OpenAI API"): "openai-api",
    ("Vendor", "ChatGPT"): "chatgpt",
    ("Vendor", "Claude"): "anthropic-claude",
    ("Vendor", "Gemini"): "google-gemini",
    ("Vendor", "Gemini API"): "google-gemini-api",
    ("Vendor", "Mistral"): "mistral",
    ("Vendor", "Grok"): "xai-grok",
    ("Microsoft 365", "Microsoft 365 Copilot"): "m365-copilot",
    ("Microsoft 365", "Microsoft 365 admin"): "m365-admin",
    ("Copilot Studio", "Microsoft Copilot Studio"): "copilot-studio",
    ("Copilot Studio", "Power Virtual Agents"): "power-virtual-agents",
    ("GitHub Copilot", "GitHub Copilot"): "github-copilot",
    ("GitHub Models", "GitHub Models"): "github-models",
    ("Microsoft Foundry", "Azure OpenAI Service"): "azure-openai",
    ("Microsoft Foundry", "Azure AI Studio"): "azure-ai-studio",
    ("Microsoft Foundry", "Azure AI Foundry"): "azure-ai-foundry",
    ("Microsoft Foundry", "Microsoft Foundry"): "microsoft-foundry",
    ("Microsoft Foundry", "Azure"): "azure-ai-catalog",
    ("Microsoft Foundry", "Azure AI Studio / Azure OpenAI"): "azure-openai",
    ("Microsoft", "Microsoft/OpenAI partnership"): "microsoft-corporate",
}

# --------------------------------------------------------------------------
# experiences: free-text -> controlled ids (a list, because several
# announcements covered more than one experience at once)
# --------------------------------------------------------------------------
EXPERIENCES = {
    "Analyst": ["analyst"],
    "Researcher": ["researcher"],
    # Every bare "Copilot Chat" in the v2 data sits on a GitHub Copilot event.
    "Copilot Chat": ["github-copilot-chat"],
    "Quick response": ["quick-response"],
    "Think deeper": ["think-deeper"],
    "code_completion": ["code-completion"],
    "conversation_booster": ["conversation-booster"],
    "Copilot Cowork / Excel": ["cowork", "excel"],
    "Copilot Cowork / PowerPoint": ["cowork", "powerpoint"],
    "Cowork / Copilot Chat / Excel / PowerPoint": ["cowork", "m365-copilot-chat", "excel", "powerpoint"],
    "Cowork Frontier / Excel / PowerPoint": ["cowork", "excel", "powerpoint"],
    "Copilot in Microsoft 365 apps (Word / Excel / PowerPoint)": ["word", "excel", "powerpoint"],
    # model display names wrongly stored as experiences; resolved via aliases
    "GPT-5.3 Chat": [],
    "GPT-5.4 Reasoning": [],
    "GPT-5.5 Chat": [],
    "GPT-5.5 Reasoning": [],
}

# --------------------------------------------------------------------------
# model strings that name no model, or name a vendor-level target
# --------------------------------------------------------------------------
NO_MODEL = {
    "Azure AI Foundry", "Azure AI Studio", "Copilot Studio",
    "Azure OpenAI-backed generative AI", "Frontier model experiences",
}
VENDOR_TARGET = {
    "Claude models": "Anthropic",
    "OpenAI-operated models": "OpenAI",
}
FAMILY_STRINGS = {
    "GPT-3 family": (["gpt-3"], "family"),
    "GPT-3.5 generation": (["gpt-3-5"], "family"),
    "GPT-4 generation": (["gpt-4"], "family"),
    "GPT-4.1 family": (["gpt-4-1", "gpt-4-1-mini", "gpt-4-1-nano"], "family"),
    "GPT-5.6 family": (["gpt-5-6-sol", "gpt-5-6-terra", "gpt-5-6-luna"], "family"),
    "Claude 3 family": (["claude-3-opus", "claude-3-sonnet"], "family"),
}

# nuance lost when collapsing 30 availability values into 8 lifecycle values
CAVEAT_ADDITION = {
    "waitlist": "Access was gated behind a waitlist at this point.",
    "invite_only_preview": "Access was invite-only at this point.",
    "restricted_preview": "Access was restricted to selected customers at this point.",
    "experimental": "Published as an experimental model.",
    "early_release": "Published under GitHub's early-release programme.",
    "business_enterprise": "This event expanded availability to Business and Enterprise plans.",
    "frontier": "Delivered through the Microsoft 365 Copilot Frontier early-access programme.",
    "frontier_preview": "Delivered through the Microsoft 365 Copilot Frontier early-access programme.",
    "frontier_rollout": "Delivered through the Microsoft 365 Copilot Frontier programme.",
    "beta": "Published as a beta release.",
    "technical_preview": "Published as a technical preview.",
    "ga_rollout": "Generally available and rolling out progressively.",
    "announced_rollout": "Announced with a progressive rollout.",
    "policy_cutover": "A cutover of an existing policy rather than a new control.",
}

# Gaps the kind=availability/announcement split makes visible. Each of these
# was previously masked by an announcement standing in for an availability
# record; they are research questions, not timeline facts.
EXTRA_BACKLOG = [
    {
        "id": "github-gemini-1-5-pro-first-availability-2024",
        "state": "open",
        "working_claim": "Gemini 1.5 Pro became selectable in GitHub Copilot some time after the 29 October 2024 GitHub Universe multi-model announcement.",
        "reason": "The only record is the Universe keynote, which announced multi-model choice rather than dating each model's arrival. Reclassifying it as an announcement leaves this model with no GitHub Copilot availability date.",
        "target": "Find the dated GitHub changelog entry for Gemini 1.5 Pro reaching the Copilot model picker.",
        "model_ids": ["gemini-1-5-pro"],
        "surface_id": "github-copilot",
    },
    {
        "id": "m365-researcher-first-availability-2025",
        "state": "open",
        "working_claim": "Researcher reached general availability in Microsoft 365 Copilot on 2 June 2025, alongside Analyst.",
        "reason": "The 25 March 2025 record is an announcement, and the 2 June GA evidence note covers Researcher but the event itself is scoped to Analyst and o3-mini. Researcher has no availability event of its own.",
        "target": "Split a dedicated Researcher availability event once the model attribution and date are separately sourced.",
        "model_ids": ["openai-deep-research"],
        "surface_id": "m365-copilot",
    },
]

POLICY_REGIONS = {
    "m365-anthropic-eu-apps-setting-2026-04-03": ["EU", "EFTA", "UK"],
}

RELATION_MAP = {
    "vendor_release": "announced_by",
    "same_announcement": "announced_by",
    "replacement": "supersedes",
    "retirement": "supersedes",
    "other": "announced_by",
}


def build_alias_table() -> tuple[dict, dict]:
    models = yaml.safe_load((ROOT / "data/models.yaml").read_text(encoding="utf-8"))
    alias = {}
    for entry in models["models"]:
        alias[entry["display_name"]] = entry["id"]
        for name in entry.get("aliases", []):
            alias[name] = entry["id"]
    families = {}
    for entry in models["families"]:
        families[entry["display_name"]] = entry["id"]
    return alias, families


def resolve_models(event: dict, alias: dict) -> tuple[list[str], str | None, dict | None]:
    raw = event.get("models") or [event["model"]]
    single = event["model"]

    if single in NO_MODEL:
        return [], None, None
    if single in VENDOR_TARGET:
        return [], None, {"vendor": VENDOR_TARGET[single]}
    if single in FAMILY_STRINGS:
        return list(FAMILY_STRINGS[single][0]), "family", None

    ids, claim = [], "specific"
    if event.get("models"):
        claim = "family" if len(event["models"]) > 1 else "specific"
    for name in raw:
        if name in FAMILY_STRINGS:
            ids.extend(FAMILY_STRINGS[name][0])
            claim = "family"
        elif name in alias:
            ids.append(alias[name])
        else:
            sys.exit(f"unresolved model string: {name!r} in {event['id']}")
    # de-duplicate, preserve order
    ids = list(dict.fromkeys(ids))
    return ids, (claim if ids else None), None


def convert(event: dict, alias: dict) -> dict:
    eid = event["id"]
    v2 = event["event"]
    kind = KIND_OVERRIDE.get(eid, "availability")
    if v2["type"] == "admin_policy":
        kind = "policy"

    out: dict = {"id": eid, "kind": kind}

    date = {"start": event["date"], "precision": event["date_precision"]}
    out["date"] = date

    out["surface_id"] = SURFACE[(event["platform"]["family"], event["platform"]["product"])]
    exp = event["platform"].get("experience")
    if exp:
        if exp not in EXPERIENCES:
            sys.exit(f"unmapped experience {exp!r} in {eid}")
        if EXPERIENCES[exp]:
            out["experience_ids"] = EXPERIENCES[exp]

    ids, claim, applies = resolve_models(event, alias)
    out["model_ids"] = ids
    if claim:
        out["model_claim"] = claim

    # A policy lives on the admin surface but applies elsewhere. Move any
    # experiences onto applies_to rather than pretending the admin centre
    # hosts Word and Excel.
    if kind == "policy" and out.get("experience_ids"):
        applies = dict(applies or {})
        applies["surfaces"] = ["m365-copilot"]
        applies["experiences"] = out.pop("experience_ids")
    if kind == "policy" and eid in POLICY_REGIONS:
        applies = dict(applies or {})
        applies["regions"] = POLICY_REGIONS[eid]

    if kind == "availability":
        out["lifecycle"] = LIFECYCLE_BY_AVAILABILITY[v2["availability"]]
        exposure = EXPOSURE_OVERRIDE.get(eid)
        if exposure is None:
            exposure = EXPOSURE_BY_SCOPE.get(v2.get("scope"))
        if exposure is None:
            exposure = "catalogue" if v2["type"] == "catalogue_availability" else "not_applicable"
        out["exposure"] = exposure

    if applies:
        out["applies_to"] = applies

    out["confidence"] = event["confidence"]
    out["evidence_note"] = event["evidence_note"]

    caveat = event.get("caveat")
    addition = CAVEAT_ADDITION.get(v2["availability"])
    if addition:
        caveat = f"{caveat} {addition}" if caveat else addition
    if caveat:
        out["caveat"] = caveat
    if event.get("notes"):
        out["notes"] = event["notes"]
    if event.get("tags"):
        out["tags"] = event["tags"]

    if event.get("related_events"):
        out["relations"] = [
            {"type": RELATION_MAP[r["relation"]], "target": r["id"]}
            for r in event["related_events"]
        ]

    out["sources"] = event["sources"]
    return out


# --------------------------------------------------------------------------
# house-style YAML writer: double-quoted scalars, fixed key order, no wrapping
# --------------------------------------------------------------------------
KEY_ORDER = [
    "id", "kind", "date", "surface_id", "experience_ids", "model_ids", "model_claim",
    "lifecycle", "exposure", "applies_to", "confidence", "confidence_detail",
    "evidence_note", "caveat", "notes", "tags", "relations", "sources",
]
SOURCE_ORDER = [
    "publisher", "title", "url", "primary", "retrieved_at", "published_at",
    "source_type", "archived_url", "quote", "supports", "note",
]


def q(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def emit_event(event: dict, out: list[str]) -> None:
    first = True
    for key in KEY_ORDER:
        if key not in event:
            continue
        lead = "  - " if first else "    "
        first = False
        value = event[key]
        if key == "date":
            out.append(f"{lead}date:")
            for dk in ("start", "precision", "end", "basis"):
                if dk in value:
                    out.append(f"      {dk}: {q(value[dk])}")
        elif key in ("experience_ids", "model_ids", "tags"):
            if not value:
                out.append(f"{lead}{key}: []")
            else:
                out.append(f"{lead}{key}: [{', '.join(q(v) for v in value)}]")
        elif key == "applies_to":
            out.append(f"{lead}applies_to:")
            for ak, av in value.items():
                if isinstance(av, list):
                    out.append(f"      {ak}: [{', '.join(q(v) for v in av)}]")
                else:
                    out.append(f"      {ak}: {q(av)}")
        elif key == "confidence_detail":
            out.append(f"{lead}confidence_detail:")
            for ck, cv in value.items():
                out.append(f"      {ck}: {q(cv)}")
        elif key == "relations":
            out.append(f"{lead}relations:")
            for rel in value:
                out.append(f"      - type: {q(rel['type'])}")
                out.append(f"        target: {q(rel['target'])}")
        elif key == "sources":
            out.append(f"{lead}sources:")
            for src in value:
                inner = True
                for sk in SOURCE_ORDER:
                    if sk not in src:
                        continue
                    slead = "      - " if inner else "        "
                    inner = False
                    if sk == "supports":
                        out.append(f"{slead}{sk}: [{', '.join(q(v) for v in src[sk])}]")
                    else:
                        out.append(f"{slead}{sk}: {q(src[sk])}")
        else:
            out.append(f"{lead}{key}: {q(value)}")


BACKLOG_ORDER = [
    "id", "state", "working_claim", "reason", "target", "model_ids", "surface_ids",
    "resolution", "resolved_on", "promoted_to", "sources",
]


def emit_backlog(item: dict, out: list[str]) -> None:
    first = True
    for key in BACKLOG_ORDER:
        if key not in item:
            continue
        lead = "  - " if first else "    "
        first = False
        value = item[key]
        if key in ("model_ids", "surface_ids"):
            out.append(f"{lead}{key}: [{', '.join(q(v) for v in value)}]")
        elif key == "sources":
            out.append(f"{lead}sources:")
            for src in value:
                inner = True
                for sk in SOURCE_ORDER:
                    if sk not in src:
                        continue
                    slead = "      - " if inner else "        "
                    inner = False
                    out.append(f"{slead}{sk}: {q(src[sk])}")
        else:
            out.append(f"{lead}{key}: {q(value)}")


def main() -> None:
    alias, _ = build_alias_table()
    data = yaml.safe_load((ROOT / "data/events.yaml").read_text(encoding="utf-8"))

    events = [convert(e, alias) for e in data["events"]]
    events.sort(key=lambda e: (e["date"]["start"], e["id"]))

    backlog = list(EXTRA_BACKLOG)
    for item in data["validation_backlog"]:
        new = {"id": item["id"], "state": "open", "working_claim": item["working_claim"],
               "reason": item["reason"], "target": item["target"]}
        if item.get("sources"):
            new["sources"] = item["sources"]
        backlog.append(new)

    out: list[str] = []
    out.append("version: 3")
    out.append(f'updated: {q(data["updated"])}')
    out.append(f'research_cutoff: {q(data["research_cutoff"])}')
    out.append("metadata:")
    md = data["metadata"]
    out.append(f'  project: {q(md["project"])}')
    out.append(f'  purpose: {q(md["purpose"])}')
    out.append("  interpretation_rules:")
    for rule in md["interpretation_rules"]:
        out.append(f"    - {q(rule)}")
    out.append("  confidence_definitions:")
    for k, v in md["confidence_definitions"].items():
        out.append(f"    {k}: {q(v)}")
    out.append("  import_provenance:")
    for k, v in md["import_provenance"].items():
        out.append(f"    {k}: {q(v) if isinstance(v, str) else v}")
    out.append("events:")
    for event in events:
        emit_event(event, out)
    out.append("validation_backlog:")
    for item in backlog:
        emit_backlog(item, out)

    (ROOT / "data/events.yaml").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"migrated {len(events)} events and {len(backlog)} backlog items to schema v3")


if __name__ == "__main__":
    main()
