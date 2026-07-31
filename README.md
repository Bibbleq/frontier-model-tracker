# 365Explained Frontier Model Tracker

An independent, community-maintained history of frontier and significant AI model availability across the Microsoft AI stack.

The project tracks when models are released by their vendors and when they become available across Microsoft surfaces including:

- Microsoft 365 Copilot
- Microsoft Copilot Studio
- GitHub Copilot
- GitHub Models
- Microsoft Foundry / Azure AI Foundry / Azure OpenAI

The aim is to distinguish *what happened* from *how it was exposed*: underlying model use, specialist experiences, model-picker availability, previews, GA, defaults, retirements, catalogue availability and admin/policy changes are recorded as separate events.

## Project status

The structured dataset is the source of truth. It contains **over 140 canonical events** spanning June 2020 onward, alongside dozens of validation targets undergoing further research. Exact current totals, warning counts and coverage gaps are published in [`generated/status.json`](generated/status.json).

Treat the dataset as a sourced research project rather than official product documentation.

## Repository layout

```text
data/              Human-maintained source data: model and surface registries, events
docs/              Data contract, methodology and research provenance
generated/         Machine-generated JSON/CSV outputs
published/         Immutable contract and dataset snapshots
schema/            JSON Schema for event validation
scripts/           Build and validation tooling
.github/           Contribution and validation workflows
```

## Consuming the data

The generated outputs are published to a stable URL on every change to `main`.
They are a standalone data source: downstream applications decide independently
how to query, analyse or present them.

Start at the manifest: <https://bibbleq.github.io/frontier-model-tracker/manifest.json>

[`docs/data-contract.md`](docs/data-contract.md) is the promise consumers can
rely on: which paths are stable, how versioning and deprecation work, and the
interpretation rules consumers must preserve so the distinctions in the data are
not flattened or misrepresented.

## Event model

A model may have several events on the same surface: vendor release, limited/public preview, confirmed underlying use, selectable model, specialist experience, GA, default, retirement, catalogue availability, or an admin/policy change.

This prevents a catalogue listing from being mistaken for GitHub Copilot availability, or a specialist Microsoft 365 agent from being mistaken for general Copilot Chat model selection.

Schema v3 separates three orthogonal axes: `kind` (is this an availability fact, an announcement, a policy change or a milestone), `lifecycle` (where in the release cycle) and `exposure` (underlying, specialist, catalogue, selectable or default). Models and surfaces are referenced by stable IDs from `data/models.yaml` and `data/platforms.yaml`, so a model cannot appear under two spellings and a product rename does not fragment its history. The model registry also distinguishes broad numbered `generation`, recurring `model_line`, narrower marketed `family`, and evidenced `supersedes` links; membership in the first three never implies technical ancestry or replacement. Unresolved claims live in `validation_backlog` rather than being assigned invented dates or scopes.

## Evidence policy

Every availability claim should be backed by a public source. Primary vendor, Microsoft, GitHub and product-documentation sources are preferred.

`confirmed` means a primary source explicitly supports the material date and scope. `supported` is reserved for claims backed by strong evidence where the exact first date relies on retrospective or current documentation. Claims that do not meet either threshold stay outside the canonical event list.

The dataset records **publicly documented availability**. It does not claim to represent internal deployment dates, undocumented service architecture or roadmap information.

Corrections are welcome through pull requests and issues. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licensing

Source code in this repository is licensed under the **MIT License**. See [LICENSE](LICENSE).

The structured research dataset under `/data` and generated representations derived from it under `/generated` are licensed under **Creative Commons Attribution 4.0 International (CC BY 4.0)**. See [LICENSE-DATA](LICENSE-DATA).

Third-party names, trademarks, linked source material and quoted content remain subject to their respective owners' rights.

## Independence

365Explained Frontier Model Tracker is an independent community project. It is not affiliated with, authorised, sponsored or approved by Microsoft Corporation, OpenAI, Anthropic, GitHub or any other model provider referenced in the dataset.

Microsoft, Azure, Microsoft 365, Copilot, GitHub and other product names are used descriptively to identify the products and services being tracked.
