# Methodology

How derived analysis is computed, and what it deliberately refuses to compute.

## Generated outputs

| File | Contents |
| --- | --- |
| `events.json` | The dataset verbatim, metadata included |
| `events.csv` | Flattened timeline, IDs resolved to display names |
| `validation-backlog.csv` | The research queue with states and targets |
| `models.csv`, `surfaces.csv` | Model and surface registries, each with an `event_count` |
| `series.csv`, `generations.csv`, `model-lines.csv` | Model classification registries |
| `lag.csv` | Derived adoption lag |

`event_count` in the registry exports is a coverage signal. A registry entry
with zero events is either a gap worth filling or an entry that exists only so
a backlog item can name its target.

Model grouping is descriptive, not a succession calculation. `generation`
groups named or numbered eras within a vendor series, `model_line` follows recurring
named branches, and `family` records models marketed together. Only an explicit
`supersedes` link asserts replacement.

`generated/lag.csv` is rebuilt from source on every build. Lag is never stored
in canonical data, so it cannot drift from the events it describes and cannot
be edited into a claim the sources do not support.

## What counts as an availability fact

Only events with `kind: availability` enter any derived calculation.

`announcement` events are excluded by construction. This is not a filter that
an analyst has to remember to apply: the schema forbids `lifecycle` and
`exposure` on non-availability events, so an announcement has nothing for the
lag calculation to read.

That rule exists because the dataset previously recorded a Wave 2 statement
that Microsoft *would* add o1 to Microsoft 365 Copilot as though it were
availability, dated 92 days before OpenAI released the model.

`policy` and `milestone` events are excluded for the same reason. A policy
event carries no `model_ids` at all, so an admin toggle can never be counted
as a model becoming available.

## The baseline

The lag origin for a model is the earliest `kind: availability` event on a
surface marked `vendor_baseline` in `data/platforms.yaml`.

`baseline_lifecycle` is emitted alongside it. This matters: GPT-5.6 Sol was
previewed by OpenAI on 26 June 2026 and generally released on 9 July, so its
baseline is a `limited_preview`. Consumers who want vendor GA as the origin
can filter on that column rather than having the choice made for them.

If a model has no vendor release event in the dataset, every lag row for it is
`unknown_no_baseline`. The build also warns. Twelve models are currently in
this state, including Codex, Llama 2 and DeepSeek-R1.

## Tiers

Tiers come from `counts_as` on each surface. They are declared once in the
registry and never re-derived per query.

| Tier | Means |
| --- | --- |
| `microsoft` | first availability anywhere in the Microsoft estate |
| `copilot` | first availability in a Copilot product |
| `m365` | first availability in Microsoft 365 Copilot |
| `studio` | first availability in Copilot Studio |
| `github_copilot` | first availability in GitHub Copilot |
| `foundry` | first availability in the Foundry lineage |

Two consequences are deliberate and load-bearing:

**Catalogue availability counts as Microsoft availability but never as Copilot
availability.** Foundry surfaces declare `[microsoft, foundry]`. A model
appearing in the Foundry catalogue has genuinely arrived on a Microsoft
surface, and saying otherwise would understate Microsoft's estate. But it is
not available in any Copilot product, and counting it as such would be the
central false equivalence this project exists to prevent.

**GitHub Models counts as Microsoft but never as Copilot.** It is a developer
model catalogue that happens to share a brand prefix with GitHub Copilot.

**The Microsoft 365 admin centre counts as Microsoft but never as Copilot.**
An admin control appearing is not a model reaching users.

**Copilot Cowork counts as Copilot but never as `m365`.** Cowork is a distinct
product with its own model picker, reached through the Microsoft 365 Copilot
Frontier programme, and models arrive there on dates the rest of Microsoft 365
Copilot does not share. The `m365` tier continues to mean the Microsoft 365
Copilot surface — Copilot Chat and the app experiences — so a model that has
only reached Cowork reports no `m365` availability. That is the narrower
reading: a later ruling can widen the tier without rewriting history, while
removing a tier from a surface would be a breaking change.

## Measures

Every model and tier produces two rows, because "available" is ambiguous and
collapsing the two readings is how misleading numbers get made.

| Measure | Exposures included |
| --- | --- |
| `any_exposure` | `underlying`, `specialist`, `catalogue`, `selectable`, `default` |
| `selectable_or_default` | `selectable`, `default` |

The gap between them is often the most interesting number in the dataset.
GPT-4.1 reached a Microsoft surface the day OpenAI released it, via the
Foundry catalogue — `any_exposure` lag of 0 days. It did not become a model a
Copilot Studio maker could actually get until it became the default months
later — `selectable_or_default` lag of 170 to 200 days. Reporting only the
first number would be true and misleading.

## Partial precision

Dates are widened to the interval of days they could mean before any
subtraction:

| Precision | Interval |
| --- | --- |
| `day` | that day |
| `month` | first to last day of the month |
| `year` | 1 January to 31 December |
| with `end` | from the start of `start` to the end of `end` |

Lag is then computed as an interval:

```
lag_days_min = platform_earliest - baseline_latest
lag_days_max = platform_latest  - baseline_earliest
```

`certainty` is `exact` when the two agree and `range` when they do not. A
month-precision date never becomes a point value, so partial precision cannot
be laundered into false precision by arithmetic.

## When lag is deliberately not a number

| `certainty` | Meaning |
| --- | --- |
| `exact` | A single defensible number |
| `range` | A window, because at least one date is partial |
| `not_recorded` | The model has a vendor release but no recorded availability on this tier |
| `unknown_open_research` | An open validation-backlog item covers this model and tier |
| `unknown_no_baseline` | No vendor release event, so there is nothing to measure from |

`unknown_open_research` is the important one. If the backlog holds an open
question about a model on a surface, the lag for that tier is suppressed
rather than reported as absent. Without it, a gap in *research* renders
identically to evidence of *non-availability*, which is the most likely way
this dataset would mislead someone.

`not_recorded` is a weaker statement than absence. It means the dataset holds
no availability event for that model and tier — which may be because it never
happened, or because nobody has sourced it yet. Treat it as an invitation to
open a backlog item, not as a finding.

## Promotion from the validation backlog

An item may become a canonical event when all of the following hold:

1. At least one primary source that is not merely current-state
   documentation. Current docs prove a model is supported now; they rarely
   prove when it first was. Where the first date does rest on retrospective
   documentation, the event takes `confidence: supported` and says so in
   `caveat`.
2. Date precision matches the evidence. If the source supports only a month,
   the event uses month precision.
3. Surface and exposure are unambiguous.
4. No unresolved contradiction between sources. Contradictions stay in the
   backlog with both sources recorded.
5. Cross-platform inference is never sufficient on its own. That a model
   appeared on one surface is not evidence it appeared on another the same
   day, however plausible.

Items that fail permanently are marked `rejected` with a `resolution`, and
stay in the file. This is deliberate: without a rejected state the same
question is reopened and may be decided differently next time.
