#!/usr/bin/env python3
"""Look a freshly filed candidate issue up against the dataset.

A candidate issue carries a headline and a source URL. Before anyone reads the
page, three questions have mechanical answers:

1. Is that URL already cited by an event or a validation-backlog item?
2. Has the dataset ever cited that publisher's host?
3. Which registered models does the headline name, and what is already
   recorded for them?

This script answers those and renders a comment for the issue. It is a lookup,
not a decision: it never closes an issue and never edits data. Only the first
answer can mark an issue as a likely duplicate, and only when the URL is
already cited by a published event.

The issue title and body are untrusted text. They are parsed with regular
expressions and compared against the dataset; nothing in them is executed, and
the only parts echoed back are the URL and host, inside code spans.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import yaml

MARKER = "<!-- pretriage -->"
DUPLICATE_LABEL = "likely-duplicate"

SOURCE_LINE = re.compile(r"^\*\*Source:\*\*\s*(\S+)", re.MULTILINE)
ARCHIVE_PREFIX = re.compile(r"^web\.archive\.org/web/\d+(?:[a-z]{2}_)?/(.+)$", re.IGNORECASE)
LOCALE_SEGMENT = re.compile(r"^/[a-z]{2}-[a-z]{2}(?=/|$)")
# Besides every utm_ parameter.
TRACKING_PARAMS = ("ocid", "wt.mc_id", "mc_cid", "mc_eid")
TECHCOMMUNITY_ID = re.compile(r"/(\d{5,})$")

SEPARATOR = r"[\s ‐‑-]"

MAX_EVENTS_PER_MODEL = 6
MAX_MODELS = 8
# Names this short match ordinary words and other models' names.
MIN_NAME_LENGTH = 4


def normalise_url(url: str) -> str:
    """Reduce a URL to the form two citations of the same page share.

    Scheme, `www.`, a leading locale segment, tracking parameters, the fragment
    and a trailing slash all vary between citations of one page. A Wayback
    capture is reduced to the page it captured.
    """
    text = url.strip().strip("<>")
    if "://" not in text:
        text = "https://" + text
    parts = urlsplit(text)
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path
    archived = ARCHIVE_PREFIX.match(host + path)
    if archived:
        return normalise_url(archived.group(1) + ("?" + parts.query if parts.query else ""))
    path = LOCALE_SEGMENT.sub("", path.lower()).rstrip("/")
    query = sorted(
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not (key.lower().startswith("utm_") or key.lower() in TRACKING_PARAMS)
    )
    suffix = "?" + "&".join(f"{key}={value}" for key, value in query) if query else ""
    return f"{host}{path}{suffix}"


def page_keys(url: str) -> set[str]:
    """Every key a page can be matched on.

    Tech Community posts are published under more than one path for the same
    numeric post id, so the id is a key of its own.
    """
    normalised = normalise_url(url)
    keys = {normalised}
    host = normalised.split("/", 1)[0]
    if host == "techcommunity.microsoft.com":
        post = TECHCOMMUNITY_ID.search(normalised.split("?", 1)[0])
        if post:
            keys.add(f"techcommunity:{post.group(1)}")
    return keys


def host_of(url: str) -> str:
    return normalise_url(url).split("/", 1)[0].split("?", 1)[0]


def extract_source(body: str) -> str | None:
    """The URL on the issue's `**Source:**` line, if it has one."""
    found = SOURCE_LINE.search(body or "")
    if not found:
        return None
    candidate = found.group(1).strip("<>")
    if not re.match(r"^https?://[^\s<>\"'`]+$", candidate):
        return None
    return candidate


class Index:
    """The dataset, arranged for the three lookups."""

    def __init__(self, events_doc: dict, models_doc: dict) -> None:
        self.events_by_page: dict[str, list[str]] = {}
        self.backlog_by_page: dict[str, list[str]] = {}
        self.host_citations: dict[str, int] = {}
        self.events_by_model: dict[str, list[dict]] = {}
        self.names: list[tuple[re.Pattern[str], str, str]] = []

        for event in events_doc.get("events") or []:
            self._add_sources(event, self.events_by_page)
            for model_id in event.get("model_ids") or []:
                self.events_by_model.setdefault(model_id, []).append(event)
        for item in events_doc.get("validation_backlog") or []:
            self._add_sources(item, self.backlog_by_page)

        entries: list[tuple[str, str, str]] = []
        for model in models_doc.get("models") or []:
            display = model.get("display_name") or model["id"]
            for name in {display, *(model.get("aliases") or [])}:
                if len(name) >= MIN_NAME_LENGTH:
                    entries.append((name, model["id"], display))
        # Longest first, so "GPT-5.4 mini" is tried before "GPT-5.4".
        entries.sort(key=lambda entry: (-len(entry[0]), entry[0]))
        for name, model_id, display in entries:
            # Headlines write "GPT-5.5", "GPT 5.5" and "GPT‑5.5" (a non-breaking
            # hyphen) for one model, so a space and a hyphen are one separator.
            escaped = re.sub(r"\\[ -]", lambda _: SEPARATOR, re.escape(name))
            pattern = re.compile(r"(?<![\w.-])" + escaped + r"(?![\w-]|\.\d)", re.IGNORECASE)
            self.names.append((pattern, model_id, display))

    def _add_sources(self, record: dict, target: dict[str, list[str]]) -> None:
        for source in record.get("sources") or []:
            for field in ("url", "archived_url"):
                url = source.get(field)
                if not url:
                    continue
                for key in page_keys(url):
                    ids = target.setdefault(key, [])
                    if record["id"] not in ids:
                        ids.append(record["id"])
            if source.get("url"):
                host = host_of(source["url"])
                self.host_citations[host] = self.host_citations.get(host, 0) + 1

    def cited_by(self, url: str) -> tuple[list[str], list[str]]:
        events: list[str] = []
        backlog: list[str] = []
        for key in sorted(page_keys(url)):
            for found, target in ((self.events_by_page, events), (self.backlog_by_page, backlog)):
                for record_id in found.get(key, []):
                    if record_id not in target:
                        target.append(record_id)
        return events, backlog

    def models_named(self, text: str) -> list[tuple[str, str]]:
        """Registered models named in the text, longest names claiming their span first."""
        taken: list[tuple[int, int]] = []
        hits: list[tuple[int, str, str]] = []
        for pattern, model_id, display in self.names:
            for found in pattern.finditer(text or ""):
                span = found.span()
                if any(span[0] < end and start < span[1] for start, end in taken):
                    continue
                taken.append(span)
                if all(model_id != seen for _, seen, _ in hits):
                    hits.append((span[0], model_id, display))
        return [(model_id, display) for _, model_id, display in sorted(hits)]


