# Dataset

`events.yaml` is the human-maintained source of truth.

The file contains canonical sourced events and a separate `validation_backlog`.
Backlog items are research targets, not timeline facts.

## Record shape

Each canonical event records:

- stable `id`, `date`, and `date_precision`
- vendor and a single model, or `models[]` for a true family/milestone event
- `platform.owner`, `platform.family`, `platform.product`, and optional experience
- structured `event.type`, availability, scope, and nullable selectability
- `confirmed` or `supported` confidence
- a concise evidence note, optional caveat/notes/tags/relationships
- one or more sources with publisher, title, HTTPS URL, primary status, and retrieval date

Use month or year precision when the evidence does not support a day. Never
invent a day merely to satisfy sorting or display code.

## Event classes

Typical `event.type` values include:

- `vendor_release`
- `platform_launch`
- `limited_preview`
- `public_preview`
- `underlying_model`
- `specialist_experience`
- `model_picker`
- `ga`
- `default_model`
- `catalogue_availability`
- `retirement`
- `admin_policy`
- `suspension`
- `restoration`

An event describes one claim on one date. Do not combine a preview and GA into
one row if both dates are known. Split model-specific platform availability
into separate records; retain `models[]` only for genuine family announcements
or multi-model product milestones.
