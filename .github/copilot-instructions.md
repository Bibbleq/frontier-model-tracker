# Copilot instructions: triaging a `candidate` issue

You are working on the **365Explained Frontier Model Tracker**, a sourced history of
when frontier and significant AI models were released by their vendors and when
they became available on tracked Microsoft surfaces. The dataset is the product.
Everything in `generated/` and `published/` is derived from three
human-maintained files in `data/`.

Most tasks you are given will arrive as an issue labelled `candidate`: a piece of
published news, filed automatically, that *might* be a dataset event. Your job is
to decide what the evidence actually supports and to leave the repository in a
state a human can merge or reject in one reading.

## Prime directive

**Never invent a date and never overstate confidence.**

The dataset exists to prevent two specific failures: false precision (a month
padded into a day, a rollout window collapsed to a point) and false equivalence
(a catalogue listing read as product availability, an announcement read as
general availability). Every rule below serves one of those two.

A corollary that is easy to miss: **absence of record is a published state, not a
gap to be filled.** If Microsoft never published a GA date, the honest output is
a `blocked` backlog item quoting the policy that makes the date unobtainable —
not a plausible date. `docs/methodology.md` has the worked example: Azure OpenAI
GA transitions genuinely have no publication date, so five model/surface pairs
sit in the backlog rather than being inferred from a retirement schedule.

"I could not verify this" is a first-class, successful outcome of triage.

## Read these before you touch anything

In this order, and actually read them — they are the specification, and these
instructions are only a summary:

1. `docs/data-contract.md` — what is promised to consumers, and the eight
   interpretation rules
2. `data/README.md` — the three axes, the record shape, dates, sources,
   modality, registry scope, how to record endings and promotions
3. `docs/methodology.md` — what derived analysis computes and what it refuses to
   compute
4. `CONTRIBUTING.md` — core rules, identifier stability, backlog states
5. `schema/events.schema.json` — the enforced shape
6. `docs/research-provenance.md` — how the existing record was built, and the
   editorial standard it was built to

Then look at how the last few merged data commits did it: `git log --oneline`,
then read the diffs for a promotion, a rejection and a registry addition.

## The three axes

Every event answers three separate questions. They are orthogonal. None restates
another, and collapsing any two is the central error this project exists to
prevent.

| Field | Question | Values |
| --- | --- | --- |
| `kind` | Is this an availability fact at all? | `availability`, `announcement`, `policy`, `milestone` |
| `lifecycle` | Where in the release cycle? | `private_preview`, `limited_preview`, `public_preview`, `ga`, `legacy`, `deprecated`, `retired`, `suspended`, `restored` |
| `exposure` | How is the model exposed? | `underlying`, `specialist`, `catalogue`, `selectable`, `default`, `not_applicable` |

`lifecycle` and `exposure` are permitted **only** when `kind: availability`; the
schema rejects them otherwise. That is the mechanism that keeps announcements out
of every timeline and lag calculation.

### The classic traps

Work through all of these before you write a line of YAML.

- **A catalogue listing is not product availability.** Foundry surfaces declare
  `counts_as: [microsoft, foundry]` and never `copilot`. A model in the Foundry
  catalogue has genuinely arrived on a Microsoft surface; it is not available in
  any Copilot product. Record it as `exposure: catalogue`.
- **A build-date version string is not availability evidence.** The Foundry
  retirement schedule carries version strings like `2026-04-09`. That is when the
  model was built, not when it arrived. Use it as a *floor* on a bounded window
  if you use it at all, say so in `caveat`, and never let it set the date. See
  the caveats on `microsoft-mai-image-2-2026-04` and
  `microsoft-mai-image-2e-2026-04`, and the commit "Date the MAI image previews
  from the evidence, not build strings".
- **An announcement is not GA.** A statement that a model *will* arrive is
  `kind: announcement`. The dataset once recorded a Microsoft statement that o1
  would come to Microsoft 365 Copilot, dated 92 days before OpenAI released the
  model. That is the failure the axis exists to stop.
- **GitHub Models is not GitHub Copilot.** Shared brand prefix, different
  surface. `github-models` counts as `microsoft` only.
- **The Microsoft 365 admin centre is not a Copilot surface.** An admin control
  appearing is not a model reaching users. Those are `kind: policy`, carry no
  `model_ids`, and name their target in `applies_to`.
