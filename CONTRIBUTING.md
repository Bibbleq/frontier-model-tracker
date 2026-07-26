# Contributing

Corrections, additional model events and better primary sources are welcome.

## Core rules

1. Record only publicly supportable claims.
2. Prefer first-party vendor, Microsoft, GitHub or product documentation.
3. Do not turn an inference into a deployment date.
4. Keep GitHub Models separate from GitHub Copilot.
5. Keep embedded/specialist use separate from a generally selectable model.
6. Use separate events for preview, GA, default, retirement and policy changes when those dates are independently known.
7. If the date or scope is uncertain, lower the confidence field and explain why in `notes`.

## Adding or correcting an event

Edit `data/events.yaml`. Each event needs a stable `id`, date, vendor/model,
platform/surface information, event classification, confidence and at least one
public source.

Please keep IDs descriptive and stable, for example:

```text
openai-gpt-5-m365-2025-08-07-rollout
anthropic-claude-3-5-sonnet-github-2024-11-01-public-preview
```

Run:

```bash
python -m pip install pyyaml jsonschema
python scripts/build.py
```

The build validates the YAML against the JSON Schema, checks IDs and sources,
and regenerates `generated/events.json` and `generated/events.csv`.

## Confidence

- `confirmed`: clear first-party evidence for the event/date/scope
- `probable`: evidence is good but a detail such as exact rollout date or scope remains uncertain
- `needs-verification`: retained for research, but should not be used for firm lag calculations

## Pull requests

A useful PR explains what changed, why, and links the strongest public source.
Where a correction changes an availability or lag claim, note the previous and
new interpretation explicitly.
