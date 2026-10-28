# Catalogue gap report, 28 October 2026

> **Status (28 October 2026): actioned.** The alias, variant, registration and findings work proposed here landed in #157, #158, #159 and #160. The leads that no public source could settle are open items in the validation backlog. This file is a dated record of what the catalogue showed against the dataset that day, not a to-do list.

A one-off, read-only comparison of the Microsoft Foundry models listing the catalogue watcher has collected with the tracker's dataset. Nothing here is a data change: every row is a lead for triage under `.github/copilot-instructions.md`, and the catalogue is an observation, never a dated event.

## Method

- **Catalogue:** `scripts/build_catalogue.py` run locally on `main` at `590c51f`, replaying 35 regions from the seed checkpoints (`2026-10-27T19:30:00Z`) through `2026-10-28T01:30:00Z`. A model key is ARM `name@version`; a name is *listed* if any region has an open cell for it. Qatar Central lists no models yet and is not counted.
- **Tracker:** `data/models.yaml` (ids, display names, aliases), `data/events.yaml` (events on the Foundry surfaces `azure-openai`, `azure-ai-catalog`, `azure-ai-studio`, `azure-ai-foundry` and `microsoft-foundry`, the ones with `counts_as: foundry`) and the validation backlog.
- **Linked** means the ARM name or key is in a model's `aliases`, which is the only link the viewer and catalogue make (ruling 35). **Near** means the ARM name equals a model's id, display name or alias once case and punctuation are ignored (`gpt-5.1` against `gpt-5-1`). A near match is an alias-only fix. **Unmatched** names were classified by hand.
- **Stage** compares the tracker's latest availability event on a Foundry surface (by start date) with the portal word the catalogue shows today. A difference is a lead, not a verdict: the triage guide says record both in a backlog item and never pick one.
- **Absence is weak.** Gated, Deprecating and Fireworks- or Hugging Face-routed models can be invisible to this one pay-as-you-go subscription.

## Headline

| | Names | Keys |
|---|---:|---:|
| Catalogue, total | 151 | 181 |
| Linked through an alias | 17 | 17 |
| Near match: alias-only fix | 62 | 71 |
| Unmatched, frontier-scope candidate | 22 | 22 |
| Unmatched, extended-scope candidate | 23 | 35 |
| Unmatched, not a model | 2 | 8 |
| Unmatched, long tail | 25 | 28 |

Tracker side: 73 models have events on a Foundry surface; 19 of them match no catalogue name. A further 21 registered models are listed in the catalogue with no event on a Foundry surface (10 of those are MAI models recorded on the `microsoft-ai` vendor surface by design). Stage leads: 29.

## 1. Catalogue models with no tracker link

### 1a. Alias-only fixes (62 names, 71 keys)

The model is registered; the exact ARM spelling is missing from `aliases`. Adding it links every version of the name. `590c51f` did this for `gpt-5.4` on the morning of this report.

| ARM name | Tracker model | Versions listed | Regions | Stage now |
|---|---|---|---:|---|
| `claude-fable-5` | `claude-fable-5` | 1 | 2 | Preview |
| `claude-fable-5-1` | `claude-fable-5-1` | 1 | 9 | Preview |
| `claude-haiku-4-5` | `claude-haiku-4-5` | 2, 20251001 | 9 | Generally Available |
| `claude-haiku-5-5` | `claude-haiku-5-5` | 1, 2 | 9 | Generally Available |
| `claude-opus-4-1` | `claude-opus-4-1` | 20250805 | 3 | Retired (API `Deprecated`) |
| `claude-opus-4-5` | `claude-opus-4-5` | 20251101 | 9 | Generally Available |
| `claude-opus-4-6` | `claude-opus-4-6` | 1 | 9 | Generally Available |
| `claude-opus-4-8` | `claude-opus-4-8` | 1, 2 | 9 | Generally Available |
| `claude-opus-5` | `claude-opus-5` | 1, 2 | 9 | Generally Available |
| `claude-opus-5-5` | `claude-opus-5-5` | 1, 2 | 9 | Generally Available |
| `claude-sonnet-4-5` | `claude-sonnet-4-5` | 20250929 | 9 | Deprecated (API `Deprecating`) |
| `claude-sonnet-4-6` | `claude-sonnet-4-6` | 1 | 9 | Generally Available |
| `claude-sonnet-5` | `claude-sonnet-5` | 1, 2 | 9 | Generally Available |
| `claude-sonnet-5-5` | `claude-sonnet-5-5` | 1, 2 | 9 | Generally Available |
| `DeepSeek-R1` | `deepseek-r1` | 1 | 32 | Retired (API `Deprecated`) |
| `DeepSeek-V3.2` | `deepseek-v3-2` | 1 | 32 | Generally Available |
| `DeepSeek-V3.2-Speciale` | `deepseek-v3-2-speciale` | 1 | 32 | Generally Available |
| `DeepSeek-V4-Flash` | `deepseek-v4-flash` | 2026-04-23 | 32 | Generally Available |
| `DeepSeek-V4-Flash-0731` | `deepseek-v4-flash-0731` | 2026-07-31 | 32 | Preview |
| `DeepSeek-V4-Pro` | `deepseek-v4-pro` | 2026-04-23 | 32 | Generally Available |
| `gpt-4.1` | `gpt-4-1` | 2025-04-14 | 31 | Legacy |
| `gpt-4.1-mini` | `gpt-4-1-mini` | 2025-04-14 | 31 | Legacy |
| `gpt-4.1-nano` | `gpt-4-1-nano` | 2025-04-14 | 31 | Legacy |
| `gpt-4o` | `gpt-4o` | 2024-05-13, 2024-08-06, 2024-11-20 | 31 | Deprecated (API `Deprecating`); Legacy |
| `gpt-5` | `gpt-5` | 2025-08-07 | 29 | Generally Available |
| `gpt-5-mini` | `gpt-5-mini` | 2025-08-07 | 29 | Generally Available |
| `gpt-5.1` | `gpt-5-1` | 2025-11-13 | 29 | Generally Available |
| `gpt-5.2` | `gpt-5-2` | 2025-12-11 | 29 | Generally Available |
| `gpt-5.5` | `gpt-5-5` | 2026-04-24 | 29 | Generally Available |
| `gpt-5.6-luna` | `gpt-5-6-luna` | 2026-07-09 | 28 | Generally Available |
| `gpt-5.6-sol` | `gpt-5-6-sol` | 2026-07-09 | 28 | Generally Available |
| `gpt-5.6-terra` | `gpt-5-6-terra` | 2026-07-09 | 28 | Generally Available |
| `gpt-6-astra` | `gpt-6-astra` | 2026-09-03 | 29 | Generally Available |
| `gpt-6-luna` | `gpt-6-luna` | 2026-09-22 | 28 | Generally Available |
| `gpt-6-sol` | `gpt-6-sol` | 2026-09-22 | 28 | Generally Available |
| `gpt-image-1` | `gpt-image-1` | 2025-04-15 | 5 | Retired (API `Preview`) |
| `gpt-image-1.5` | `gpt-image-1-5` | 2025-12-16 | 5 | Generally Available |
| `gpt-image-2` | `gpt-image-2` | 2026-04-21 | 6 | Generally Available |
| `gpt-live-transcribe` | `gpt-live-transcribe` | 2026-07-28 | 7 | Generally Available |
| `gpt-realtime` | `gpt-realtime` | 2025-08-28 | 7 | Generally Available |
| `gpt-transcribe` | `gpt-transcribe` | 2026-07-28 | 7 | Generally Available |
| `grok-4.6` | `grok-4-6` | 1 | 32 | Preview |
| `grok-4.7` | `grok-4-7` | 1 | 32 | Generally Available |
| `Kimi-K2.7-Code` | `kimi-k2-7-code` | 2026-06-12 | 32 | Preview |
| `MAI-Code-1.1-Flash` | `mai-code-1-1-flash` | 2026-09-15 | 24 | Preview |
| `MAI-Image-2` | `mai-image-2` | 2026-02-20 | 7 | Retired (API `Deprecated`) |
| `MAI-Image-2.5` | `mai-image-2-5` | 2026-06-02 | 7 | Preview |
| `MAI-Image-2.5-Flash` | `mai-image-2-5-flash` | 2026-06-02 | 7 | Preview |
| `MAI-Image-2.6` | `mai-image-2-6` | 2026-07-31 | 7 | Generally Available |
| `MAI-Image-2.6-Flash` | `mai-image-2-6-flash` | 2026-07-31 | 7 | Generally Available |
| `MAI-Image-2e` | `mai-image-2e` | 2026-04-09 | 7 | Retired (API `Deprecated`) |
| `MAI-Thinking-1` | `mai-thinking-1` | 2026-06-01 | 31 | Preview |
| `MAI-Transcribe-2-Streaming` | `mai-transcribe-2-streaming` | 2026-08-06 | 4 | Preview |
| `Microsoft-Decision-1` | `microsoft-decision-1` | 1 | 32 | Preview |
| `Mistral-Large-3` | `mistral-large-3` | 1 | 32 | Generally Available |
| `mistral-medium-3-5` | `mistral-medium-3-5` | 1 | 32 | Preview |
| `o1` | `o1` | 2024-12-17 | 31 | Deprecated (API `Deprecating`) |
| `o3` | `o3` | 2025-04-16 | 29 | Deprecated (API `Deprecating`) |
| `o3-mini` | `o3-mini` | 2025-01-31 | 29 | Deprecated (API `Deprecating`) |
| `o4-mini` | `o4-mini` | 2025-04-16 | 31 | Deprecated (API `Deprecating`) |
| `sora-2` | `sora-2` | 2025-12-08 | 2 | Retired (API `Deprecated`) |
| `whisper` | `whisper` | 001 | 31 | Generally Available |

