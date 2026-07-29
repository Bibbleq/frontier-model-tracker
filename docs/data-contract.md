# Data contract

This repository is the authoritative source for the dataset. It publishes the
generated outputs at a stable URL so that display layers — the 365Explained
WordPress plugin first, others later — can render the data without copying
historical claims into a second place.

This document is the promise those consumers can rely on. It describes what is
stable, what may change, how change is signalled, and what a consumer must do
to render the data honestly.

**Contract version 2. Dataset version 3.**

## Base URL

```
https://bibbleq.github.io/frontier-model-tracker/
```

The live tree and immutable release snapshots are published from `main`:

| Tree | Meaning |
| --- | --- |
| `/` | Latest. Receives data additions and corrections and may move to a new version pair. |
| `/c2/v3/` | Immutable snapshot of contract version 2 and dataset version 3. Its bytes never change. |
| `/c1/v3/` | Earlier snapshot, retained. |

Consumers that need current research should use `/`, inspect both version
numbers in the manifest, and refuse unsupported versions. Consumers that need
reproducible bytes can pin to the version-pair snapshot.

Start at the manifest:

```
https://bibbleq.github.io/frontier-model-tracker/manifest.json
https://bibbleq.github.io/frontier-model-tracker/c2/v3/manifest.json
```

## What is in the contract

These paths are stable within a version tree. Every payload path (everything
except `manifest.json` itself) is listed in the manifest with its byte length
and SHA-256. The manifest is verified separately against the committed snapshot.

| Path | Contents |
| --- | --- |
| `manifest.json` | Contract and dataset versions, file inventory with checksums, licence and attribution |
| `data/events.json` | The whole dataset: metadata, canonical events, validation backlog |
| `data/status.json` | Totals, warning counts, coverage gaps, lag certainty distribution |
| `data/events.csv` | Flattened timeline, IDs resolved to display names |
| `data/validation-backlog.csv` | Research queue with states and targets |
| `data/lag.csv` | Derived adoption lag |
| `data/current-state.csv` | Last known lifecycle per model and surface, with the caveats needed to read it |
| `data/models.csv`, `data/surfaces.csv` | The registries, each with an `event_count` |
| `schema/events.schema.json` | JSON Schema the dataset validates against |
| `schema/models.schema.json`, `schema/platforms.schema.json` | Registry schemas |

`events.json` is the complete picture. The CSVs are conveniences derived from
it; if they ever disagree, `events.json` wins.

## Versioning

Two version numbers, and they answer different questions.

**`dataset_version`** (also `version` inside `events.json`) describes the shape
of the data. It is currently `3`. It increments when a change would break a
consumer that reads the previous shape: a field removed or renamed, a value
removed from an enum, or a field's meaning changed.

**`contract_version`** describes this document and the publishing layout — URL
structure, the manifest format, which files exist. It is currently `2`.

Either may increment without the other. Snapshot paths therefore include both
numbers: `/c{contract_version}/v{dataset_version}/`.

### What is a breaking change

Breaking, and therefore requires the relevant version bump and a new immutable
version-pair snapshot:

- removing or renaming a field
- removing a value from a closed enum (`kind`, `lifecycle`, `exposure`,
  `confidence`, relation `type`, backlog `state`, `counts_as` tiers)
- changing what an existing field or value means
- removing a published file, or moving it

Not breaking, and may happen at any time without notice:

- adding an event, a model, a surface, or a backlog item
- adding an optional field to a record
- adding a new value to an open vocabulary (`availability` on a source's
  `publisher`, free-text `caveat`, `evidence_note`)
- adding a new file
- adding a new warning code to `status.json`
- correcting data: a date, a confidence level, an event promoted from the
  backlog or withdrawn from the timeline

Consumers must therefore **ignore fields they do not recognise** rather than
failing on them.

The same applies to values. A closed enum may gain a value — `lifecycle`
gained `legacy` at contract version 2 — so a consumer must treat an
unrecognised value as opaque rather than rejecting the record or mapping it
onto the nearest value it knows. Removing a value stays breaking; adding one
does not.

### Deprecation policy

When either version changes:

