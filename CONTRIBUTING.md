# Contributing

Corrections, additional model events and better primary sources are welcome.

## Core rules

1. Record only publicly supportable claims.
2. Prefer first-party vendor, Microsoft, GitHub or product documentation.
3. Do not turn an inference into a deployment date.
4. Keep GitHub Models separate from GitHub Copilot.
5. Keep embedded/specialist use separate from a generally selectable model.
6. Use separate events for preview, GA, default, retirement and policy changes when those dates are independently known.
7. Preserve the evidence's real date precision; do not invent a day. Use
   `date.end` for a rollout window rather than picking a point inside it.
8. If a claim is not yet strong enough for `confirmed` or `supported`, add it to `validation_backlog` instead of the canonical timeline.

## Adding or correcting an event

Edit `data/events.yaml`. Each event needs a stable `id`, a `kind`, a `date`
object, a `surface_id`, `model_ids`, confidence, an evidence note, and at
least one public source. Availability events also need `lifecycle` and
`exposure`.

If the model or surface is not yet in `data/models.yaml` or
`data/platforms.yaml`, add it there first. The build rejects unknown IDs, so
a typo cannot silently create a second identity for an existing model.

Set `kind` honestly. `availability` means the model was actually available on
that surface on that date. An announcement of future availability is
`announcement` and is excluded from timelines and lag by construction.

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

The build validates all three data files against their schemas, resolves every
model, surface and experience ID, checks relationships and ordering, and
regenerates the files in `generated/`.

It reports two classes of problem. **Errors** fail the build: unknown IDs,
duplicate or semantically duplicate events, a restoration without a
suspension, a release stage that precedes an earlier stage on the same
surface, an event dated before its model's vendor release, or `confirmed`
without a primary source. **Warnings** are printed but do not fail: day
precision landing on the first of a month, `confirmed` resting only on
current documentation, and models with no vendor release event.

## Confidence

- `confirmed`: clear first-party evidence for the event/date/scope
- `supported`: strong evidence, but the exact first date relies on retrospective/current documentation or paired evidence

Where parts of a claim differ in evidential strength, record that with
`confidence_detail`. `confidence` must equal the weakest part.

Unresolved claims belong in `validation_backlog`; they do not receive a
canonical confidence value until promoted with sufficient evidence.

## Backlog states

Every backlog item has a `state`. When you resolve one, say how:

- `promoted` — record `resolution`, `resolved_on` and `promoted_to`
- `rejected` — record `resolution` and `resolved_on`, and leave the item in
  place so the question is not reopened and decided differently later
- `blocked` — no source appears to exist; say what would unblock it

Promotion requires: a primary source that is not merely current-state
documentation (or `supported` confidence with the reliance stated in
`caveat`); date precision matching the evidence; and an unambiguous surface
and exposure. Cross-platform inference is never sufficient on its own.

## Pull requests

A useful PR explains what changed, why, and links the strongest public source.
Where a correction changes an availability or lag claim, note the previous and
new interpretation explicitly.