### 1b. Frontier-scope candidates, not registered (22 names)

| ARM name | Publisher | Regions | Stage now | Note |
|---|---|---:|---|---|
| `DeepSeek-V4-Pro-0813` | DeepSeek | 1 | Preview | Dated V4 Pro build; the registry already carries the parallel `deepseek-v4-flash-0731`. |
| `Llama-4-Maverick-17B-128E-Instruct-FP8` | Meta | 32 | Generally Available | Llama 4; the registry has only `llama-2` for Llama. |
| `Llama-4-Scout-17B-16E-Instruct` | Meta | 32 | Generally Available | Llama 4. |
| `Muse-Glimmer-30B` | Meta | 10 | Generally Available | Meta Muse Glimmer; backlog item `meta-muse-glimmer-release-evidence` is open. |
| `MAI-Image-2.5-Pro` | Microsoft | 7 | Preview | MAI image line; 2.5 and 2.5 Flash are registered, Pro is not. |
| `mistral-medium-2505` | Mistral AI | 32 | Generally Available | Mistral Medium 3; the registry has Medium 3.5 but not 3. |
| `codex-mini` | OpenAI | 3 | Deprecated (API `Deprecating`) | Codex line (catalogue: Deprecated). |
| `gpt-4o-mini` | OpenAI | 31 | Deprecated (API `Deprecating`) | GPT-4o mini; no registry entry (catalogue: Deprecated). |
| `gpt-5-codex` | OpenAI | 28 | Generally Available | Codex model line; the registry's `codex` is the 2021 model, not this line. |
| `gpt-5-nano` | OpenAI | 26 | Generally Available | GPT-5 family member; no registry entry. |
| `gpt-5-pro` | OpenAI | 28 | Generally Available | GPT-5 Pro; no registry entry. |
| `gpt-5.1-codex` | OpenAI | 29 | Generally Available | Codex line. |
| `gpt-5.1-codex-max` | OpenAI | 28 | Generally Available | Codex line. |
| `gpt-5.1-codex-mini` | OpenAI | 28 | Generally Available | Codex line. |
| `gpt-5.2-codex` | OpenAI | 29 | Generally Available | Codex line. |
| `gpt-5.3-codex` | OpenAI | 29 | Generally Available | Codex line. |
| `gpt-5.4-mini` | OpenAI | 29 | Generally Available | GPT-5.4 family member; GPT-5.4 itself is registered. |
| `gpt-5.4-nano` | OpenAI | 29 | Generally Available | GPT-5.4 family member. |
| `gpt-5.4-pro` | OpenAI | 29 | Generally Available | GPT-5.4 Pro. |
| `o3-deep-research` | OpenAI | 2 | Deprecated (API `Deprecating`) | Possibly the API model behind `openai-deep-research`; a judgement call, not a spelling miss. |
| `gpt-oss-120b` | OpenAI-OSS | 32 | Generally Available | OpenAI open-weight model (publisher OpenAI-OSS). |
| `gpt-oss-20b` | OpenAI-OSS | 32 | Generally Available | OpenAI open-weight model. |

### 1c. Extended-scope candidates (23 names, 35 keys)

Modality variants, older versions and small models from vendors the tracker covers. Candidates for `scope: extended` entries if breadth is wanted.

| ARM name | Publisher | Kind | Keys | Stage now |
|---|---|---|---:|---|
| `cohere-command-a` | Cohere | Cohere chat | 1 | Generally Available |
| `Cohere-command-a-plus-05-2026` | Cohere | Cohere chat (catalogue: Retired) | 1 | Retired (API `Preview`) |
| `Llama-3.3-70B-Instruct` | Meta | older Llama | 6 | Generally Available |
| `Phi-4` | Microsoft | Microsoft SLM | 6 | Generally Available |
| `Phi-4-mini-instruct` | Microsoft | Microsoft SLM | 1 | Generally Available |
| `Phi-4-mini-reasoning` | Microsoft | Microsoft SLM | 1 | Generally Available |
| `Phi-4-multimodal-instruct` | Microsoft | Microsoft SLM | 1 | Generally Available |
| `Phi-4-reasoning` | Microsoft | Microsoft SLM | 1 | Generally Available |
| `Codestral-2501` | Mistral AI | Mistral code model | 1 | Generally Available |
| `Ministral-3B` | Mistral AI | Mistral SLM | 1 | Generally Available |
| `Mistral-large` | Mistral AI | older Mistral Large | 1 | Generally Available |
| `mistral-small-2503` | Mistral AI | Mistral Small 3.1 | 1 | Generally Available |
| `gpt-audio` | OpenAI | audio | 1 | Generally Available |
| `gpt-audio-1.5` | OpenAI | audio | 1 | Generally Available |
| `gpt-audio-mini` | OpenAI | audio | 2 | Generally Available |
| `gpt-image-1-mini` | OpenAI | image | 1 | Generally Available |
| `gpt-image-2.5-flare` | OpenAI | image | 1 | Generally Available |
| `gpt-image-2.5-sunburst` | OpenAI | image | 1 | Generally Available |
| `gpt-realtime-1.5` | OpenAI | realtime | 1 | Generally Available |
| `gpt-realtime-2` | OpenAI | realtime | 1 | Preview |
| `gpt-realtime-2.1` | OpenAI | realtime | 1 | Generally Available |
| `gpt-realtime-2.1-mini` | OpenAI | realtime | 1 | Generally Available |
| `gpt-realtime-mini` | OpenAI | realtime | 2 | Generally Available |

