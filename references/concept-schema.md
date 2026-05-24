# Concept Record Schema

Create one JSON record per concept. The helper script accepts this shape and writes `concept.json`, `concept.qd`, `concept.md`, `sources.json`, updates `index.json`, renders `html/<slug>.html`, and creates `slidev/<slug>/slides.md`.

## Required Fields

```json
{
  "title": "Agent Skill",
  "slug": "agent-skill",
  "aliases": ["Skill", "Codex Skill", "Agent Skill"],
  "category": "AI workflow",
  "depth": "standard",
  "direct_answer": "一句话说，Agent Skill 像给 AI 准备的一本小手册：Prompt 是这次怎么做，Skill 是以后遇到同类任务都按这套做。",
  "summary": "A reusable instruction package that teaches an AI agent how to perform a specific kind of task.",
  "plain_explanation": "Explain the concept in simple Chinese.",
  "why_it_matters": "Explain why this concept exists and why a user should care.",
  "how_it_works": ["Step or mechanism 1", "Step or mechanism 2"],
  "not_this": ["Misconception or boundary line"],
  "comparisons": [
    {
      "name": "Prompt",
      "summary": "A one-off instruction in a chat.",
      "difference": "A prompt tells the model what to do now; a skill preserves a reusable workflow for future tasks."
    }
  ],
  "related": [
    {
      "name": "Prompt Engineering",
      "relation": "sibling",
      "why": "Both shape model behavior, but at different levels of reuse."
    }
  ],
  "timeline": [
    {
      "label": "Origin",
      "detail": "Where the concept came from or why it appeared."
    }
  ],
  "example": {
    "title": "Everyday example",
    "body": "A concrete scenario that makes the concept easy to picture."
  },
  "memory_hook": "A compact metaphor or phrase.",
  "takeaways": ["Remember this 1", "Remember this 2", "Remember this 3"],
  "quiz": [
    {
      "question": "Which description best matches an Agent Skill?",
      "options": ["A one-off chat sentence", "A reusable workflow package", "A web browser"],
      "answer": 1,
      "explanation": "A skill packages reusable instructions and resources."
    }
  ],
  "sources": [
    {
      "title": "Official docs or source",
      "url": "https://example.com",
      "note": "What this source supports"
    }
  ],
  "refresh_policy": {
    "days": 90,
    "reason": "Refresh sooner for fast-changing tools or product details."
  }
}
```

## Writing Rules

- Write all user-facing fields in concise Chinese unless the concept name is English.
- Use `depth: "quick" | "standard" | "deep"` to record research depth. Most concepts are `standard`.
- `direct_answer` is the first thing shown to the user in chat. It must answer the question directly in 1-3 short sentences and should use an analogy when useful.
- `summary` should be one sentence. It powers the immediate chat answer and hero block.
- `plain_explanation` should be short enough to skim.
- `not_this` should include at least two misconception boundaries when possible.
- `comparisons` should cover the terms the user is likely to confuse with the concept.
- `related` should include parent, sibling, child, prerequisite, or next-step concepts.
- `quiz.answer` is a zero-based option index.
- Use absolute dates in source notes when freshness matters.
- If no external source was used, include a source with `title: "Local reasoning"` and `note` explaining that the entry is model-derived or user-context-derived.
- Treat `concept.qd` as the Quarkdown mother draft for reading and long-term knowledge-base consistency.
- Treat `slidev/<slug>/slides.md` as the presentation draft extracted from the mother draft and concept record.

## Slug Rules

- Prefer lowercase English slugs with hyphens: `agent-skill`, `vibe-coding`, `context-engineering`.
- For Chinese-only terms, use pinyin or a short translated slug.
- Keep slugs stable. If a title changes, keep the old slug and add the old title to aliases.
