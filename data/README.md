# Dataset

Three human-maintained files are the source of truth:

- `models.yaml` — the model registry: stable IDs, vendors, families, aliases
- `platforms.yaml` — the surface registry: stable IDs, rename lineage, analytical tiers, experiences
- `events.yaml` — the canonical timeline and the validation backlog

Events reference the registries by ID. Nothing in `events.yaml` names a model
or a product in free text, so a model cannot be recorded under two spellings
and a 2023 Azure OpenAI event cannot be relabelled with a 2025 brand name.

## The three axes

Every event answers three separate questions. They are deliberately
orthogonal: none of them restates another.

| Field | Question | Values |
| --- | --- | --- |
| `kind` | Is this an availability fact at all? | `availability`, `announcement`, `policy`, `milestone` |
| `lifecycle` | Where in the release cycle? | `private_preview`, `limited_preview`, `public_preview`, `ga`, `legacy`, `deprecated`, `retired`, `suspended`, `restored` |
| `exposure` | How is the model exposed? | `underlying`, `specialist`, `catalogue`, `selectable`, `default`, `not_applicable` |

`lifecycle` and `exposure` apply only when `kind: availability`. The schema
enforces this, which is what stops an announcement of future availability from
ever entering a timeline or a lag calculation.

`selectable` is **derived** from `exposure` and appears only in generated
output. It is never authored, so it cannot contradict the exposure.

## Record shape

```yaml
- id: "foundry-opus5-availability-2026-07-24"
  kind: "availability"
  date:
    start: "2026-07-24"
    precision: "day"
  surface_id: "microsoft-foundry"
  model_ids: ["claude-opus-5"]
  model_claim: "specific"
  lifecycle: "ga"
  exposure: "catalogue"
  confidence: "confirmed"
  evidence_note: "..."
  sources:
    - publisher: "Microsoft"
      title: "..."
      url: "https://..."
      primary: true
      retrieved_at: "2026-07-27"
```

`model_claim` says whether the sources support each named model individually
(`specific`) or only the family as a group (`family`). A family announcement
lists its members without pretending each was separately dated.

Optional fields: `experience_ids`, `caveat`, `notes`, `tags`, `relations`,
`confidence_detail`.

## Dates

`date.precision` is `day`, `month` or `year`, and `date.start` must match it.
Use `date.end` for a rollout window. Never pad a month to a day to make
sorting or rendering easier — the build rejects a mismatch, and derived lag
becomes a range rather than a false point.

## Confidence

`confidence` is the headline and must equal the weakest part of the claim.
Where parts differ in strength, record that explicitly:

```yaml
  confidence: "supported"
  confidence_detail:
    model: "confirmed"
    date: "supported"
```

That case is common: the model attribution is first-party and certain while
the exact first date rests on retrospective documentation. It is not the only
shape. For the Claude Fable 5 suspension in Foundry the date is certain and it
is the *surface* that is soft, because no Microsoft-issued notice exists.

## Sources

Beyond publisher, title, URL, primary flag and retrieval date:

- `source_type` — `announcement`, `changelog`, `documentation`, `release_notes`,
  `news` or `other`
- `published_at` — when the source was published, if known
- `quote` — the verbatim sentence that attests the claim
- `supports` — which parts of the claim this source underwrites, from `date`,
  `model`, `exposure`, `lifecycle`, `policy`
- `note` — commentary about the source, not words taken from it
- `archived_url` — a snapshot, for sources likely to be edited in place

`quote` and `supports` earn their keep together. The build warns when a
`confirmed` event rests only on `documentation` sources, because current docs
prove a model is supported now and rarely prove when it first was. That
warning is suppressed when a documentation source carries a `quote` that
`supports` the date, since that means someone has checked the page actually
attests the date rather than merely the capability.

## Recording an ending

The dataset was built by tracking arrivals, and endings are published far less
consistently. Record them anyway: without a terminal event a model sits at the
last stage anyone recorded, and a renderer will show it as though nothing has
changed since.

The lifecycle runs `private_preview` -> `limited_preview` -> `public_preview`
-> `ga` -> `legacy` -> `deprecated` -> `retired`. The last three matter here:

| Stage | Meaning |
| --- | --- |
| `legacy` | Newer models exist and migration is advised; new deployments still allowed |
| `deprecated` | Existing customers only; new customers cannot start |
| `retired` | Removed from service |

**Where the date is published**, record it as normal. Foundry sets GA
retirement dates 18 months out at launch and publishes a schedule; OpenAI
publishes a shutdown table; GitHub publishes deprecation changelogs.

**Where a model simply disappeared**, do not invent a day. Bound it instead:

```yaml
  lifecycle: "retired"
  date:
    start: "2025-11-04"   # last date observed present
    end: "2026-02-17"     # first date observed absent
    precision: "day"
  confidence: "supported"
  caveat: "No withdrawal notice was published. Bounded by catalogue observation."
```

