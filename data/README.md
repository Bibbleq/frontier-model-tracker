# Dataset

`events.yaml` is the human-maintained source of truth.

The initial file contains only a small set of seed events used to validate the
schema and workflow. The researched 2021–2026 history will be imported after
each event has been reconciled against its public evidence.

## Event classes

Typical `event_type` values include:

- `vendor_release`
- `platform_launch`
- `limited_preview`
- `public_preview`
- `underlying_model`
- `specialist_experience`
- `model_picker`
- `general_availability`
- `default_model`
- `catalog_availability`
- `retirement`
- `policy_change`
- `suspension`
- `restoration`

An event describes one claim on one date. Do not combine a preview and GA into
one row if both dates are known.