### 1d. Not a model

| ARM name | Keys | Note |
|---|---:|---|
| `gpt-chat-latest` | 5 | Routing alias, not a distinct model (backlog `foundry-gpt-chat-latest-gpt5-6-sol-2026-08`). Five versioned builds are listed: 2026-05-05, 05-28, 06-24, 08-06 and 10-07. |
| `model-router` | 3 | Microsoft's router over other models, published under the OpenAI format; not a model release. |

### 1e. Long tail (25 names, 28 keys)

Embeddings, rerankers, speech, OCR and document models, and vendors outside the tracker's scope. Listed for completeness; no action proposed.

| Publisher | Names |
|---|---|
| Alibaba | `qwen3-32b`, `qwen3.6-35b-a3b`, `qwen3.8-27b` |
| Black Forest Labs | `FLUX-1.1-pro`, `FLUX.1-Kontext-pro`, `FLUX.2-flex`, `FLUX.2-pro` |
| Cohere | `Cohere-embed-v3-english`, `Cohere-embed-v3-multilingual`, `Cohere-rerank-v4.0-fast`, `Cohere-rerank-v4.0-pro`, `embed-v-4-0` |
| Mistral AI | `mistral-document-ai-2512`, `mistral-ocr-4-0` |
| OpenAI | `gpt-4o-mini-transcribe`, `gpt-4o-mini-tts`, `gpt-4o-transcribe`, `gpt-4o-transcribe-diarize`, `gpt-realtime-translate`, `gpt-realtime-whisper`, `text-embedding-3-large`, `text-embedding-3-small`, `text-embedding-ada-002`, `tts`, `tts-hd` |

## 2. Tracker models with Foundry events but no catalogue listing

19 models. The reason column is a hypothesis; absence is weak evidence.

| Tracker model | Latest Foundry event | Likely reason | Lead |
|---|---|---|---|
| `claude-opus-4-7` | ga on `microsoft-foundry`, 2026-04-16 | Unexplained: GA on Foundry 2026-04-16, no key in any region. Retired early, or gated to existing customers? | investigate |
| `gpt-5-5-instant` | ga on `microsoft-foundry`, 2026-05-07 | Unexplained under its own name. GPT-5.5 Chat may be what `gpt-chat-latest@2026-05-05` serves (listed in 29 regions) | investigate |
| `grok-4` | ga on `azure-ai-foundry`, 2025-09-29 | Unexplained: GA on Foundry 2025-09-29, no key. Possibly retired with Grok 3 or superseded by 4.x | investigate |
| `codex` | ga on `azure-openai`, 2023-01-17 | Retired 2023 model; no ending recorded | ending backlog item |
| `dall-e-2` | ga on `azure-openai`, 2023-01-17 | Retired; no ending recorded | ending backlog item |
| `gpt-3` | limited_preview on `azure-openai`, 2021-11-02 | Retired generation; no ending recorded | ending backlog item |
| `gpt-3-5` | ga on `azure-openai`, 2023-01-17 | Retired generation; no ending recorded | ending backlog item |
| `gpt-3-5-turbo` | public_preview on `azure-openai`, 2023-03-09 | Retired; no ending recorded (ARM spelling would be gpt-35-turbo) | ending backlog item |
| `gpt-4` | public_preview on `azure-openai`, 2023-03-21 | Retired generation; no ending recorded | ending backlog item |
| `gpt-4-turbo` | ga on `azure-openai`, 2024-05-01 | Retired; no ending recorded | ending backlog item |
| `llama-2` | ga on `azure-ai-catalog`, 2023-07-18 | Gone from the catalogue; no ending recorded | ending backlog item |
| `o1-mini` | limited_preview on `azure-openai`, 2024-09-12 | Retired; no ending recorded | ending backlog item |
| `o1-preview` | limited_preview on `azure-openai`, 2024-09-12 | Retired; no ending recorded | ending backlog item |
| `kimi-k3` | ga on `microsoft-foundry`, 2026-07-28 | Fireworks route (alias `FW Kimi K3`); this API does not list Fireworks-hosted models | none: route not in this API |
| `muse-spark-open` | public_preview on `microsoft-foundry`, 2026-10-15 | Hugging Face collection route (`meta-models--…`); not listed by this API | none: route not in this API |
| `nemotron-3-5-lightning` | ga on `microsoft-foundry`, 2026-08-19 | Hugging Face / partner route; not listed by this API | none: route not in this API |
| `deepseek-v3-0324` | retired on `microsoft-foundry`, 2026-07-13 | Retired, as recorded | none |
| `grok-3` | retired on `microsoft-foundry`, 2026-05-01 | Retired, as recorded | none |
| `grok-3-mini` | retired on `microsoft-foundry`, 2026-05-01 | Retired, as recorded | none |

### 2b. Registered, listed, but no event on a Foundry surface (21 models)

The catalogue lists these; the tracker has the model but records no Foundry arrival. A listing never dates an arrival, so each lead is a `microsoft-foundry` backlog item until a Microsoft post or Learn revision dates it. MAI models are recorded on the `microsoft-ai` vendor surface by the registry's own rule, so they are listed separately.

| Tracker model | Catalogue keys | Regions | Stage now |
|---|---|---:|---|
| `claude-opus-4-8` | `claude-opus-4-8@1`, `claude-opus-4-8@2` | 9 | Generally Available |
| `gpt-5-1` | `gpt-5.1@2025-11-13` | 29 | Generally Available |
| `gpt-5-2` | `gpt-5.2@2025-12-11` | 29 | Generally Available |
| `gpt-5-mini` | `gpt-5-mini@2025-08-07` | 29 | Generally Available |
| `gpt-live-1` | `gpt-live-1@2026-09-10` | 7 | Generally Available |
| `grok-4-1-fast` | `grok-4-1-fast-non-reasoning@1`, `grok-4-1-fast-reasoning@1` | 32 | Generally Available |
| `kimi-k2-7-code` | `Kimi-K2.7-Code@2026-06-12` | 32 | Preview |
| `mistral-medium-3-5` | `mistral-medium-3-5@1` | 32 | Preview |
| `o1` | `o1@2024-12-17` | 31 | Deprecated (API `Deprecating`) |
| `sora-2` | `sora-2@2025-12-08` | 2 | Retired (API `Deprecated`) |
| `whisper` | `whisper@001` | 31 | Generally Available |

MAI models on `microsoft-ai` by design: `mai-code-1-1-flash`, `mai-image-2`, `mai-image-2-5`, `mai-image-2-5-flash`, `mai-image-2-6`, `mai-image-2-6-flash`, `mai-image-2e`, `mai-thinking-1`, `mai-transcribe-2-streaming`, `microsoft-decision-1`.

## 3. Stage leads

### Catalogue says Preview, tracker says GA: a contradiction to record, not resolve (5)

| Tracker model | Tracker's latest Foundry stage | Catalogue now |
|---|---|---|
| `cohere-embed-v5` | ga (2026-09-30) | Preview |
| `cohere-rerank-v5` | ga (2026-10-21) | Preview |
| `grok-4-20` | ga (2026-03-30) | Preview |
| `grok-4-3` | ga (2026-05) | Preview |
| `mai-transcribe-2-streaming` | ga (microsoft-ai, 2026-10-01) | Preview |

