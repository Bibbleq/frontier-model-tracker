# Research provenance

The schema-v2 historical import was built from two research inputs with a cut-off of 26 July 2026.

## Sourced history pack

The canonical seed pack contained:

- 128 sourced candidate events
- 23 structured validation targets
- 133 citations across 116 unique URLs
- a YAML source, readable Markdown history, and flattened CSV index

Archive SHA-256:

```text
7787D6528F4E97DE077B29E739BCDB565F65E6FEF55AE64B4168699F4E4BE705
```

Every seed event had at least one source. The import split records that combined independently queryable products or model availability, producing 144 canonical events. True family announcements and strategic multi-model milestones remain grouped and may use `models[]`.

## Editorial master backlog

The editorial backlog supplied the coverage rules, platform lineages, strategic eras, governance timeline, and unresolved research questions.

File SHA-256:

```text
1963F37DC6D18D15021ECD71E59D26A29B184CB856C7AB4D00A01F0C8A234715
```

Its internal ChatGPT citation tokens were not treated as publishable evidence. Claims were promoted only when the sourced history pack contained direct public URLs. Backlog-only claims were retained as validation targets.

## Import principles

- GitHub Models is not GitHub Copilot.
- Foundry catalogue presence is not Copilot Studio availability.
- A specialist Microsoft 365 experience is not general Copilot Chat selection.
- Announcement, rollout, preview, GA, default, retirement, suspension, restoration, and policy change are distinct events.
- Current support documentation does not by itself establish a historical first date.
- Month/year precision is retained rather than converted to an invented day.

The source pages themselves are not redistributed in this repository. Source records include retrieval dates, and the schema permits publication dates, source types, archive URLs, and source notes when those details are available.
