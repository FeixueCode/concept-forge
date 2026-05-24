---
name: concept-forge
description: Convert everyday questions, concepts, keywords, unfamiliar terms, or "what is X / how does X differ from Y" requests into reusable Chinese knowledge cards, Quarkdown mother drafts, Slidev presentation sources, and interactive HTML explainers. Use when the user wants to understand, remember, compare, review, or build a personal knowledge base for concepts; especially for fragmented internet-era knowledge such as tools, methods, acronyms, technical terms, products, workflows, and conceptual questions. The skill researches like a lightweight hv-analysis pass, stores structured JSON plus Quarkdown/Markdown records, generates a polished interactive HTML page, creates Slidev source when useful, and reuses existing entries on repeated or similar questions.
---

# Concept Forge

Concept Forge turns a user's scattered question into a durable concept asset: a concise answer, a structured knowledge card, a Quarkdown reading draft, a Slidev presentation draft, and a self-contained interactive HTML explainer.

The goal is not to produce a one-off answer. The goal is to make the concept easier to remember and to grow a reusable local knowledge/html library over time.

## Core Loop

Always follow this order:

1. **Normalize the question**: identify the core concept, aliases, comparison targets, and user intent.
2. **Look up existing entries first** with `scripts/concept_forge.py lookup`.
3. **Plan depth** with `scripts/concept_forge.py plan` or the Research Method: choose Quick, Standard, or Deep.
4. **Reuse before rebuilding**: if a strong match exists, return the existing direct answer and HTML path. Refresh only when the user asks, the entry is stale, or the concept is time-sensitive.
5. **Research at the chosen depth** if no usable entry exists: use the Concept Lens below, browsing when the topic may have changed or precise sourcing matters.
6. **Forge the concept record** as structured JSON using `references/concept-schema.md`.
7. **Render and store** with `scripts/concept_forge.py upsert`; this must create JSON, Quarkdown, Markdown, HTML, and Slidev source artifacts.
8. **Validate** the stored entry and generated artifacts with `scripts/concept_forge.py validate`.
9. **Report in Chinese**: always give the answer first, then the local HTML path. Avoid implementation details unless asked.

## User-Facing Response Shape

Every completed request must return two things, in this order:

1. **Direct answer**: 1-3 short Chinese sentences that answer the user's question immediately. Prefer a vivid analogy when it helps memory. This should stand alone for users who do not have time to open the HTML.
2. **Interactive HTML**: a local path or link to the generated/reused HTML explainer.

Use a compact shape like:

```text
一句话说，Skill 像给 AI 准备的一本小手册：Prompt 是这次怎么做，Skill 是以后遇到同类任务都按这套做。

互动页：<path/to/html>
```

Do not make the user open the HTML to get the basic answer.

## Workspace

Default workspace:

```text
<current working directory>/concept-forge-workspace
```

If the user names another storage location, use that. Initialize before first use:

```bash
python <skill>/scripts/concept_forge.py init --workspace <workspace>
```

The workspace contains:

```text
knowledge/index.json
knowledge/concepts/<slug>/concept.json
knowledge/concepts/<slug>/concept.qd
knowledge/concepts/<slug>/concept.md
knowledge/concepts/<slug>/sources.json
html/<slug>.html
slidev/<slug>/slides.md
slidev/<slug>/package.json
quarkdown/
assets/
config.json
```

## Concept Lens

Borrow the spirit of hv-analysis, but keep it light and concept-sized.

For every new or refreshed concept, answer these layers:

- **One-line memory**: the shortest useful definition.
- **Direct answer**: a chat-ready explanation, usually one short paragraph, optionally with a metaphor.
- **What it is**: plain-language explanation.
- **Why it exists**: what problem, confusion, workflow, or historical shift created the need for it.
- **How it works**: the minimum mechanism needed to understand it.
- **What it is not**: common misconceptions and boundary lines.
- **Horizontal comparison**: nearby concepts, tools, prompts, workflows, or terms it is often confused with.
- **Related map**: parent concepts, sibling concepts, child concepts, prerequisites, and next questions.
- **Example**: one concrete everyday scenario.
- **Memory hook**: metaphor, phrase, or visual anchor that makes it stick.
- **Mini quiz**: 2-3 lightweight questions to reinforce memory.

