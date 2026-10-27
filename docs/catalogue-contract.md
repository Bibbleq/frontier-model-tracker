# Catalogue contract, version 2

This document describes three folders of machine-written catalogue snapshots
and the file shapes inside them. It is separate from the dataset's
[data contract](data-contract.md): the dataset is curated research, whereas
these folders are captured listings of what a public API returned.

**Catalogue contract version 2.**

These folders are append-only but not versioned; they sit outside the immutable
`published/` promise of the data contract.

## What the folders hold

| Folder | Contents |
| --- | --- |
| `observations/` | Diff-only observation files: one file per run of one source in one region that saw at least one change |
| `checkpoints/` | Full-state checkpoints: a seed that starts a chain, then one per month |
| `status/` | Two status exports, `arm.json` and `regions.json`: a status report and reference data, never evidence |

The first source is the Azure Resource Manager Models API, which the paths call
`arm`. The catalogue watcher polls it for every Azure region four times a day.

## Who writes them

The `bibble-envoy[bot]` GitHub app writes these folders and commits directly to
`main`. Nothing here is hand-edited. The watcher's own state is private and is
not part of this contract; the files record only what a run saw and what
changed.

## Layout

```text
observations/arm/<region>/<YYYY>/<MM>/<timestamp>.json
checkpoints/arm/<region>/<timestamp>.json
status/arm.json
status/regions.json
```

`<region>` is the ARM lowercase region identifier, for example `uksouth`.
`<timestamp>` is the run's UTC time with hyphens in place of colons, for
example `2026-10-27T12-30-44Z`, because Windows cannot create a file whose
name contains a colon. The `observed_at` field inside the file keeps the
ordinary form, `2026-10-27T12:30:44Z`.

The shapes are published as JSON Schema beside the dataset schemas:

| Schema | Describes |
| --- | --- |
| `schema/observation.schema.json` | One observation file |
| `schema/checkpoint.schema.json` | One checkpoint file |
| `schema/lifecycle-mapping.json` | The stage vocabulary table: the API's `lifecycleStatus` values, the portal words and the dataset's `lifecycle` values |

`lifecycle-mapping.json` is a vocabulary table, not a JSON Schema. The watcher's
normaliser and the replay both read it, so they cannot disagree.

## Write on change, and how silent runs are attested

A run that sees nothing new writes no file. A chain of files is still enough to
show that the silent runs happened:

- `previous_run_at` is the last successful run of the same source and region,
  and the "absent at" edge of every first-seen window in the file.
- `runs_since_previous_file` counts the silent successful runs between the
  previous file and this one.
- `keys_present` is the full list of model keys the run saw, not only the
  changed ones, so a key missing from it is an absence the run saw.
- `previous_file` links to the previous observation file (or is null for the
  first file after a checkpoint), and `checkpoint` names the seed or monthly
  checkpoint the chain replays from.
- `snapshot_sha256` lets a replay check it reached the same state as the
  watcher without the private snapshot being published.
- Files are written in a canonical order so two writers produce the same bytes
  for the same run: `keys_present` sorted, `changes` sorted by `kind` then
  `model_key`, checkpoint `entries` sorted by `model_key`, object keys in the
  order the schemas list them. Observation files are pretty-printed with two
  spaces; checkpoints are minified. A reader must not depend on the order.

## Honesty rules

These are interpretation rules for anything that reads or renders the files.

- **An observation dates the observation, never the change.** `observed_at` is
  when a run saw something. It is never the day a model arrived or left.
- **Always a window, run to run.** Every change carries `window_start` and
  `window_end`: the run that last saw the old state and the run that first saw
  the new one. Render it as a window.
- **Presence is strong, absence is weak.** A listing is one subscription's view
  (`observed_from` says which). A model can be visible to a subscription that
  has deployed it before and absent from a new one, so every ARM absence is
  recorded with `absence_strength: weak`.
- **The stage value sits beside its portal word.** Microsoft's API and its
  portal use different words for the same stage: the API's `Deprecating` is the
  portal's "Deprecated", and the API's `Deprecated` is the portal's "Retired".
  Show the raw value and the portal word together, from
  `schema/lifecycle-mapping.json`. A value the table does not map is recorded
  raw and marked unmapped, never guessed.
- **Version strings are build identifiers, never dates.** `gpt-chat-latest@2026-10-07`
  is a name and a build label; the model key keeps the API's spelling and case.
- **Capacity is a moment.** A capacity figure is what the API reported at
  `capacity_at`. It is absent, not zero, when it was not read.

## The derived catalogue

The Pages site publishes a catalogue product built from these folders by
`scripts/build_catalogue.py`. Start at its manifest:
<https://bibbleq.github.io/frontier-model-tracker/catalogue/manifest.json>

| File | Origin | Contents |
| --- | --- | --- |
| `catalogue/manifest.json` | derived | `catalogue_contract_version`, the first and latest observation times, the licence, and the size and SHA-256 of every file below |
| `catalogue/intervals.json` | derived | Presence windows and state segments, replayed from `checkpoints/` and `observations/` |
| `catalogue/regions.json` | export | `status/regions.json`, byte for byte |
| `catalogue/status.json` | export | `status/arm.json`, byte for byte |