1. The new version pair appears at `/` and gets its own committed snapshot,
   for example `/c1/v4/` or `/c2/v3/`.
2. Previous snapshots remain published for at least **six months**.
3. The change is recorded in the change log at the end of this document and in
   the repository release notes.

Snapshots are stored under `published/cN/vN/` in the repository and copied
into every Pages artifact. A snapshot is never altered in place. Data additions
and corrections after its creation appear only in the live `/` tree and in a
future snapshot.

## Obligations on a consumer

The dataset exists to avoid false precision and false equivalence. A renderer
can undo that work by flattening distinctions the data keeps. These are the
rules a display layer must respect; they are not stylistic preferences.

### 1. Only `kind: availability` belongs on a timeline

Every event carries `kind`, one of `availability`, `announcement`, `policy`,
`milestone`.

An `announcement` is a statement that something *will* become available. It is
not availability and must never be drawn as though it were. The dataset records
a Microsoft statement from 16 September 2024 that o1 would come to Microsoft 365
Copilot; OpenAI released o1 on 17 December 2024. Rendering that announcement as
availability produces a model arriving on a Microsoft surface 92 days before it
existed.

`policy` events carry no `model_ids` at all and must not be counted as a model
becoming available.

Only `availability` events carry `lifecycle` and `exposure`. If those fields are
absent, the event is not an availability fact.

### 2. Do not merge `lifecycle` and `exposure`

`lifecycle` says where in the release cycle: `private_preview`,
`limited_preview`, `public_preview`, `ga`, `legacy`, `deprecated`, `retired`,
`suspended`, `restored`.

`exposure` says how the model is exposed: `underlying`, `specialist`,
`catalogue`, `selectable`, `default`, `not_applicable`.

They are independent. A model can be GA on a surface and still not selectable
by a user, because it is catalogue-only or powers a feature invisibly. If your
UI has one "available" state, you are collapsing two different facts.

### 3. Surface tiers come from the registry, not from names

`surfaces.csv` and `platforms.yaml` give each surface a `counts_as` list. Use
it. Do not infer grouping from display names.

In particular:

- **GitHub Models is not GitHub Copilot.** It counts as `microsoft` and never
  as `copilot`.
- **Foundry catalogue availability is not Copilot availability.** Foundry
  surfaces count as `microsoft` and `foundry`, never `copilot`.
- **The Microsoft 365 admin centre is not a Copilot surface.** An admin control
  appearing is not a model reaching users.

A surface that has been renamed keeps its history through `renamed_from` and
`renamed_to`. Group by `lineage` when you want the product's whole history;
label individual events with the name that was current on the day, not the
current brand.

### 4. Never render a partial date as an exact one

Every event's `date` has a `precision` of `day`, `month` or `year`, and may
carry an `end` for a rollout window.

Format from the precision. A month-precision date is "October 2025", never
"1 October 2025". Sorting may pad internally — sort by the earliest possible
day — but display must not.

### 5. Read `certainty` before reading a lag number

`lag.csv` gives `lag_days_min` and `lag_days_max` alongside a `certainty`:

| `certainty` | Meaning |
| --- | --- |
| `exact` | A single defensible number |
| `range` | A window, because at least one date is partial |
| `not_recorded` | No availability recorded on this tier |
| `unknown_open_research` | An open backlog item covers this model and tier |
| `unknown_no_baseline` | No vendor release to measure from |

`unknown_open_research` is the one that matters. It means the question has not
been researched, not that the model never arrived. Rendering it identically to
`not_recorded` — or as a gap in a chart — turns a gap in research into an
apparent finding. Show the three unknowns distinguishably, or show none of them.

Every row also has a `measure`, either `any_exposure` or
`selectable_or_default`. Do not average or merge them. GPT-4.1 reached a
Microsoft surface in 0 days via the Foundry catalogue and became selectable in
Copilot Studio 170 to 200 days later. Both are true; reporting only the first
is misleading.

### 6. The backlog is not history

`validation-backlog.csv` and the `validation_backlog` array are open research
questions. Items have a `state`: `open`, `promoted`, `rejected`, `blocked`.