- **A specialist or embedded experience is not model-picker availability.**
  Researcher, Analyst, Word, Think Deeper are `experience_ids` with
  `exposure: specialist` or `underlying` — not `selectable`.
- **Current documentation proves current support, not a first date.** A Learn
  page listing a model today says nothing about when it arrived.
- **Cross-platform inference is never sufficient.** That a model appeared on one
  surface is not evidence it appeared on another the same day, however plausible.
- **A date in a model's name is not a date.** `DeepSeek-V4-Flash-0731` was dated
  from the weights repository's creation timestamp; the `0731` was treated as a
  coincidence that agreed, not as the source.
- **A coverage date is not an event date.** An aggregator or newsletter reprints
  the vendor's present tense: "today we are releasing" means the day the vendor
  published, not the day the newsletter sent it, and never the day the candidate
  was flagged. The Grok 4.6 candidate reached triage on 17 August carrying
  "Today we are releasing Grok 4.6"; the release was the 12th, and a sibling
  changelog in the same batch had already proved the model public by the 14th.
  Do the weekday arithmetic too: "on Monday" in an article published Friday
  14 August is the 10th, not "around the 11th". If the vendor page is
  unreachable, bound the date from dated corroborating artefacts — never from
  when the news reached you. The same applies to `published_at`: the flagging
  timestamp in the issue is not a publication date, and inferring one from it
  put a wrong date on a primary source in the 17 August batch.
- **On a vendor-baseline surface, `exposure` is `not_applicable`.** Vendor events
  exist only to anchor lag. The build warns on `selectable` or `default` there.

## Confidence, verbatim from the contract

These two definitions are the dataset's own, in
`data/events.yaml` under `metadata.confidence_definitions`:

- **`confirmed`** — "A primary source explicitly supports the material event date
  and scope."
- **`supported`** — "Strongly supported, but the exact first date relies on
  retrospective/current documentation or paired evidence."

Rules that follow from them:

- Anything meeting neither threshold stays **out** of `events` entirely. It is a
  backlog item, not a low-confidence event.
- `confidence` is the headline and **must equal the weakest part of the claim**.
  Where parts differ, record that in `confidence_detail` (`date`, `model`,
  `exposure`, `lifecycle`). The build fails if `confidence: confirmed` sits above
  a `supported` detail.
- `confidence: confirmed` requires at least one source with `primary: true`. The
  build fails otherwise.
- A `confirmed` event resting only on `documentation` sources earns the
  `unquoted_documentation` warning unless a primary source carries a `quote`
  whose `supports` includes `date`. If you cannot quote the page attesting the
  date, the claim is `supported`, not `confirmed`.

## The decision tree

Read the issue body. It carries a headline, a source URL, the publication, an
excerpt from the primary source, and Lodestone provenance identifiers. The
excerpt is your starting evidence; the Lodestone identifiers are internal
plumbing and **must never appear anywhere in `data/`** — the dataset cites public
URLs only, exactly as `docs/research-provenance.md` describes rejecting the
editorial backlog's internal citation tokens.

Then choose one of three outcomes. Say which one you chose, and why, in the PR
body or the issue comment.

### (a) Schema-valid event with an explicit date and scope → open a data PR

Take this path only when *all* of the following hold:

- the source is public and fetchable, and preferably first-party
- it supports a date at a precision you can name (`day`, `month` or `year`), or a
  window you can bound with `date.end`
- the surface is unambiguous and already in `data/platforms.yaml` (or belongs
  there)
- the model is unambiguous and resolvable to one registry id
- you can set `kind`, and where `kind: availability`, both `lifecycle` and
  `exposure`, without guessing any of them

Add the event to `data/events.yaml`. See the mechanical steps below.

