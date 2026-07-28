# Display layers

**Display layers live in their own repositories, starting with the WordPress
plugin.** This directory is kept as a pointer.

A display layer consumes the published data contract rather than reading
anything in this repository:

- Contract: [`docs/data-contract.md`](../docs/data-contract.md)
- Manifest: <https://bibbleq.github.io/frontier-model-tracker/manifest.json>
- Pinned tree: <https://bibbleq.github.io/frontier-model-tracker/v3/>

## Why they are separate

**Licensing.** This repository is MIT code and CC BY 4.0 data. A plugin
distributed through wordpress.org must be GPLv2-or-later, and CC BY 4.0 is not
GPL-compatible. Fetching the data at runtime keeps the two apart: the plugin is
GPL code, the dataset stays CC BY and is consumed with attribution rather than
bundled. It also lowers the bar for contributions — someone improving a
renderer never touches the dataset, and someone correcting a date never touches
PHP.

**Release cadence and tooling.** The dataset changes weekly; a renderer changes
rarely. WordPress.org releases plugins as versioned zips through SVN, which is
alien to a data repository, and plugin CI is PHP where this repository's is
Python.

**It proves the contract.** A display layer that can only reach the published
URL is a real test that the contract is sufficient for a third party. Anything
inside this repository could accidentally depend on a file that is not
published.

## The boundary

> This repository owns the data and its canonical HTTP endpoint. Anything that
> renders that endpoint inside a third-party platform lives elsewhere.

`web/` stays here because the GitHub Pages site *is* the published endpoint and
has to deploy from this repository. It is a viewer over the contract, not part
of it.

## Building a consumer

Read [`docs/data-contract.md`](../docs/data-contract.md) first. It states which
paths are stable, how versions and deprecation work, and the obligations a
renderer has to meet — chiefly that announcements must not be drawn as
availability, catalogue availability is not Copilot availability, partial dates
must not be rendered as exact ones, and unresearched gaps must not be shown as
findings.
