# Interactive HTML Explainer Spec

The HTML page is the memory surface. It should feel like a compact learning object, not a pasted article.

## Required Sections

1. **Hero**: concept title, category, one-line summary, memory hook.
2. **Direct answer**: the same short explanation the user receives in chat, so the page is still useful when shared alone.
3. **Three pillars**: what it is, why it matters, how it works.
4. **Not this**: misconception cards that can be expanded/revealed.
5. **Comparison**: cards comparing nearby concepts.
6. **Map**: related concepts grouped by relation.
7. **Timeline/origin**: short origin strip if data exists.
8. **Example**: one concrete scenario.
9. **Quiz**: 2-3 interactive questions.
10. **Takeaways**: three sentences to remember.
11. **Sources**: readable source list and update date.

## Interaction Rules

- Include at least one click-to-reveal area.
- Include a quiz with immediate feedback.
- Keep all JavaScript inline and dependency-free.
- HTML must be self-contained so it can be opened directly from disk.

## Visual Rules

- Prefer a calm, readable knowledge-card style.
- Use multiple accent colors, not a one-color theme.
- Avoid decorative blobs, heavy gradients, and stock-like empty hero art.
- Keep text short in cards.
- Make mobile layout single-column.
- Use semantic headings and accessible button labels.

## Content Rules

- The page must be useful without the chat transcript.
- The page should reflect the same structure as the Quarkdown mother draft, but be shorter and more interactive.
- Do not expose raw tool commands, API paths, or implementation logs.
- Use Chinese for explanations unless preserving an English term.
- Include sources when external facts are used.