For a complete worked promotion, read `github-copilot-mai-code-1-1-flash-2026-08-11`
in `data/events.yaml` (PR #57): a `ga` lifecycle call on "rolling out" wording made
honest by an explicit `caveat`, a `confidence_detail` split (`date: confirmed`,
`lifecycle: supported`) resolving to overall `supported` under the weakest-part
rule, per-plan access differences captured in `evidence_note`, and the paired
backlog transition (`state: promoted`, `resolution`, `promoted_to`) with its
unswept-window sweep item. When the evidence meets the five conditions above,
**promotion is the correct outcome** — do not choose the backlog because it is
easier to defend; an under-promoted dataset is wrong in a quieter way.

### (b) Real but underdated or underscoped → add a validation backlog item

This is the *common* outcome, and it is a success, not a fallback. Take it when
the claim is probably true but the evidence will not carry a canonical event: no
date, a date only from current-state documentation, an ambiguous surface, an
unclear exposure, or two sources that contradict each other.

The backlog lives in the **same file as the events**: `data/events.yaml`, in the
top-level `validation_backlog:` array (it begins after the last event, currently
around line 6165). It is not a separate file. `generated/validation-backlog.csv`
is derived from it and must never be edited by hand.

A new item is `state: "open"` and needs `id`, `state`, `working_claim`, `reason`
and `target`, plus `model_ids` and `surface_ids` where known:

```yaml
  - id: "foundry-example-model-arrival-dates"
    state: "open"
    working_claim: "One sentence stating the claim as it would be recorded if it were provable."
    reason: "Why it is not recorded: which part is unevidenced, what each source does and does not establish."
    target: "What specific artefact would resolve it, and what has already been searched."
    model_ids: ["example-model"]
    surface_ids: ["microsoft-foundry"]
    sources:
      - publisher: "Publisher"
        title: "Title"
        url: "https://..."
        primary: false
        retrieved_at: "YYYY-MM-DD"
        published_at: "YYYY-MM-DD"
        source_type: "news"
        quote: "The sentence that attests as much as is attested."
```

Two things to get right:

- **Always name `surface_ids` on an open item.** An open item naming a surface
  suppresses the lag answer for that model and tier, so the output reports
  `unknown_open_research` rather than rendering a research gap identically to
  evidence of non-availability. An open item with no surface earns the
  `backlog_without_surface` warning and does no work.
- **Write `target` so the next person does not redo your search.** Say what you
  checked and found nothing in. Negative evidence is worth recording.

Attach the sources you did find. A backlog item with the evidence attached is far
more useful than a bare question.

### (c) Duplicate, out of scope, or not a model event → comment and close

Take this path when the candidate is:

- already recorded — say which event id or backlog item covers it
- already `rejected` in the backlog — say so and leave the rejection standing;
  `rejected` items exist precisely so a settled question is not reopened and
  decided differently
- not about a model reaching a vendor or a tracked Microsoft surface: pricing,
  benchmarks, funding, partnerships without availability, feature launches, a
  fine-tuning service rather than a model
- a leak or a third-party sighting of something unreleased — Microsoft
  announcing nothing means there is no announcement to record; recording it
  "would turn a leak into a rollout" (see the `mai-realtime-voice-unreleased`
  backlog item)
- outside the registry's scope decisions — read the "Registry scope" and
  "Modality models" sections of `data/README.md` before deciding something is
  out of scope

Comment with the reasoning and the rule it rests on, then close. Do not open an
empty PR to say nothing changed.

If your harness can only answer with a pull request, open a no-change PR that
carries the comment you would have left: title it
`Triage #N: … — close as <duplicate|out of scope|rejected>`, state the outcome,
the rule it rests on and the covering event or backlog id in the body, and use
**no** closing keyword — a human closes the PR and the candidate issue together.
Tick **only** the checklist lines for steps you actually ran, which for a
no-change PR is usually none of them. A ticked build step that never ran is a
false attestation, and it is the first thing a reviewer checks.

## Mechanical steps for a data PR

Work in this order. The order matters.

1. **Registries first.** Resolve the model to an existing id in
   `data/models.yaml` and the surface to an existing id in
   `data/platforms.yaml`. Search `aliases` as well as `display_name` — Microsoft
   and GitHub often publish a model under a different name. **Never create a new
   spelling of a model that is already registered.** The build fails on unknown
   ids, which is what stops a typo silently creating a second identity, but it
   cannot stop you registering a duplicate under a new id. If the model is
   genuinely new, add it with `id`, `display_name`, `vendor`, and the
   classification fields (`series` via `generation`/`model_line`, `family`,
   `modality`, `scope`) that the existing entries around it use. Vendor must
   match the classification's vendor; the build checks.
2. **Identifiers are permanent.** Event ids are lowercase letters, digits and
   hyphens, and read surface-model-date:
   `foundry-opus5-availability-2026-07-24`,
   `github-gemini3-6-flash-2026-07-21`. Once merged, an id is never renamed and
   never reused. If you get one wrong, fix it in the same PR.
3. **Edit `data/events.yaml`.** Insert the event in the correct position: the
   build **fails** unless `events` is sorted by `(date.start, id)`. Required
   fields are `id`, `kind`, `date`, `surface_id`, `model_ids`, `confidence`,
   `evidence_note`, `sources`; plus `model_claim` whenever `model_ids` is
   non-empty, and `lifecycle` + `exposure` whenever `kind: availability`.
4. **Match date precision to the evidence.** `date.start` must match
   `date.precision` exactly — `2026-04` with `precision: month`, not `2026-04-01`
   with `precision: day`. Use `date.end` for a rollout or observation window
   rather than picking a point inside it. A day-precision date on the first of a
   month is flagged unless a source's `published_at` is that exact day or a
   `quote` lists `date` in its `supports`; a test enforces this over the whole
   dataset, so an unattested first-of-month date will fail CI.
5. **Cite properly.** Every source needs `publisher`, `title`, `url` (https) and
   `primary`. `retrieved_at` is schema-required on every source and the build
   fails without it, so never omit it — omitting it for an unfetched source is
   how PR #66 broke. When you fetched the URL in this session, the field attests
   the retrieval. When the fetch failed or was never attempted, set it to the
   date of the attempt and put the honesty in `note`: that the fetch 403ed or
   the host would not resolve, and where any `quote` actually came from — an
   issue excerpt is not the page. A `retrieved_at` whose note discloses a failed
   fetch is honest; a bare one on a page you never saw is not. Add `published_at`, `source_type`, `quote` and
   `supports` wherever you can — a verbatim `quote` with `supports: ["date"]` is
   what turns current documentation into date evidence. **Each claim cluster the
   event asserts (date, model, scope/plans, lifecycle) should have its own
   verbatim quote where the source provides one** — a scope claim resting only on
   your paraphrase is the weakest link in the diff. For `documentation` and
   `release_notes` sources, look up an existing Wayback snapshot and set
   `archived_url`; use the read-only CDX API
   (`https://web.archive.org/cdx/search/cdx?url=<url>&filter=statuscode:200&limit=5`),
   build the link as `https://web.archive.org/web/<timestamp>/<original>`, and
   do **not** try to create snapshots. Avoid the availability API
   (`archive.org/wayback/available`): from some networks it 429s every request
   regardless of volume, and an instant 429 on a first request is the endpoint
   refusing you, not a rate limit to wait out. Missing archives are a warning,
   not a failure, and the queue is meant to shrink.
6. **Mind `research_cutoff`.** `data/events.yaml` declares `updated` and
   `research_cutoff` at the top. If your event is dated after the current
   `research_cutoff`, that is **always two changes, never one** — a PR that moves
   the cutoff without its companion item is incomplete and will be sent back:
   1. move the cutoff to cover the event's date, and
   2. open an `open` backlog item recording that the intervening window is
      unswept, so absence of other events in that window is not read as evidence.
   `sweep-2026-07-29-to-08-06` and `sweep-2026-08-07-to-08-11` are the shapes to
   follow. Update `updated` to the date of the change.

   Before moving the cutoff, look at the other open triage PRs. If a sibling PR
   already moves it to or past your event's date, leave the cutoff alone and say
   so in your PR body — whoever moves it furthest carries the sweep item. Two
   PRs in the 17 August batch each moved it independently and opened overlapping
   sweep items, which cost a human a manual reconciliation of both.
7. **Rebuild.** `python -m pip install -r requirements.txt` then
   `python scripts/build.py`. It validates all three files against their schemas,
   resolves every id, checks relations, lifecycle ordering, suspension pairs and
   vendor baselines, and rewrites `generated/`.
8. **Commit the regenerated `generated/` tree.** CI hard-fails on stale output:
   `git diff --exit-code -- generated/` runs in both workflows. Never hand-edit
   anything under `generated/`, and never touch `published/` — those snapshots
   are immutable by contract.
9. **Run the tests.** `python -m unittest discover -s tests -v`. They pin the
   invariants CI pins, including the exact list of events tagged
   `pre_release_access`, that every first-of-month date is attested, and that the
   live dataset produces no unexpected split-ending warnings.
10. **Read the warnings.** The build prints them and counts them in
    `generated/status.json`. New warnings are acceptable when they are honest
    (`missing_archive` on a source with no snapshot yet) and unacceptable when
    they are telling you something is wrong (`selectable_on_vendor_surface`,
    `vendor_ending_split`). Explain any new warning in the PR body.

### PR body

- Say which of the three outcomes you took, and why.
- **Cite the source URL for every factual claim you make.** A claim without a URL
  does not belong in the diff or the description.
- State the previous and the new interpretation explicitly where you change an
  availability or lag claim.
- When a source splits access by plan or tier (auto model selection for some
  plans, manual selection for others, an admin policy gate), state your
  flattening decision explicitly: one event with the differences in
  `evidence_note`/`caveat`, or separate events per exposure — and why. The axes
  exist to prevent silent flattening; a deliberate, argued flattening is fine.
- Reference the triggering issue with a closing keyword (`Fixes #N` / `Closes #N`)
  whether you are promoting to a canonical event **or** adding a backlog item:
  either way the candidate has been triaged and the issue's job is done. For a
  backlog add, the `validation_backlog` entry becomes the open handle for the
  research question — one tracker per claim, not two. Only a pure rejection
  needs no linkage keyword; close the issue with the explanatory comment instead.
- Tick the checklist in `.github/pull_request_template.md` honestly.
- Note anything you could not verify and what a human should check.

Keep commit messages in the house style: a one-line summary of what the evidence
supports, then prose explaining what each source does and does not establish, and
what was deliberately *not* recorded.

## Verification behaviour

- The excerpt in the issue body is a starting point, not the evidence. Fetch the
  source URL and read the page.
- **The batch is evidence.** Before you write a date claim, look at the other
  open candidate issues and triage PRs for the same model, using whatever GitHub
  access you have; a sibling source may bound or refute your date. A changelog
  showing a model on a Microsoft surface on the 14th makes any later vendor
  release date impossible — that contradiction shipped in the 17 August batch
  because each candidate was triaged blind to its siblings. If you cannot list
  the open candidates, say so in the PR body.
- Cross-verify against the official domain where one exists and is reachable:
  `microsoft.com`, `learn.microsoft.com`, `techcommunity.microsoft.com`,
  `devblogs.microsoft.com`, `blogs.microsoft.com`, `microsoft.ai`, `github.blog`,
  `openai.com`, `anthropic.com`, and the vendor's own newsroom or docs.
- **If a source you need is unreachable, do not guess.** Your options are
  `confidence: supported` with the reliance stated in `caveat`, or a backlog item
  saying precisely what needs manual verification. Say in the PR body or comment
  which sources you could not reach.
- Where two sources disagree, do not pick one. Record both in a backlog item and
  say what the contradiction is. Unresolved contradictions stay in the backlog by
  rule.
- Where the source is undated or client-rendered, say so in a source `note`
  rather than silently trusting it.

## Guardrails

- **Smallest possible diff.** One candidate, one decision, the minimum lines that
  express it, plus the regenerated `generated/` tree.
- **No refactors.** Do not reformat YAML, reorder keys, rewrap prose, or tidy
  files you did not need to change. Do not touch `scripts/` or `tests/` unless
  the task is explicitly about them.
- **Never change a schema, the data contract, or the interpretation rules.** The
  files under `schema/`, `docs/data-contract.md` and the `metadata` block of
  `data/events.yaml` encode versioned human decisions. If a candidate seems to
  require a schema change, that is a finding to report in a comment, not a change
  to make.
- **Never edit `published/`.** Snapshots are immutable; their bytes never change.
- **Never rename or reuse a merged identifier.**
- **British English** throughout — "catalogue", "licence" as a noun, "organise",
  "behaviour". The dataset's own prose is British; match it. Product names keep
  their official spelling ("Microsoft 365 admin centre" is the registry's
  `display_name`, so use it).
- **Licensing and attribution stay as they are.** The dataset under `data/` and
  its generated representations are CC BY 4.0; the code is MIT. Do not alter
  `LICENSE`, `LICENSE-DATA`, or the attribution string the manifest carries.
- The project is independent and not affiliated with Microsoft, OpenAI, Anthropic
  or GitHub. Never write prose implying otherwise.

## A note on model choice

Triage here is judgement work, not code generation: reading sources critically,
deciding whether evidence supports a date, and choosing between an event, a
backlog item and a rejection. Run these tasks on a **frontier reasoning model**
rather than a flash- or mini-tier one. A fast model will produce plausible dates,
and a plausible date is the single worst output this repository can accept.

If you find yourself reaching for an inference to fill a gap, stop. The backlog
is the right answer.