### Catalogue says GA, tracker's latest is a preview: a GA step the tracker has not recorded (9)

| Tracker model | Tracker's latest Foundry stage | Catalogue now |
|---|---|---|
| `claude-haiku-4-5` | public_preview (2025-11-18) | Generally Available |
| `claude-opus-4-6` | public_preview (2026-02-05) | Generally Available |
| `claude-sonnet-4-6` | public_preview (2026-02-17) | Generally Available |
| `deepseek-v3-2` | public_preview (2025-12-15) | Generally Available |
| `deepseek-v3-2-speciale` | public_preview (2025-12-15) | Generally Available |
| `gpt-image-1-5` | limited_preview (2025-12) | Generally Available |
| `gpt-image-2` | public_preview (2026-04-21) | Generally Available |
| `mai-image-2-6` | public_preview (microsoft-ai) | Generally Available |
| `mai-image-2-6-flash` | public_preview (microsoft-ai) | Generally Available |

### Catalogue says Legacy, Deprecated or Retired, tracker records no ending (13)

| Tracker model | Tracker's latest Foundry stage | Catalogue now |
|---|---|---|
| `claude-opus-4-1` | public_preview (2025-11-18) | Retired (API `Deprecated`) |
| `claude-sonnet-4-5` | public_preview (2025-11-18) | Deprecated (API `Deprecating`) |
| `deepseek-r1` | public_preview (2025-01-29) | Retired (API `Deprecated`) |
| `gpt-4-1` | ga (2025-04-14) | Legacy |
| `gpt-4-1-mini` | ga (2025-04-14) | Legacy |
| `gpt-4-1-nano` | ga (2025-04-14) | Legacy |
| `gpt-4o` | public_preview (2024-05-13) | Deprecated (API `Deprecating`); Legacy |
| `gpt-image-1` | limited_preview (2025-04) | Retired (API `Preview`) |
| `mai-image-2` | public_preview (microsoft-ai) | Retired (API `Deprecated`) |
| `mai-image-2e` | public_preview (microsoft-ai) | Retired (API `Deprecated`) |
| `o3` | ga (2025-04-16) | Deprecated (API `Deprecating`) |
| `o3-mini` | ga (2025-01-31) | Deprecated (API `Deprecating`) |
| `o4-mini` | ga (2025-04-16) | Deprecated (API `Deprecating`) |

### Tracker says suspended, catalogue still lists it (1)

| Tracker model | Tracker's latest Foundry stage | Catalogue now |
|---|---|---|
| `claude-fable-5` | suspended (2026-06-12) | Preview |

### Tracker has Foundry events but no availability event (1)

| Tracker model | Tracker's latest Foundry stage | Catalogue now |
|---|---|---|
| `claude-opus-4-5` | none (no availability event) | Generally Available |

Notes:

- The three owed corrections are confirmed: `cohere-embed-v5` and `cohere-rerank-v5` are GA in the tracker and Preview in every listing region (32), and `mai-transcribe-2-streaming` is GA on `microsoft-ai` and Preview in the 4 regions that list it.
- A portal word of Retired can come from a passed `deprecation_inference` date while the API still says Preview or GA (`gpt-image-1` is API `Preview`, portal Retired). Quote both, per the lifecycle mapping.
- `claude-fable-5` is recorded as suspended and is still listed (Preview) in 2 regions. The open backlog item `foundry-fable5-restoration-2026` is the place for this.

## 4. Region and deployment-type facts

The dataset records no per-region availability, so there is little to contradict. Its evidence notes do name deployment types; each was checked against the catalogue's open cells.

| Event | Tracker says | Catalogue | Verdict |
|---|---|---|---|
| `foundry-gpt6-sol-luna-2026-09-22` | Standard in all 28 Global regions, US and EU Data Zones, Provisioned for Sol | `gpt-6-sol` in 28 regions with Global, DataZone and Provisioned cells | Agrees, region count exact |
| `foundry-gpt6-1-sol-2026-09-29` | Global, US/EU/APAC Data Zones, Provisioned through Global and Data Zone | 28 regions; GlobalStandard, DataZoneStandard, GlobalProvisionedManaged, DataZoneProvisionedManaged | Agrees |
| `foundry-grok4-20-ga-2026-03-30` | Serverless or provisioned throughput deployments | GlobalStandard and DataZoneStandard only, 32 regions | Contradiction: no provisioned cell (and stage, see 3) |
| `foundry-deepseek-v4-flash-0731-2026-08-19`, `foundry-deepseek-v4-1-flash-2026-09-23` | Fireworks route with Data Zone and Provisioned types | Direct listing, GlobalStandard only | Not a contradiction: the Fireworks route is not in this API |
| `foundry-opus5-5-2026-09-22`, `foundry-sonnet5-5-2026-09-28`, `foundry-grok4-7-2026-10-06`, `foundry-gpt6-1-terra-2026-10-26`, `foundry-grok4-6-preview-2026-08-26`, `foundry-gpt-live-transcribe-2026-07-29` | Global Standard, plus Data Zone where stated | Matching cells | Agrees |

## 5. Identity audit

Every Foundry name once, against the registry, in the fields the viewer's mapping notes asked for. **Exact** means the same API identity (dated builds of one name count as one identity, as the registry already treats `gpt-4o`). **Variant** means a distinct API identity related to a registered model: smaller, larger, specialised, a later version or a dated build. Variants are never aliased to their parent. **Ambiguous** needs a source before any mapping. **Unrelated** has no registry counterpart. A name match is never enough on its own: every Exact row also checks that the publisher matches the registry's vendor.

| Classification | Verified | Needs review |
|---|---:|---:|
| Exact | 69 | 2 |
| Variant | 25 | 8 |
| Ambiguous | 0 | 4 |
| Unrelated | 43 | 0 |

Of the 69 verified exact identities, 9 are already aliases and 60 are not: those 60 are the alias PR. No registry name or alias is used by two models, and none of the proposed aliases collides with another model's name.

The 8 *Variant (joined to parent)* rows are existing aliases that map two API identities onto one registry model: Grok 4.1 Fast and Grok 4.20 in reasoning and non-reasoning modes, and Cohere Embed v5 and Rerank v5 in Fast and Pro sizes. They are correct as the registry is written today. Whether to split them is a registry decision, best taken with the `variant_of` recommendation below.

