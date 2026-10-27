# Checkpoints

Full-state catalogue checkpoints, written by the catalogue watcher: a seed checkpoint that starts a chain of observation files, then one monthly checkpoint per source and region. They are machine-captured catalogue snapshots, not curated data.

This folder starts empty apart from this README. Files are laid out as `checkpoints/arm/<region>/<timestamp>.json`, where `<timestamp>` is the run's UTC time with hyphens in place of colons, for example `2026-10-27T19-30-00Z`.

Cite a file by a commit-pinned raw URL: `https://raw.githubusercontent.com/Bibbleq/frontier-model-tracker/<sha>/checkpoints/...`

Licensed CC BY 4.0 (see [LICENSE-DATA](../LICENSE-DATA)); attribute "CtrlAltBen Frontier Model Tracker". The file shape is described in [docs/catalogue-contract.md](../docs/catalogue-contract.md).