That is the honest shape — the removal happened somewhere in the window, and
the derived lag machinery already understands intervals.

**Where absence cannot be observed at all**, do not guess. A model used as an
`underlying` model on a surface that does not disclose it, such as Microsoft
365 Copilot, leaves no listing to disappear from. Open a `blocked` backlog item
saying no source can exist, so the question is not repeatedly reopened.

## Recording a promotion

Endings are under-published; so are middles. A model can arrive in preview with
a dated announcement and reach GA with none, leaving it parked at
`public_preview` years after the fact.

Azure OpenAI is the clearest case, and it is deliberate rather than an
oversight. Microsoft's lifecycle policy states that a GA model's retirement
date is set programmatically at launch and that there is **no separate
announcement**, and that preview deployments are force-upgraded to GA rather
than the GA being announced per model. The what's-new changelog announces
releases and previews; the retirement schedule reports current status without
dating the change. So the transition genuinely has no publication date to find.

Do not close that gap by inference. A model being absent from the preview list,
or a retirement schedule row implying it must have passed GA, dates nothing.
Open a `blocked` backlog item naming every affected model and surface, quote
the policy that makes the date unobtainable, and say in `target` that the
search has already been done. `blocked` items suppress lag the same way `open`
ones do, so the pair reports `unknown_open_research` rather than absence, and
`current-state.csv` shows a non-terminal state with an open question against it.

Exceptions exist and are worth recording when a vendor does announce one — GPT-4
Turbo with Vision reached GA on Azure with a dated post on 1 May 2024, and that
is a normal `lifecycle: "ga"` event.

## When Microsoft is not the one serving the model

Some catalogue entries are hosted by a third party. Kimi K3 reached Microsoft
Foundry on 28 July 2026 with Fireworks AI supplying the inference and Microsoft
supplying only deployment and governance; the catalogue names it "FW Kimi K3"
to say so.

Record these with `tags: ["partner_hosted"]` and name the host in the caveat.
The distinction is worth keeping because availability then depends on two
parties rather than one, and a withdrawal by either ends it. Unlike
`pre_release_access` this tag changes no validation behaviour — it is
descriptive only.

Keep the vendor as the model's creator, not the host. Kimi K3 is a Moonshot AI
model served by Fireworks, so its vendor baseline is still Moonshot's release.

## When a partner ships before the vendor

The build refuses an availability event on a non-vendor surface dated before
that model's vendor release, because it almost always means an announcement has
been recorded as availability or a date is wrong.

Occasionally it is true. GitHub Copilot ran on OpenAI Codex from 29 June 2021;
OpenAI opened the Codex private beta on 10 August. Microsoft had the model
first, and the resulting lag is legitimately negative.

Declare it in the data rather than working around it:

```yaml
  tags: ["pre_release_access"]
```

The guard then reports a `pre_release_access` warning instead of failing, so the
exception stays visible in the warning queue. Do not reach for the tag to
silence a date you have not checked — a test asserts the exact list of events
carrying it, so adding one is a deliberate act.

## Governance events

Admin and policy changes use `kind: policy`. They live on the surface that
exposes the control, usually an admin centre, and name their target in
`applies_to`:

```yaml
  kind: "policy"
  surface_id: "m365-admin"
  model_ids: []
  applies_to:
    vendor: "Anthropic"
    regions: ["EU", "EFTA", "UK"]
    surfaces: ["m365-copilot"]
    experiences: ["word", "excel", "powerpoint"]
```

They carry no `model_ids`, so a policy toggle can never be counted as a model
becoming available.

## Relationships

`relations` express directed links between events. Each is a verb read from
this event to the target. Inverses are derived, never authored, so the two
directions cannot disagree.

| Verb | Meaning | Implied date order |
| --- | --- | --- |
| `announced_by` | this was announced by the target | target not later |
| `previews_for` | this preview leads to the target's GA | target not earlier |
| `restores` | this restores what the target suspended | target strictly earlier |
| `supersedes` | this replaces the target | target not later |
| `part_of` | this belongs to the target umbrella event | target not later |
| `depends_on` | this requires the target to have happened | target not later |

The build enforces those orderings and rejects cycles. A cycle would assert
that two events each precede the other, which cannot be true and makes any
derived traversal non-terminating. Targets must exist and must not be the
event itself.

## Validation backlog

Backlog items are research targets, not timeline facts. Each has a `state`:

- `open` — still being researched
- `promoted` — became a canonical event; records `promoted_to`
- `rejected` — investigated and found unsupportable; records `resolution`
- `blocked` — cannot progress without a source that does not appear to exist

`rejected` matters: it stops the same question being reopened and decided
differently next time. A rejected item stays visible with its evidence
attached.