| Foundry name | Publisher | Research model ID | Research display name | Current mapping | Proposed mapping | Classification | Confidence | Evidence |
|---|---|---|---|---|---|---|---|---|
| `claude-fable-5` (1 key) | Anthropic | `claude-fable-5` | Claude Fable 5 | null | `claude-fable-5` | Exact | Needs review | Name equals registry id `claude-fable-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. Recorded as suspended; listed in 2 regions. Alias is right, but settle the stage first. |
| `whisper` (1 key) | OpenAI | `whisper` | Whisper | null | `whisper` | Exact | Needs review | Name equals registry id `whisper` after case and punctuation folding; publisher OpenAI matches vendor OpenAI. The registry entry does not distinguish Whisper builds; Foundry `whisper@001` is one build. |
| `claude-fable-5-1` (1 key) | Anthropic | `claude-fable-5-1` | Claude Fable 5.1 | null | `claude-fable-5-1` | Exact | Verified | Name equals registry id `claude-fable-5-1` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-haiku-4-5` (2 keys) | Anthropic | `claude-haiku-4-5` | Claude Haiku 4.5 | null | `claude-haiku-4-5` | Exact | Verified | Name equals registry id `claude-haiku-4-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-haiku-5-5` (2 keys) | Anthropic | `claude-haiku-5-5` | Claude Haiku 5.5 | null | `claude-haiku-5-5` | Exact | Verified | Name equals registry id `claude-haiku-5-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-opus-4-1` (1 key) | Anthropic | `claude-opus-4-1` | Claude Opus 4.1 | null | `claude-opus-4-1` | Exact | Verified | Name equals registry id `claude-opus-4-1` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-opus-4-5` (1 key) | Anthropic | `claude-opus-4-5` | Claude Opus 4.5 | null | `claude-opus-4-5` | Exact | Verified | Name equals registry id `claude-opus-4-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-opus-4-6` (1 key) | Anthropic | `claude-opus-4-6` | Claude Opus 4.6 | null | `claude-opus-4-6` | Exact | Verified | Name equals registry id `claude-opus-4-6` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-opus-4-8` (2 keys) | Anthropic | `claude-opus-4-8` | Claude Opus 4.8 | null | `claude-opus-4-8` | Exact | Verified | Name equals registry id `claude-opus-4-8` after case and punctuation folding; publisher Anthropic matches vendor Anthropic. |
| `claude-opus-5` (2 keys) | Anthropic | `claude-opus-5` | Claude Opus 5 | null | `claude-opus-5` | Exact | Verified | Name equals registry id `claude-opus-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-opus-5-5` (2 keys) | Anthropic | `claude-opus-5-5` | Claude Opus 5.5 | null | `claude-opus-5-5` | Exact | Verified | Name equals registry id `claude-opus-5-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-sonnet-4-5` (1 key) | Anthropic | `claude-sonnet-4-5` | Claude Sonnet 4.5 | null | `claude-sonnet-4-5` | Exact | Verified | Name equals registry id `claude-sonnet-4-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-sonnet-4-6` (1 key) | Anthropic | `claude-sonnet-4-6` | Claude Sonnet 4.6 | null | `claude-sonnet-4-6` | Exact | Verified | Name equals registry id `claude-sonnet-4-6` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-sonnet-5` (2 keys) | Anthropic | `claude-sonnet-5` | Claude Sonnet 5 | null | `claude-sonnet-5` | Exact | Verified | Name equals registry id `claude-sonnet-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `claude-sonnet-5-5` (2 keys) | Anthropic | `claude-sonnet-5-5` | Claude Sonnet 5.5 | null | `claude-sonnet-5-5` | Exact | Verified | Name equals registry id `claude-sonnet-5-5` after case and punctuation folding; publisher Anthropic matches vendor Anthropic; the registry already records this model on a Foundry surface. |
| `Cohere-parse-v5` (1 key) | Cohere | `cohere-parse-v5` | Cohere Parse v5 | `cohere-parse-v5` | `cohere-parse-v5` | Exact | Verified | Already an alias. |
| `DeepSeek-R1` (1 key) | DeepSeek | `deepseek-r1` | DeepSeek-R1 | null | `deepseek-r1` | Exact | Verified | Name equals registry id `deepseek-r1` after case and punctuation folding; publisher DeepSeek matches vendor DeepSeek; the registry already records this model on a Foundry surface. |
| `DeepSeek-V3.2` (1 key) | DeepSeek | `deepseek-v3-2` | DeepSeek V3.2 | null | `deepseek-v3-2` | Exact | Verified | Name equals registry id `deepseek-v3-2` after case and punctuation folding; publisher DeepSeek matches vendor DeepSeek; the registry already records this model on a Foundry surface. |
| `DeepSeek-V3.2-Speciale` (1 key) | DeepSeek | `deepseek-v3-2-speciale` | DeepSeek V3.2-Speciale | null | `deepseek-v3-2-speciale` | Exact | Verified | Name equals registry id `deepseek-v3-2-speciale` after case and punctuation folding; publisher DeepSeek matches vendor DeepSeek; the registry already records this model on a Foundry surface. |
| `DeepSeek-V4-Flash` (1 key) | DeepSeek | `deepseek-v4-flash` | DeepSeek V4 Flash | null | `deepseek-v4-flash` | Exact | Verified | Name equals registry id `deepseek-v4-flash` after case and punctuation folding; publisher DeepSeek matches vendor DeepSeek; the registry already records this model on a Foundry surface. |
| `DeepSeek-V4-Flash-0731` (1 key) | DeepSeek | `deepseek-v4-flash-0731` | DeepSeek-V4-Flash-0731 | null | `deepseek-v4-flash-0731` | Exact | Verified | Name equals registry id `deepseek-v4-flash-0731` after case and punctuation folding; publisher DeepSeek matches vendor DeepSeek; the registry already records this model on a Foundry surface. |
| `DeepSeek-V4-Pro` (1 key) | DeepSeek | `deepseek-v4-pro` | DeepSeek V4 Pro | null | `deepseek-v4-pro` | Exact | Verified | Name equals registry id `deepseek-v4-pro` after case and punctuation folding; publisher DeepSeek matches vendor DeepSeek; the registry already records this model on a Foundry surface. |
| `DeepSeek-V4.1-Flash` (1 key) | DeepSeek | `deepseek-v4-1-flash` | DeepSeek V4.1 Flash | `deepseek-v4-1-flash` | `deepseek-v4-1-flash` | Exact | Verified | Already an alias. |
| `gpt-4.1` (1 key) | OpenAI | `gpt-4-1` | GPT-4.1 | null | `gpt-4-1` | Exact | Verified | Name equals registry id `gpt-4-1` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-4.1-mini` (1 key) | OpenAI | `gpt-4-1-mini` | GPT-4.1 mini | null | `gpt-4-1-mini` | Exact | Verified | Name equals registry id `gpt-4-1-mini` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-4.1-nano` (1 key) | OpenAI | `gpt-4-1-nano` | GPT-4.1 nano | null | `gpt-4-1-nano` | Exact | Verified | Name equals registry id `gpt-4-1-nano` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-4o` (3 keys) | OpenAI | `gpt-4o` | GPT-4o | null | `gpt-4o` | Exact | Verified | Name equals registry id `gpt-4o` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-5` (1 key) | OpenAI | `gpt-5` | GPT-5 | null | `gpt-5` | Exact | Verified | Name equals registry id `gpt-5` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-5-mini` (1 key) | OpenAI | `gpt-5-mini` | GPT-5 mini | null | `gpt-5-mini` | Exact | Verified | Name equals registry id `gpt-5-mini` after case and punctuation folding; publisher OpenAI matches vendor OpenAI. |
| `gpt-5.1` (1 key) | OpenAI | `gpt-5-1` | GPT-5.1 | null | `gpt-5-1` | Exact | Verified | Name equals registry id `gpt-5-1` after case and punctuation folding; publisher OpenAI matches vendor OpenAI. |
| `gpt-5.2` (1 key) | OpenAI | `gpt-5-2` | GPT-5.2 | null | `gpt-5-2` | Exact | Verified | Name equals registry id `gpt-5-2` after case and punctuation folding; publisher OpenAI matches vendor OpenAI. |
| `gpt-5.4` (1 key) | OpenAI | `gpt-5-4` | GPT-5.4 | `gpt-5-4` | `gpt-5-4` | Exact | Verified | Already an alias. |
| `gpt-5.5` (1 key) | OpenAI | `gpt-5-5` | GPT-5.5 | null | `gpt-5-5` | Exact | Verified | Name equals registry id `gpt-5-5` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-5.6-luna` (1 key) | OpenAI | `gpt-5-6-luna` | GPT-5.6 Luna | null | `gpt-5-6-luna` | Exact | Verified | Name equals registry id `gpt-5-6-luna` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-5.6-sol` (1 key) | OpenAI | `gpt-5-6-sol` | GPT-5.6 Sol | null | `gpt-5-6-sol` | Exact | Verified | Name equals registry id `gpt-5-6-sol` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-5.6-terra` (1 key) | OpenAI | `gpt-5-6-terra` | GPT-5.6 Terra | null | `gpt-5-6-terra` | Exact | Verified | Name equals registry id `gpt-5-6-terra` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-6-astra` (1 key) | OpenAI | `gpt-6-astra` | GPT-6 Astra | null | `gpt-6-astra` | Exact | Verified | Name equals registry id `gpt-6-astra` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-6-luna` (1 key) | OpenAI | `gpt-6-luna` | GPT-6 Luna | null | `gpt-6-luna` | Exact | Verified | Name equals registry id `gpt-6-luna` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-6-sol` (1 key) | OpenAI | `gpt-6-sol` | GPT-6 Sol | null | `gpt-6-sol` | Exact | Verified | Name equals registry id `gpt-6-sol` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-6.1-sol` (1 key) | OpenAI | `gpt-6-1-sol` | GPT-6.1 Sol | `gpt-6-1-sol` | `gpt-6-1-sol` | Exact | Verified | Already an alias. |
| `gpt-6.1-terra` (1 key) | OpenAI | `gpt-6-1-terra` | GPT-6.1 Terra | `gpt-6-1-terra` | `gpt-6-1-terra` | Exact | Verified | Already an alias. |
| `gpt-image-1` (1 key) | OpenAI | `gpt-image-1` | GPT-image-1 | null | `gpt-image-1` | Exact | Verified | Name equals registry id `gpt-image-1` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-image-1.5` (1 key) | OpenAI | `gpt-image-1-5` | GPT-image-1.5 | null | `gpt-image-1-5` | Exact | Verified | Name equals registry id `gpt-image-1-5` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-image-2` (1 key) | OpenAI | `gpt-image-2` | GPT-image-2 | null | `gpt-image-2` | Exact | Verified | Name equals registry id `gpt-image-2` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-live-1` (1 key) | OpenAI | `gpt-live-1` | GPT-Live-1 | `gpt-live-1` | `gpt-live-1` | Exact | Verified | Already an alias. |
| `gpt-live-transcribe` (1 key) | OpenAI | `gpt-live-transcribe` | GPT-live-transcribe | null | `gpt-live-transcribe` | Exact | Verified | Name equals registry id `gpt-live-transcribe` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-realtime` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | `gpt-realtime` | Exact | Verified | Name equals registry id `gpt-realtime` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `gpt-transcribe` (1 key) | OpenAI | `gpt-transcribe` | GPT-transcribe | null | `gpt-transcribe` | Exact | Verified | Name equals registry id `gpt-transcribe` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `grok-4.3` (1 key) | xAI | `grok-4-3` | Grok 4.3 | `grok-4-3` | `grok-4-3` | Exact | Verified | Already an alias. |
| `grok-4.6` (1 key) | xAI | `grok-4-6` | Grok 4.6 | null | `grok-4-6` | Exact | Verified | Name equals registry id `grok-4-6` after case and punctuation folding; publisher xAI matches vendor xAI; the registry already records this model on a Foundry surface. |
| `grok-4.7` (1 key) | xAI | `grok-4-7` | Grok 4.7 | null | `grok-4-7` | Exact | Verified | Name equals registry id `grok-4-7` after case and punctuation folding; publisher xAI matches vendor xAI; the registry already records this model on a Foundry surface. |
| `Kimi-K2.5` (1 key) | MoonshotAI | `kimi-k2-5` | Kimi K2.5 | `kimi-k2-5` | `kimi-k2-5` | Exact | Verified | Already an alias. |
| `Kimi-K2.6` (1 key) | MoonshotAI | `kimi-k2-6` | Kimi K2.6 | `kimi-k2-6` | `kimi-k2-6` | Exact | Verified | Already an alias. |
| `Kimi-K2.7-Code` (1 key) | MoonshotAI | `kimi-k2-7-code` | Kimi K2.7 Code | null | `kimi-k2-7-code` | Exact | Verified | Name equals registry id `kimi-k2-7-code` after case and punctuation folding; publisher MoonshotAI matches vendor Moonshot AI. |
| `MAI-Code-1.1-Flash` (1 key) | Microsoft | `mai-code-1-1-flash` | MAI-Code-1.1-Flash | null | `mai-code-1-1-flash` | Exact | Verified | Name equals registry id `mai-code-1-1-flash` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Image-2` (1 key) | Microsoft | `mai-image-2` | MAI-Image-2 | null | `mai-image-2` | Exact | Verified | Name equals registry id `mai-image-2` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Image-2.5` (1 key) | Microsoft | `mai-image-2-5` | MAI-Image-2.5 | null | `mai-image-2-5` | Exact | Verified | Name equals registry id `mai-image-2-5` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Image-2.5-Flash` (1 key) | Microsoft | `mai-image-2-5-flash` | MAI-Image-2.5 Flash | null | `mai-image-2-5-flash` | Exact | Verified | Name equals registry id `mai-image-2-5-flash` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Image-2.6` (1 key) | Microsoft | `mai-image-2-6` | MAI-Image-2.6 | null | `mai-image-2-6` | Exact | Verified | Name equals registry id `mai-image-2-6` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Image-2.6-Flash` (1 key) | Microsoft | `mai-image-2-6-flash` | MAI-Image-2.6-Flash | null | `mai-image-2-6-flash` | Exact | Verified | Name equals registry id `mai-image-2-6-flash` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Image-2e` (1 key) | Microsoft | `mai-image-2e` | MAI-Image-2e | null | `mai-image-2e` | Exact | Verified | Name equals registry id `mai-image-2e` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Thinking-1` (1 key) | Microsoft | `mai-thinking-1` | MAI-Thinking-1 | null | `mai-thinking-1` | Exact | Verified | Name equals registry id `mai-thinking-1` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `MAI-Transcribe-2-Streaming` (1 key) | Microsoft | `mai-transcribe-2-streaming` | MAI-Transcribe-2-Streaming | null | `mai-transcribe-2-streaming` | Exact | Verified | Name equals registry id `mai-transcribe-2-streaming` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `Microsoft-Decision-1` (1 key) | Microsoft | `microsoft-decision-1` | Microsoft-Decision-1 | null | `microsoft-decision-1` | Exact | Verified | Name equals registry id `microsoft-decision-1` after case and punctuation folding; publisher Microsoft matches vendor Microsoft. |
| `Mistral-Large-3` (1 key) | Mistral AI | `mistral-large-3` | Mistral Large 3 | null | `mistral-large-3` | Exact | Verified | Name equals registry id `mistral-large-3` after case and punctuation folding; publisher Mistral AI matches vendor Mistral AI; the registry already records this model on a Foundry surface. |
| `mistral-medium-3-5` (1 key) | Mistral AI | `mistral-medium-3-5` | Mistral Medium 3.5 | null | `mistral-medium-3-5` | Exact | Verified | Name equals registry id `mistral-medium-3-5` after case and punctuation folding; publisher Mistral AI matches vendor Mistral AI. |
| `o1` (1 key) | OpenAI | `o1` | o1 | null | `o1` | Exact | Verified | Name equals registry id `o1` after case and punctuation folding; publisher OpenAI matches vendor OpenAI. |
| `o3` (1 key) | OpenAI | `o3` | o3 | null | `o3` | Exact | Verified | Name equals registry id `o3` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `o3-mini` (1 key) | OpenAI | `o3-mini` | o3-mini | null | `o3-mini` | Exact | Verified | Name equals registry id `o3-mini` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `o4-mini` (1 key) | OpenAI | `o4-mini` | o4-mini | null | `o4-mini` | Exact | Verified | Name equals registry id `o4-mini` after case and punctuation folding; publisher OpenAI matches vendor OpenAI; the registry already records this model on a Foundry surface. |
| `sora-2` (1 key) | OpenAI | `sora-2` | Sora 2 | null | `sora-2` | Exact | Verified | Name equals registry id `sora-2` after case and punctuation folding; publisher OpenAI matches vendor OpenAI. |
| `Cohere-Embed-V5-Fast` (1 key) | Cohere | `cohere-embed-v5` | Cohere Embed 5 | `cohere-embed-v5` | `cohere-embed-v5` | Variant (joined to parent) | Needs review | Registry aliases `Cohere-Embed-V5-Fast` to `cohere-embed-v5`: size (fast). Joins two API identities; keep or split is a registry decision. |
| `Cohere-Embed-V5-Pro` (1 key) | Cohere | `cohere-embed-v5` | Cohere Embed 5 | `cohere-embed-v5` | `cohere-embed-v5` | Variant (joined to parent) | Needs review | Registry aliases `Cohere-Embed-V5-Pro` to `cohere-embed-v5`: size (pro). Joins two API identities; keep or split is a registry decision. |
| `Cohere-rerank-v5-fast` (1 key) | Cohere | `cohere-rerank-v5` | Cohere Rerank 5 | `cohere-rerank-v5` | `cohere-rerank-v5` | Variant (joined to parent) | Needs review | Registry aliases `Cohere-rerank-v5-fast` to `cohere-rerank-v5`: size (fast). Joins two API identities; keep or split is a registry decision. |
| `Cohere-rerank-v5-pro` (1 key) | Cohere | `cohere-rerank-v5` | Cohere Rerank 5 | `cohere-rerank-v5` | `cohere-rerank-v5` | Variant (joined to parent) | Needs review | Registry aliases `Cohere-rerank-v5-pro` to `cohere-rerank-v5`: size (pro). Joins two API identities; keep or split is a registry decision. |
| `grok-4-1-fast-non-reasoning` (1 key) | xAI | `grok-4-1-fast` | Grok 4.1 Fast | `grok-4-1-fast` | `grok-4-1-fast` | Variant (joined to parent) | Needs review | Registry aliases `grok-4-1-fast-non-reasoning` to `grok-4-1-fast`: non-reasoning mode. Joins two API identities; keep or split is a registry decision. |
| `grok-4-1-fast-reasoning` (1 key) | xAI | `grok-4-1-fast` | Grok 4.1 Fast | `grok-4-1-fast` | `grok-4-1-fast` | Variant (joined to parent) | Needs review | Registry aliases `grok-4-1-fast-reasoning` to `grok-4-1-fast`: reasoning mode. Joins two API identities; keep or split is a registry decision. |
| `grok-4-20-non-reasoning` (1 key) | xAI | `grok-4-20` | Grok 4.20 | `grok-4-20` | `grok-4-20` | Variant (joined to parent) | Needs review | Registry aliases `grok-4-20-non-reasoning` to `grok-4-20`: non-reasoning mode. Joins two API identities; keep or split is a registry decision. |
| `grok-4-20-reasoning` (1 key) | xAI | `grok-4-20` | Grok 4.20 | `grok-4-20` | `grok-4-20` | Variant (joined to parent) | Needs review | Registry aliases `grok-4-20-reasoning` to `grok-4-20`: reasoning mode. Joins two API identities; keep or split is a registry decision. |
| `DeepSeek-V4-Pro-0813` (1 key) | DeepSeek | `deepseek-v4-pro` | DeepSeek V4 Pro | null | null | Variant (dated build (registry precedent: deepseek-v4-flash-0731 is its own model)) | Verified | A distinct API identity in the `deepseek-v4-pro` family; register it as its own model, never alias it to the parent. |
| `gpt-4o-mini` (1 key) | OpenAI | `gpt-4o` | GPT-4o | null | null | Variant (smaller (mini)) | Verified | A distinct API identity in the `gpt-4o` family; register it as its own model, never alias it to the parent. |
| `gpt-4o-mini-transcribe` (2 keys) | OpenAI | `gpt-4o` | GPT-4o | null | null | Variant (specialised (speech to text, mini)) | Verified | A distinct API identity in the `gpt-4o` family; register it as its own model, never alias it to the parent. |
| `gpt-4o-mini-tts` (2 keys) | OpenAI | `gpt-4o` | GPT-4o | null | null | Variant (specialised (text to speech, mini)) | Verified | A distinct API identity in the `gpt-4o` family; register it as its own model, never alias it to the parent. |
| `gpt-4o-transcribe` (1 key) | OpenAI | `gpt-4o` | GPT-4o | null | null | Variant (specialised (speech to text)) | Verified | A distinct API identity in the `gpt-4o` family; register it as its own model, never alias it to the parent. |
| `gpt-4o-transcribe-diarize` (1 key) | OpenAI | `gpt-4o` | GPT-4o | null | null | Variant (specialised (diarisation)) | Verified | A distinct API identity in the `gpt-4o` family; register it as its own model, never alias it to the parent. |
| `gpt-5-codex` (1 key) | OpenAI | `gpt-5` | GPT-5 | null | null | Variant (specialised (codex)) | Verified | A distinct API identity in the `gpt-5` family; register it as its own model, never alias it to the parent. |
| `gpt-5-nano` (1 key) | OpenAI | `gpt-5` | GPT-5 | null | null | Variant (smaller (nano)) | Verified | A distinct API identity in the `gpt-5` family; register it as its own model, never alias it to the parent. |
| `gpt-5-pro` (1 key) | OpenAI | `gpt-5` | GPT-5 | null | null | Variant (larger (pro)) | Verified | A distinct API identity in the `gpt-5` family; register it as its own model, never alias it to the parent. |
| `gpt-5.1-codex` (1 key) | OpenAI | `gpt-5-1` | GPT-5.1 | null | null | Variant (specialised (codex)) | Verified | A distinct API identity in the `gpt-5-1` family; register it as its own model, never alias it to the parent. |
| `gpt-5.1-codex-max` (1 key) | OpenAI | `gpt-5-1` | GPT-5.1 | null | null | Variant (specialised (codex, max)) | Verified | A distinct API identity in the `gpt-5-1` family; register it as its own model, never alias it to the parent. |
| `gpt-5.1-codex-mini` (1 key) | OpenAI | `gpt-5-1` | GPT-5.1 | null | null | Variant (specialised (codex, mini)) | Verified | A distinct API identity in the `gpt-5-1` family; register it as its own model, never alias it to the parent. |
| `gpt-5.2-codex` (1 key) | OpenAI | `gpt-5-2` | GPT-5.2 | null | null | Variant (specialised (codex)) | Verified | A distinct API identity in the `gpt-5-2` family; register it as its own model, never alias it to the parent. |
| `gpt-5.4-mini` (1 key) | OpenAI | `gpt-5-4` | GPT-5.4 | null | null | Variant (smaller (mini)) | Verified | A distinct API identity in the `gpt-5-4` family; register it as its own model, never alias it to the parent. |
| `gpt-5.4-nano` (1 key) | OpenAI | `gpt-5-4` | GPT-5.4 | null | null | Variant (smaller (nano)) | Verified | A distinct API identity in the `gpt-5-4` family; register it as its own model, never alias it to the parent. |
| `gpt-5.4-pro` (1 key) | OpenAI | `gpt-5-4` | GPT-5.4 | null | null | Variant (larger (pro)) | Verified | A distinct API identity in the `gpt-5-4` family; register it as its own model, never alias it to the parent. |
| `gpt-image-1-mini` (1 key) | OpenAI | `gpt-image-1` | GPT-image-1 | null | null | Variant (smaller (mini)) | Verified | A distinct API identity in the `gpt-image-1` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-1.5` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (later version) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-2` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (later version) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-2.1` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (later version) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-2.1-mini` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (later version, mini) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-mini` (2 keys) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (smaller (mini)) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-translate` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (specialised (translation)) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `gpt-realtime-whisper` (1 key) | OpenAI | `gpt-realtime` | gpt-realtime | null | null | Variant (specialised (transcription)) | Verified | A distinct API identity in the `gpt-realtime` family; register it as its own model, never alias it to the parent. |
| `MAI-Image-2.5-Pro` (1 key) | Microsoft | `mai-image-2-5` | MAI-Image-2.5 | null | null | Variant (larger (pro)) | Verified | A distinct API identity in the `mai-image-2-5` family; register it as its own model, never alias it to the parent. |
| `codex-mini` (1 key) | OpenAI | `codex` | Codex | null | null | Ambiguous | Needs review | The registry's `codex` is the 2021 model; codex-mini belongs to the 2025 Codex line. |
| `gpt-chat-latest` (5 keys) | OpenAI | null |  | null | null | Ambiguous | Needs review | Routing alias whose target changes between builds (backlog `foundry-gpt-chat-latest-gpt5-6-sol-2026-08`). |
| `Mistral-large` (1 key) | Mistral AI | `mistral-large-3` | Mistral Large 3 | null | null | Ambiguous | Needs review | Unversioned name; Mistral Large 3 is listed separately as `Mistral-Large-3`, so this is an older Large. |
| `o3-deep-research` (1 key) | OpenAI | `openai-deep-research` | OpenAI deep research model | null | null | Ambiguous | Needs review | The registry's deep-research entry may be the product, not this API model. |
| `Codestral-2501` (1 key) | Mistral AI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `cohere-command-a` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Cohere-command-a-plus-05-2026` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Cohere-embed-v3-english` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Cohere-embed-v3-multilingual` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Cohere-rerank-v4.0-fast` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Cohere-rerank-v4.0-pro` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `embed-v-4-0` (1 key) | Cohere | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `FLUX-1.1-pro` (1 key) | Black Forest Labs | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `FLUX.1-Kontext-pro` (1 key) | Black Forest Labs | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `FLUX.2-flex` (1 key) | Black Forest Labs | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `FLUX.2-pro` (1 key) | Black Forest Labs | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-5.3-codex` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-audio` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-audio-1.5` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-audio-mini` (2 keys) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-image-2.5-flare` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-image-2.5-sunburst` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-oss-120b` (1 key) | OpenAI-OSS | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `gpt-oss-20b` (1 key) | OpenAI-OSS | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Llama-3.3-70B-Instruct` (6 keys) | Meta | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Llama-4-Maverick-17B-128E-Instruct-FP8` (1 key) | Meta | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Llama-4-Scout-17B-16E-Instruct` (1 key) | Meta | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Ministral-3B` (1 key) | Mistral AI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `mistral-document-ai-2512` (1 key) | Mistral AI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `mistral-medium-2505` (1 key) | Mistral AI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `mistral-ocr-4-0` (1 key) | Mistral AI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `mistral-small-2503` (1 key) | Mistral AI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `model-router` (3 keys) | OpenAI | null |  | null | null | Unrelated (not a model) | Verified | Microsoft's router over other models. |
| `Muse-Glimmer-30B` (1 key) | Meta | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Phi-4` (6 keys) | Microsoft | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Phi-4-mini-instruct` (1 key) | Microsoft | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Phi-4-mini-reasoning` (1 key) | Microsoft | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Phi-4-multimodal-instruct` (1 key) | Microsoft | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `Phi-4-reasoning` (1 key) | Microsoft | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `qwen3-32b` (1 key) | Alibaba | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `qwen3.6-35b-a3b` (1 key) | Alibaba | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `qwen3.8-27b` (1 key) | Alibaba | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `text-embedding-3-large` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `text-embedding-3-small` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `text-embedding-ada-002` (2 keys) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `tts` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |
| `tts-hd` (1 key) | OpenAI | null |  | null | null | Unrelated (no registry model) | Verified | No registry id, name or alias matches; not a variant of a registered model. |

### Recommendation: an explicit variant relationship

Name-prefix matching in the viewer is a fair discovery aid but cannot tell a variant from a namesake. The registry should say it. The smallest change that fits the existing schema:

```yaml
  - id: gpt-5-4-mini
    display_name: "GPT-5.4 mini"
    vendor: OpenAI
    generation: gpt-5
    scope: extended
    aliases: ["gpt-5.4-mini"]
    variant_of: gpt-5-4
    variant_kind: mini        # mini | nano | pro | max | reasoning | non-reasoning | chat | codex | speech | dated-build
