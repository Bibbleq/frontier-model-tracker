# Generated outputs

Files in this directory are generated from `data/events.yaml` by
`scripts/build.py`. Do not edit generated data manually.

- `manifest.json` is the machine-readable form of [`../docs/data-contract.md`](../docs/data-contract.md): both version numbers, and a byte length and SHA-256 for every published payload file. Consumers fetch it first to check versions and skip unchanged downloads.
- `events.json` contains schema-v3 metadata, canonical events, and the validation backlog.
- `events.csv` is the flattened canonical event timeline. Model and surface IDs appear alongside their resolved display names, and `selectable` is derived from `exposure` rather than authored.
- `validation-backlog.csv` is the flattened research queue and must not be presented as confirmed history. Its `sources` column carries any evidence already gathered against a target; a populated row is still an open question, not a claim.
- `status.json` is a dashboard-oriented summary: totals, structured build warnings, coverage gaps and lag answerability. It carries no timestamp, so rebuilds stay byte-identical.
- `models.csv` and `surfaces.csv` export the registries, each with an `event_count` so gaps in coverage are visible without a query.
- `lag.csv` is derived adoption lag, recomputed on every build and never stored in source data. Read `certainty` before `lag_days_min`: a row may be `exact`, a `range` when a date is only known to a month, or one of three flavours of unknown. See [../docs/methodology.md](../docs/methodology.md).

Generated dataset representations are licensed under CC BY 4.0; see
`../LICENSE-DATA`.