def describe_event(event: dict) -> str:
    date = (event.get("date") or {}).get("start", "undated")
    what = event.get("lifecycle") or event.get("kind") or "event"
    return f"`{event['id']}` ({date}, {event.get('surface_id', 'no surface')}, {what})"


def assess(title: str, body: str, index: Index) -> dict:
    source = extract_source(body)
    result: dict = {
        "source": source,
        "host": host_of(source) if source else None,
        "cited_by_events": [],
        "cited_by_backlog": [],
        "host_citations": 0,
        "models": [],
        "duplicate": False,
    }
    if source:
        events, backlog = index.cited_by(source)
        result["cited_by_events"] = events
        result["cited_by_backlog"] = backlog
        result["host_citations"] = index.host_citations.get(result["host"], 0)
        result["duplicate"] = bool(events)
    for model_id, display in index.models_named(title)[:MAX_MODELS]:
        events = sorted(
            index.events_by_model.get(model_id, []),
            key=lambda event: (event.get("date") or {}).get("start", ""),
            reverse=True,
        )
        result["models"].append({"id": model_id, "display_name": display, "events": events})
    return result


def render(result: dict, revision: str = "") -> str:
    lines = [MARKER, "### Pre-triage lookup", ""]
    source = result["source"]
    if not source:
        lines.append("- **Source URL:** no `**Source:**` line with a web address was found in the issue, so nothing was looked up.")
    else:
        events, backlog = result["cited_by_events"], result["cited_by_backlog"]
        if events:
            cited = ", ".join(f"`{record_id}`" for record_id in events)
            lines.append(f"- **Source URL:** already cited by {cited}. **Likely duplicate**: check whether the page says anything not already recorded.")
        else:
            lines.append("- **Source URL:** not cited by any event.")
        if backlog:
            cited = ", ".join(f"`{record_id}`" for record_id in backlog)
            lines.append(f"- **Validation backlog:** the same URL is a source on {cited}. This candidate may resolve or duplicate that item.")
        count = result["host_citations"]
        if count:
            lines.append(f"- **Publisher host:** `{result['host']}` is cited {count} time{'s' if count != 1 else ''} in the dataset.")
        else:
            lines.append(f"- **Publisher host:** `{result['host']}` has not been cited in the dataset before. If this is secondary coverage, find the primary page.")

    models = result["models"]
    if not models:
        lines.append("- **Models named in the title:** none that the registry knows. Either the model is new, or the post names no model.")
    else:
        lines.append("- **Models named in the title:**")
        for model in models:
            events = model["events"]
            if not events:
                lines.append(f"  - `{model['id']}` ({model['display_name']}): registered, no events yet.")
                continue
            shown = "; ".join(describe_event(event) for event in events[:MAX_EVENTS_PER_MODEL])
            more = len(events) - MAX_EVENTS_PER_MODEL
            tail = f"; and {more} earlier" if more > 0 else ""
            lines.append(f"  - `{model['id']}` ({model['display_name']}): {len(events)} event{'s' if len(events) != 1 else ''}. {shown}{tail}.")

    lines.append("")
    at = f" at `{revision[:7]}`" if revision else ""
    lines.append(f"<sub>A mechanical lookup against `data/`{at}. It matches URLs and registered names; it does not read the page and it decides nothing.</sub>")
    return "\n".join(lines) + "\n"


def load_index(data_dir: Path) -> Index:
    events_doc = yaml.safe_load((data_dir / "events.yaml").read_text(encoding="utf-8"))
    models_doc = yaml.safe_load((data_dir / "models.yaml").read_text(encoding="utf-8"))
    return Index(events_doc, models_doc)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--title-file", type=Path, required=True)
    parser.add_argument("--body-file", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    parser.add_argument("--revision", default="")
    parser.add_argument("--comment-out", type=Path, required=True)
    parser.add_argument("--result-out", type=Path, required=True)
    args = parser.parse_args(argv)

    title = args.title_file.read_text(encoding="utf-8")
    body = args.body_file.read_text(encoding="utf-8")
    result = assess(title, body, load_index(args.data_dir))
    args.comment_out.write_text(render(result, args.revision), encoding="utf-8")
    summary = {
        "duplicate": result["duplicate"],
        "cited_by_events": result["cited_by_events"],
        "cited_by_backlog": result["cited_by_backlog"],
        "models": [model["id"] for model in result["models"]],
    }
    args.result_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
