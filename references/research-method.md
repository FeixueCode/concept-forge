# Lightweight Concept Research Method

This adapts hv-analysis for everyday concepts. Keep it practical: usually a concept entry should fit in one knowledge card and one interactive page.

## Step 1: Clarify The Concept

Extract:

- core term;
- aliases and spelling variants;
- whether the user asks for definition, comparison, pronunciation, installation, usage, or memory;
- adjacent terms already mentioned by the user.

If the concept boundary is ambiguous but low risk, choose the most likely meaning and state it in the record. Ask only when several meanings would produce very different entries.

## Step 2: Decide Research Depth

Use one of three depths:

- **Quick**: stable, common, low-risk concept. Use existing knowledge plus optional source check.
- **Standard**: tool, method, technical term, or comparison. Use web/official docs if current details matter.
- **Deep**: concept is new, disputed, fast-moving, or the user asks for a more complete page. Use multiple sources and compare them.

Most entries should use Standard depth.

Depth changes the amount of research and verification, not the artifact family:

- Quick still produces the direct answer, JSON, Quarkdown mother draft, Markdown fallback, HTML, and Slidev source.
- Standard produces the same artifacts and should make the Quarkdown draft complete enough for focused reading.
- Deep produces the same artifacts with stronger sourcing, richer horizontal/vertical analysis, and a Slidev structure that can support public explanation.

Only compile/export Quarkdown or Slidev when the tools are installed and the user needs a formal deliverable. Source generation is always required.

## Step 3: Mini Horizontal-Vertical Analysis

Vertical questions:

- Where did this term/tool/practice come from?
- What problem or shift made it necessary?
- What changed from earlier approaches?

Horizontal questions:

- What is it often confused with?
- What is the nearest sibling concept?
- What is the parent category?
- What does it replace, extend, or complement?

Cross insight:

- What is the simplest mental model that makes the concept stick?
- What should the user stop confusing after reading this?

## Step 4: Expand Related Concepts

Add related items only when they help the user build a map. Avoid dumping a glossary.

Good relation labels:

- `parent`: broader category.
- `sibling`: similar concept.
- `child`: sub-type or implementation.
- `prerequisite`: concept needed first.
- `contrast`: commonly confused opposite.
- `next`: useful follow-up.

## Step 5: Source Discipline

Browse when the answer depends on current facts, product behavior, installation instructions, release status, pricing, or official naming.

Prefer:

1. Official documentation or repository.
2. Standards/specifications.
3. Primary announcements.
4. Reputable explainers.

If exact freshness is not checked, do not claim the record is confirmed-current.