Use web research when facts may be current, niche, controversial, product-specific, or source-sensitive. Prefer official docs and primary sources. If not browsing, mark sources as "model-derived / user-provided / local context" honestly in the record.

## Output Modes

### Existing Entry

If lookup finds a strong existing entry:

- Say it already exists.
- Give the short answer from `direct_answer` if present, otherwise use `summary` plus `memory_hook`.
- Link the local HTML page.
- Offer what can be refreshed only if useful; do not rebuild by default.

### New Entry

For a new concept:

1. Create a JSON record following `references/concept-schema.md`.
2. Include at least: title, aliases, depth, direct answer, summary, what, why, not, comparisons, related, memory hook, quiz, sources.
3. Run:

```bash
python <skill>/scripts/concept_forge.py upsert --workspace <workspace> --input <concept.json>
python <skill>/scripts/concept_forge.py validate --workspace <workspace> --slug <slug>
```

4. Return the direct answer first, then the generated HTML path. Mention Quarkdown or Slidev paths only when the user asks for files, reading drafts, talks, exports, or debugging.

### Refresh

Refresh only when:

- user asks to update / redo / expand;
- entry age exceeds `refresh_policy.days`;
- topic is current or fast-moving;
- sources are weak or missing;
- user asks a more specific follow-up that changes the concept boundary.

When refreshing, preserve existing aliases and related links unless clearly wrong.

## HTML Requirements

Use `references/html-explainer.md` for the exact product shape.

The generated page must be self-contained and must include:

- hero definition;
- "what / why / not" sections;
- comparison cards;
- related concept map;
- timeline or origin strip when useful;
- interactive reveal cards;
- mini quiz;
- "three things to remember";
- source/update footer.

The page should be understandable without the chat transcript.

## First-Class Quarkdown and Slidev

Quarkdown and Slidev are part of the product shape.

- Always generate `concept.qd` as the Quarkdown mother draft. It is the canonical reading document for the knowledge base.
- Always generate `slidev/<slug>/slides.md` as the presentation draft. It is extracted from the concept record and the mother draft.
- Always generate `html/<slug>.html` as the fast interactive memory surface.
- Use dynamic depth to decide how much research, sourcing, and polish to add:
  - **Quick**: stable small concept; generate all source artifacts, normally skip compilation/export.
  - **Standard**: default for tools, methods, comparisons, and "what is X"; generate all artifacts and verify structure.
  - **Deep**: user asks for research or the topic is current/complex; strengthen sources, history, horizontal comparison, and talk structure.
- Compile Quarkdown or build/export Slidev only when the user needs a formal deliverable or local preview. Source generation must not depend on the CLIs being installed.
- Use `scripts/concept_forge.py doctor` on first use or before formal export to check Python, Quarkdown, Node, pnpm, and Slidev availability.
- For Slidev formal use, initialize inside `slidev/<slug>` with `npm install` or `pnpm install`, then run `npm run dev/build/export` or the matching pnpm command as needed.
- For Quarkdown formal use, compile `concept.qd` with `quarkdown c <concept.qd> --strict --out <verify-dir>` when `quarkdown` is available.

## Quality Gate

Before reporting completion, check:

- lookup was attempted before creating;
- final response contains both a direct answer and an HTML path;
- concept has a clear one-line memory;
- nearby concepts and misconceptions are covered;
- HTML exists and is non-empty;
- Quarkdown mother draft exists;
- Slidev source exists;
- `validate` passes;
- index contains title, aliases, slug, direct answer, summary, Quarkdown path, Slidev path, and HTML path;
- final answer is short, Chinese, and user-facing.

## References

- `references/concept-schema.md`: JSON and Markdown record shape.
- `references/research-method.md`: lightweight hv-analysis adaptation.
- `references/html-explainer.md`: interactive HTML product spec.
