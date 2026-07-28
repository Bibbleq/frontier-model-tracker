# Display layers

**Display layers live in their own repositories, starting with the WordPress
plugin.** This directory is kept as a pointer.

A display layer consumes the published data contract rather than reading
anything in this repository:

- Contract: [`docs/data-contract.md`](../docs/data-contract.md)
- Live manifest: <https://bibbleq.github.io/frontier-model-tracker/manifest.json>
- Immutable snapshot: <https://bibbleq.github.io/frontier-model-tracker/c1/v3/>

**A display layer should read the live tree, not the snapshot.** The snapshot's
bytes never change, which is what makes it citable, but it also means it never
receives a correction. `dataset_version` only moves when the *shape* of the
records changes, which is rare, so a snapshot can sit unchanged for a long time
while corrections land in the live tree. A renderer pinned to it would keep
showing a date the project has since fixed.

Use the snapshot when you need reproducible bytes — citing the dataset in an
article, or reproducing a chart. For rendering current availability, read `/`
and check both version numbers in the manifest, refusing versions you do not
support.

## Why they are separate

**Licensing and attribution.** This repository is MIT code and CC BY 4.0
data; CC BY 4.0 is GPL-compatible, while a plugin distributed through
wordpress.org is normally GPLv2-or-later. Fetching rather than bundling keeps
ownership and attribution clear: the plugin remains GPL code and the dataset is
consumed under CC BY with visible credit. It also lowers the bar for
contributions — someone improving a renderer never touches the dataset, and
someone correcting a date never touches PHP.

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