```

- `variant_of` points at a registered model, validated like `supersedes`. It never implies supersession or shared availability, so each variant keeps its own events, stage and regions.
- `variant_kind` is a closed list, so the viewer can group ("GPT-5.4 and 3 variants") without parsing names.
- The joined Grok and Cohere pairs could then be split into two registered models each, with `variant_of` pointing at the base. That is a call for the registry's owner, not a correction.
- `build_catalogue.py` would carry `variant_of` into `intervals.json` `models`, so the viewer can drop its prefix heuristic. It would remain an explicit mapping, with no fuzzy matching in the builder.

## Proposed next PRs

1. **Alias additions** (60 verified exact Foundry names onto existing models; section 5). Pure registry edit plus regenerated `generated/`; no events. `whisper` and `claude-fable-5` are held for review.
2. **Stage contradictions as backlog items** (5): the Cohere pair, MAI-Transcribe-2-Streaming, Grok 4.20 and Grok 4.3, each recording the tracker's stage beside the catalogue's (API value and portal word), citing the commit-pinned checkpoint. Add Grok 4.20's missing provisioned cell to its item.
3. **Endings the catalogue shows** (13 models in 3, plus 10 long-gone ones in 2): backlog items, promoted to bounded `retired`/`deprecated` events only where Microsoft's retirement schedule or a Learn revision dates them.
4. **GA steps not yet recorded** (9): backlog items to find the Microsoft post dating each Preview-to-GA move (ruling 12 lets an observed window resolve a blocked item, but the seed has no window).
5. **Foundry arrivals for registered models** (11 in 2b): `microsoft-foundry` backlog items, each needing a dated Microsoft source.
6. **New-model candidates** (22 frontier names in 1b): registry entries and backlog items in one batch, the GPT-5/5.4 family members, the Codex line, gpt-oss and Llama 4 first. Each arrival still needs its own dated source.
7. **Investigate** `claude-opus-4-7`, `grok-4` and `gpt-5-5-instant`, which have dated Foundry GA events but no listing.
8. **Variant relationship:** add `variant_of` and `variant_kind` to the model schema (section 5), then register the 25 verified variants as extended models.
9. **Update** backlog item `foundry-gpt-chat-latest-gpt5-6-sol-2026-08` with the five versioned `gpt-chat-latest` builds the catalogue lists.

