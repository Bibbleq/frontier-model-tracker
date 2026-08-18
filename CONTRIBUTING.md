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

## Archiving drift-prone sources

Living documentation is edited in place. A Microsoft Learn page that states a
date today may be rewritten next year, leaving a citation that no longer
attests what it was cited for.

When you add a `documentation` or `release_notes` source, look up an existing
snapshot with the read-only CDX API and record it in `archived_url`:

```
https://web.archive.org/cdx/search/cdx?url=<url-without-scheme>&filter=statuscode:200&limit=5
```

Build the `archived_url` as
`https://web.archive.org/web/<timestamp>/<original>` from a returned row.

Do not use the older availability API
(`https://archive.org/wayback/available`): from some networks it returns 429
to every request regardless of volume. An instant 429 on a first request is
the endpoint refusing you, not a rate limit to wait out — the CDX lookup on
the same infrastructure answers normally.

The build warns for every such source without one. The warning count is meant
to fall over time; it is a queue, not noise.

## Identifier stability

Identifiers are a public interface. Once a commit reaches `main`, the IDs in
it are permanent.

- **Never rename an ID that has been merged.** Downstream consumers, the
  generated CSVs and the `promoted_to` links in the validation backlog all
  reference them.
- **Never reuse an ID** for a different event, model or surface, even if the
  original was removed.
- If a model or product is renamed by its vendor, keep the ID and change
  `display_name`. Add the old name to `aliases` (models) or set
  `renamed_from` / `renamed_to` (surfaces). GPT-4o keeping its ID through a
  display change is the intent; Azure OpenAI becoming Microsoft Foundry is
  modelled as a rename chain, not an ID change.
- If an ID is genuinely wrong, correct it in the same pull request that
  introduced it. After that, treat it as permanent and record the correction
  in `caveat` instead.

IDs are lowercase, digits and hyphens only, enforced by all three schemas.
Event IDs read surface-model-date, for example
`foundry-opus5-availability-2026-07-24`. Keep them descriptive enough to
recognise in a diff without opening the file.

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

## Automated triage

Candidate events reach this repository automatically. An upstream watcher,
Steward, files them as issues through the Bibble Envoy bot account, labelled
`candidate`, with the headline, the source URL, the publication and an excerpt
from the primary source in the body. A workflow
(`.github/workflows/assign-copilot.yml`) hands each one to the GitHub Copilot
cloud agent, which works to the brief in `.github/copilot-instructions.md`. That
brief is the same standard this document sets: the agent either promotes the
candidate to a schema-valid event, adds it to `validation_backlog` when the claim
is real but underdated or underscoped, or comments explaining why it is a
duplicate, out of scope or not a model event at all. It is told, in as many words,
never to invent a date and that "I could not verify this" is a successful
outcome.

Nothing merges itself. The agent opens an ordinary pull request that a human
reads and merges, and everything the automated path produces is validated the
same way a hand-written contribution is: `python scripts/build.py` and the
invariant tests run in CI, the build fails on unknown identifiers, unsorted
events, date/precision mismatches, impossible lifecycle orderings and
`confirmed` without a primary source, and the workflow refuses any pull request
whose `generated/` tree is stale. Automation changes who drafts the diff; it does
not change the evidence bar or who is accountable for what the dataset claims.
