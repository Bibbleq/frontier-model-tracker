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

## Corrections round, 27 July 2026

`metadata.import_provenance` is a fixed historical record of the 26 July 2026 import, not a live count. It stays at 144 canonical events and 36 validation items; current totals are derived from the data itself.

The first corrections round added four canonical events and retired four backlog items. Every URL was refetched and read before the record was written.

Promoted from the backlog:

- **Copilot in Microsoft 365 apps with Anthropic models, 3 April 2026.** Microsoft Learn states the date explicitly: "On April 3, 2026, Microsoft introduced a new Microsoft 365 admin center setting Copilot in M365 apps with Anthropic models in EU/EFTA and UK." That closed the outstanding request for page-history or Message Center evidence.
- **Claude Sonnet 5 GA in Microsoft Foundry, 30 June 2026.** The Microsoft announcement carries a 30 June publication date and opens by referring back to the 29 June Claude GA post, which pins the date the working claim lacked.
- **Claude Opus 5 in Microsoft Foundry, 24 July 2026.** Microsoft's same-day announcement, corroborated by the Learn catalogue listing `claude-opus-5` as Hosted on Azure.
- **Claude Fable 5 suspension in Microsoft Foundry, 12 June 2026**, at `supported` confidence. Anthropic's directive statement is global and does not name Foundry; CNBC's later report that access had to be re-enabled "on Amazon Web Services, Google Cloud and Microsoft Foundry" establishes retrospectively that Foundry distribution was affected.

Deliberately **not** promoted:

- **Fable 5 restoration in Microsoft Foundry.** The proposed 1 July 2026 date matched the vendor and GitHub restorations, but the best available source says partner-cloud re-enablement would follow "as soon as possible". Under the project's own rule that an announcement of future availability is not first availability, this stays a validation target with the evidence attached.
- **Splitting the two GPT-5.6 vendor records.** They were reported as reading like duplicates. They do not: the 26 June record is `limited_preview` for GPT-5.6 Sol and the 9 July record is `release` for the Sol / Terra / Luna family, and the earlier record already carries a caveat separating them. Left unchanged.

One unsourced detail was dropped rather than recorded: a Message Center reference giving a 4 May 2026 effective date for default-on behaviour appeared in no cited source. The 25 March 2026 tenant-creation threshold and the summer 2026 Word rollout, both documented on Microsoft Learn, were kept.