They must never be rendered as timeline events, and `rejected` items must not
be presented as claims. If you surface the backlog at all, label it as
unresolved research.

### 7. The latest event is not the current state

The dataset records events, not states. The most recent event for a model on a
surface says what last changed; it does not say what is true today.

Model withdrawal is published far less consistently than model arrival, and on
some surfaces not at all, so a model can sit in the dataset at the last stage
anyone recorded long after it left. Reading the latest `lifecycle` as present
tense produces claims the data never made — that GPT-4 is still in public
preview on Azure OpenAI, for example, because its arrival was recorded and its
progression was not.

Use `data/current-state.csv`, which derives this once so that every renderer
does not derive it differently. Two columns carry the caveat:

| Column | Meaning |
| --- | --- |
| `state_is_terminal` | The model reached a stage it does not return from. Only then is `lifecycle` safe to present as the current state. |
| `open_questions` | Count of unresolved backlog items naming this model and surface. |
| `known_as_of` | The dataset's research cutoff. Everything else is last-known, not current. |

Where the state is not terminal, say so. "Last recorded as GA in November
2023" is honest; "GA" is not. `model_superseded_by` is offered as a hint for a
reader, not as evidence that a model was withdrawn — succession in the
registry is a fact about models, not about any surface.

### 8. Show confidence

Every event has `confidence`, either `confirmed` or `supported`, and may carry
`confidence_detail` naming which part of the claim is soft. `supported` means
the exact first date rests on retrospective or current documentation.

A renderer need not show this on every row, but it must be reachable. Do not
present `supported` claims with the same visual authority as `confirmed` ones
without any way to tell them apart.

## Caching and polite use

GitHub Pages serves these files with `Access-Control-Allow-Origin: *`, so a
browser can fetch them directly, and with an `ETag` and `Cache-Control:
max-age=600`.

- Send `If-None-Match` with the stored ETag and handle `304 Not Modified`.
- Do not poll more than once an hour. The dataset changes at most a few times
  a week.
- Cache server-side where you can. A WordPress consumer should hold the
  response in a transient rather than fetching per page view.
- `manifest.json` is small. Fetch it first to decide whether the larger files
  are worth re-fetching, and to verify checksums.

## Licence and attribution

The dataset and generated representations are licensed **CC BY 4.0**. The code
in this repository is **MIT**. Display layers are separate works and may carry
their own licence; a WordPress plugin distributed through wordpress.org will be
GPLv2-or-later. Fetching the data at runtime keeps those licences apart: the
plugin is GPL code, the data remains CC BY and is consumed rather than bundled.

Any published rendering must attribute the source. The minimum is a visible
credit naming **365Explained Frontier Model Tracker** and linking to the
repository or the published site. `manifest.json` carries the exact attribution
string.

The dataset records publicly documented availability. It is a sourced research
project, not official product documentation, and is not affiliated with
Microsoft, OpenAI, Anthropic or GitHub. A renderer should not imply otherwise.

## What is not in the contract

These may change without a version bump, and a consumer must not depend on
them:

- the layout of `data/events.yaml`, `data/models.yaml`, `data/platforms.yaml`
  or anything else under `data/` in the repository — only the published
  `data/` tree on the site is stable
- the wording of any `evidence_note`, `caveat`, `note`, `quote`,
  `working_claim`, `reason`, `target` or `resolution`
- the wording of warning messages in `status.json`; the `code` field is stable,
  the `message` is not
- the ordering of arrays, other than `events`, which is sorted by
  `(date.start, id)` and will stay so
- the HTML pages at `/` and `/dashboard.html`, which are a viewer and not an
  interface
- the repository's branch names, workflow names and internal scripts

## Change log

| Contract | Dataset | Change |
| --- | --- | --- |
| 2 | 3 | Adds `data/current-state.csv` and the obligation not to render the latest event as the current state. Adds `legacy` to the `lifecycle` enum and states that consumers must tolerate unrecognised enum values. |
| 1 | 3 | Initial contract. Establishes the base URL, immutable `/c1/v3/` snapshot, `manifest.json`, versioning and deprecation policy, and consumer obligations above. |