The two exports are copied so a reader can verify them against the same
manifest; they keep their meaning: reference data and a status report, never
evidence.

The build is a replay, not a summary. For each region it starts from the seed
checkpoint, applies every observation file in order, and at each file
recomputes the snapshot hash from the replayed state, using the watcher's
formulas:

```text
fingerprint     = sha256( json.dumps(watched, sort_keys=True, separators=(",", ":")) )
snapshot_sha256 = sha256( json.dumps([[model_key, fingerprint], ...] sorted by model_key,
                                     separators=(",", ":")) )
```

It also checks the entry and cell counts, each file's `previous_file` and
`checkpoint` links, and that every later checkpoint restates exactly the
replayed state. A chain that does not add up fails the build, so nothing is
published from a record that does not reconcile. The output carries no build
time: the same inputs give the same bytes, and anyone can run the script on a
clone to reproduce it. It is published, never committed.

### `intervals.json`

| Field | Meaning |
| --- | --- |
| `first_observed_at`, `observed_through` | The earliest and latest run any committed file records. Nothing before `first_observed_at` was observed. |
| `regions` | Per region: its own `first_observed_at` and `last_observed_at`, the `observed_from` label, how many observation files and checkpoints it has, and how many entries are present. `last_observed_at` is the latest file, not the latest run; quiet runs write nothing, and the status export says when a region was last polled. |
| `models` | Per `model_key`: `name`, `version`, `format`, and `tracker_model`, the dataset's model id when `data/models.yaml` lists the ARM name or key in that model's `aliases`, else null. No other link is made. |
| `cells` | One row per region, model key, deployment type and unbroken presence. `seen_from` is `{after, by}`: the last run known without it and the first run that saw it; `after` is null for anything present at the region's first observation. `seen_until` is null while present, else `{last_seen, absent_by, confirmed_at}`. `sku_deprecation_date`, `capacity` and `capacity_at` are the latest values the files carry. |
| `cells[].absent_unconfirmed_since` | Present only on an open row whose key has dropped out of the listing but whose absence is not yet confirmed. The row stays open until a confirmed absence closes it. |
| `states` | One row per region and model key each time the stage, the deprecation dates, the default-version flag or the capabilities change. `from` is the same `{after, by}` window. The raw `lifecycle_status` sits beside `lifecycle_portal` and the dataset's `dataset_lifecycle`, from `schema/lifecycle-mapping.json`. Capabilities live here because one key can list different capabilities in different regions. |

### Reading it

- **Presence on a day.** A cell row covers a moment *t* when `seen_from.by` ≤
  *t* and either `seen_until` is null or *t* < `seen_until.absent_by`. Between
  `seen_from.after` and `seen_from.by` the arrival happened at an unknown
  point: render the window, never a date.
- **State on a day.** For a region and key, the state at *t* is the latest
  `states` row whose `from.by` ≤ *t*.
- **A flap is not a gap.** A key that drops out and returns before its absence
  is confirmed keeps one unbroken row, as the watcher records it.
- **Capacity is a moment, and may be old.** Capacity arrives with an arrival or
  a monthly checkpoint. A `capacity_changed` change carries its figures only in
  its `note`, whose wording is not part of this contract, so the replay does not
  read them. Always show `capacity_at`.
- **The honesty rules above apply.** Observed is not confirmed, absence is
  weak, and every row is one subscription's view.

## What is not in the contract

- The watcher's private state, snapshots and configuration.
- The wording of any `note` field.

## Caching and polite use

The files live in the repository and are served by GitHub. Cite a file by a
commit-pinned raw URL, for example
`https://raw.githubusercontent.com/Bibbleq/frontier-model-tracker/<sha>/observations/arm/uksouth/2026/10/2026-10-27T12-30-44Z.json`,
not by a branch URL.

- Do not poll more than once an hour. The watcher runs four times a day.
- Cache at the appropriate application boundary rather than fetching the same
  file separately for every request.
- Prefer a single clone or archive download to many raw file requests.

## Licence and attribution

The catalogue files are licensed **CC BY 4.0**, the same terms as the dataset,
and any published use must attribute **CtrlAltBen Frontier Model Tracker**. They
are machine-captured records of public API listings rather than curated data.
The code in this repository is **MIT**.

The catalogue files record what a public API listed. They are a sourced
research project, not official product documentation. Not affiliated with
Microsoft, OpenAI, Anthropic or GitHub.

## Change log

| Version | Change |
| --- | --- |
| 1 | Initial catalogue contract: observation and checkpoint schemas, the lifecycle mapping table, and the `observations/`, `checkpoints/` and `status/` folders. |
| 1, amended 27 October 2026 | File names use hyphens in the time part (`2026-10-27T19-30-00Z.json`), so the repository can be cloned on Windows. The 35 seed checkpoints were renamed with their bytes unchanged; no observation file had been written. The `previous_file` and `checkpoint` patterns in the observation schema follow. |
| 2 | The derived catalogue: `scripts/build_catalogue.py` replays the chain, proves each file against its snapshot hash and publishes `catalogue/manifest.json`, `intervals.json` and the two exports on the Pages site. The observation and checkpoint shapes are unchanged. |
