# Generated outputs

Files in this directory are generated from `data/events.yaml` by
`scripts/build.py`. Do not edit generated data manually.

- `events.json` contains schema-v3 metadata, canonical events, and the validation backlog.
- `events.csv` is the flattened canonical event timeline. Model and surface IDs appear alongside their resolved display names, and `selectable` is derived from `exposure` rather than authored.
- `validation-backlog.csv` is the flattened research queue and must not be presented as confirmed history. Its `sources` column carries any evidence already gathered against a target; a populated row is still an open question, not a claim.

Generated dataset representations are licensed under CC BY 4.0; see
`../LICENSE-DATA`.
