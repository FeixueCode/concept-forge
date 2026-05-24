#!/usr/bin/env python3
"""Concept Forge workspace helper.

Pure-stdlib helper for initializing a concept knowledge base, looking up
existing entries, storing concept records, rendering interactive HTML explainers,
and validating generated artifacts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


VERSION = "1.1.0"


REQUIRED_FIELDS = [
    "title",
    "aliases",
    "direct_answer",
    "summary",
    "plain_explanation",
    "why_it_matters",
    "comparisons",
    "related",
    "memory_hook",
    "takeaways",
    "quiz",
    "sources",
]


DEPTH_RULES = {
    "deep": [
        "深度",
        "系统",
        "完整",
        "全面",
        "研究",
        "调研",
        "报告",
        "行业",
        "趋势",
        "竞品",
        "历史",
        "来龙去脉",
        "deep",
        "research",
    ],
    "standard": [
        "是什么",
        "为什么",
        "怎么",
        "区别",
        "对比",
        "安装",
        "使用",
        "原理",
        "prompt",
        "工具",
    ],
}


RELATION_LABELS = {
    "parent": "上位概念",
    "sibling": "相邻概念",
    "child": "下位概念",
    "prerequisite": "前置概念",
    "contrast": "容易混淆",
    "next": "继续探索",
}


def now_date() -> str:
    return dt.datetime.now().astimezone().date().isoformat()


def default_workspace() -> Path:
    return Path(os.environ.get("CONCEPT_FORGE_WORKSPACE", Path.cwd() / "concept-forge-workspace"))


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).lower()
    return re.sub(r"[\W_]+", "", text, flags=re.UNICODE)


def slugify(title: str) -> str:
    value = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii").lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if value:
        return value[:80]
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:10]
    return f"concept-{digest}"


def e(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def workspace_paths(workspace: Path) -> Dict[str, Path]:
    return {
        "root": workspace,
        "knowledge": workspace / "knowledge",
        "concepts": workspace / "knowledge" / "concepts",
        "quarkdown": workspace / "quarkdown",
        "slidev": workspace / "slidev",
        "html": workspace / "html",
        "assets": workspace / "assets",
        "templates": workspace / "templates",
        "index": workspace / "knowledge" / "index.json",
        "config": workspace / "config.json",
    }


def init_workspace(workspace: Path) -> Dict[str, str]:
    paths = workspace_paths(workspace)
    for key in ["knowledge", "concepts", "quarkdown", "slidev", "html", "assets", "templates"]:
        paths[key].mkdir(parents=True, exist_ok=True)

    if not paths["index"].exists():
        write_json(paths["index"], {"version": VERSION, "entries": []})

    if not paths["config"].exists():
        write_json(
            paths["config"],
            {
                "version": VERSION,
                "created_at": now_date(),
                "default_refresh_days": 90,
                "html_theme": "knowledge-card",
                "notes": "Concept Forge workspace. concept.qd is the reading draft, slidev/<slug>/slides.md is the presentation draft.",
            },
        )

    return {name: str(path) for name, path in paths.items()}


def load_index(workspace: Path) -> Dict[str, Any]:
    init_workspace(workspace)
    index = read_json(workspace_paths(workspace)["index"], {"version": VERSION, "entries": []})
    if "entries" not in index or not isinstance(index["entries"], list):
        index["entries"] = []
    return index


def save_index(workspace: Path, index: Dict[str, Any]) -> None:
    index["version"] = VERSION
    write_json(workspace_paths(workspace)["index"], index)


def concept_dir(workspace: Path, slug: str) -> Path:
    return workspace_paths(workspace)["concepts"] / slug


def html_path(workspace: Path, slug: str) -> Path:
    return workspace_paths(workspace)["html"] / f"{slug}.html"


def quarkdown_path(workspace: Path, slug: str) -> Path:
    return concept_dir(workspace, slug) / "concept.qd"


def slidev_dir(workspace: Path, slug: str) -> Path:
    return workspace_paths(workspace)["slidev"] / slug


def slidev_path(workspace: Path, slug: str) -> Path:
    return slidev_dir(workspace, slug) / "slides.md"


def load_concept(workspace: Path, slug: str) -> Dict[str, Any]:
    return read_json(concept_dir(workspace, slug) / "concept.json", {})


def score_entry(query: str, entry: Dict[str, Any]) -> float:
    q_norm = normalize_text(query)
    if not q_norm:
        return 0.0
    candidates = [entry.get("slug", ""), entry.get("title", ""), *(entry.get("aliases") or [])]
    best = 0.0
    for candidate in candidates:
        c_norm = normalize_text(candidate)
        if not c_norm:
            continue
        if q_norm == c_norm:
            best = max(best, 100.0)
        elif q_norm in c_norm or c_norm in q_norm:
            best = max(best, 82.0)
        else:
            best = max(best, SequenceMatcher(None, q_norm, c_norm).ratio() * 75.0)
    summary_norm = normalize_text(entry.get("summary", ""))
    if summary_norm and (q_norm in summary_norm or summary_norm in q_norm):
        best = max(best, 55.0)
    return round(best, 2)


def lookup(workspace: Path, query: str, limit: int = 5) -> List[Dict[str, Any]]:
    index = load_index(workspace)
    matches: List[Dict[str, Any]] = []
    for entry in index.get("entries", []):
        score = score_entry(query, entry)
        if score >= 35:
            item = dict(entry)
            item["score"] = score
            matches.append(item)
    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:limit]


def classify_depth(query: str) -> str:
    text = normalize_text(query)
    for token in DEPTH_RULES["deep"]:
        if normalize_text(token) in text:
            return "deep"
    for token in DEPTH_RULES["standard"]:
        if normalize_text(token) in text:
            return "standard"
    return "quick"


def output_plan(depth: str) -> Dict[str, Any]:
    compile_policy = {
        "quick": "生成 Quarkdown/Slidev 源文件和 HTML；通常不编译导出。",
        "standard": "生成全部源文件；如工具已安装且用户需要正式交付，可编译 Quarkdown 或预览 Slidev。",
        "deep": "生成全部源文件；优先补足来源、横纵对比和讲稿结构，必要时编译 Quarkdown 并构建 Slidev 静态页。",
    }
    return {
        "depth": depth,
        "research": {
            "quick": "稳定常识或小概念，少量核对即可。",
            "standard": "工具、方法、比较题或容易混淆的概念，需要更完整的结构化解释。",
            "deep": "新、复杂、变化快或用户要求深度调研，需要多来源和横纵分析。",
        }[depth],
        "outputs": [
            "direct_answer",
            "knowledge/concepts/<slug>/concept.json",
            "knowledge/concepts/<slug>/concept.qd",
            "knowledge/concepts/<slug>/concept.md",
            "html/<slug>.html",
            "slidev/<slug>/slides.md",
        ],
        "compile_policy": compile_policy[depth],
    }


def ensure_record(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("concept input must be a JSON object")
    title = str(record.get("title") or "").strip()
    if not title:
        raise ValueError("concept record requires title")
    record = dict(record)
    record["slug"] = str(record.get("slug") or slugify(title)).strip()
    record["aliases"] = list(dict.fromkeys([str(x).strip() for x in record.get("aliases", []) if str(x).strip()]))
    if title not in record["aliases"]:
        record["aliases"].insert(0, title)
    record["updated_at"] = str(record.get("updated_at") or now_date())
    record.setdefault("created_at", record["updated_at"])
    record.setdefault("category", "概念")
    depth = str(record.get("depth") or "standard").strip().lower()
    record["depth"] = depth if depth in {"quick", "standard", "deep"} else "standard"
    if not str(record.get("direct_answer") or "").strip():
        summary = str(record.get("summary") or "").strip()
        hook = str(record.get("memory_hook") or "").strip()
        if summary and hook and hook not in summary:
            record["direct_answer"] = f"{summary} 类比一下：{hook}"
        else:
            record["direct_answer"] = summary or hook
    record.setdefault("how_it_works", [])
    record.setdefault("not_this", [])
    record.setdefault("comparisons", [])
    record.setdefault("related", [])
    record.setdefault("timeline", [])
    record.setdefault("example", {})
    record.setdefault("takeaways", [])
    record.setdefault("quiz", [])
    record.setdefault("sources", [])
    record.setdefault("refresh_policy", {"days": 90, "reason": "默认按 90 天检查一次是否需要刷新。"})
    return record


def list_md(items: Iterable[Any]) -> str:
    rows = [f"- {str(item)}" for item in items if str(item).strip()]
    return "\n".join(rows) if rows else "- 暂无"


def render_markdown(record: Dict[str, Any]) -> str:
    title = record.get("title", "")
    aliases = "、".join(record.get("aliases", []))
    comparisons = record.get("comparisons", [])
    related = record.get("related", [])
    quiz = record.get("quiz", [])
    sources = record.get("sources", [])
    timeline = record.get("timeline", [])
    example = record.get("example") or {}

    lines: List[str] = [
        f"# {title}",
        "",
        f"> 更新时间：{record.get('updated_at', now_date())} | 分类：{record.get('category', '概念')} | 深度：{record.get('depth', 'standard')}",
        "",
        "## 直接回答",
        record.get("direct_answer", record.get("summary", "")),
        "",
        "## 一句话记住",
        record.get("summary", ""),
        "",
        "## 它是什么",
        record.get("plain_explanation", ""),
        "",
        "## 它解决什么问题",
        record.get("why_it_matters", ""),
        "",
        "## 它怎么工作",
        list_md(record.get("how_it_works", [])),
        "",
        "## 它不是什么",
        list_md(record.get("not_this", [])),
        "",
        "## 它和相近概念的区别",
    ]

    if comparisons:
        for item in comparisons:
            lines.extend(
                [
                    f"### {item.get('name', '相近概念')}",
                    item.get("summary", ""),
                    "",
                    f"区别：{item.get('difference', '')}",
                    "",
                ]
            )
    else:
        lines.append("暂无")

    lines.extend(["", "## 一个具体例子", f"### {example.get('title', '例子')}", example.get("body", ""), ""])
    lines.extend(["## 关联概念"])
    if related:
        for item in related:
            relation = RELATION_LABELS.get(str(item.get("relation", "")), item.get("relation", "相关"))
            lines.append(f"- **{item.get('name', '')}**（{relation}）：{item.get('why', '')}")
    else:
        lines.append("- 暂无")

    if timeline:
        lines.extend(["", "## 来源与演变"])
        for item in timeline:
            lines.append(f"- **{item.get('label', '')}**：{item.get('detail', '')}")

    lines.extend(
        [
            "",
            "## 记忆钩子",
            record.get("memory_hook", ""),
            "",
            "## 三句话带走",
            list_md(record.get("takeaways", [])),
            "",
            "## 小测验",
        ]
    )
    if quiz:
        for i, item in enumerate(quiz, 1):
            lines.append(f"{i}. {item.get('question', '')}")
            for j, option in enumerate(item.get("options", []), 1):
                lines.append(f"   {j}. {option}")
            answer = item.get("answer", 0)
            try:
                answer_label = item.get("options", [])[int(answer)]
            except Exception:
                answer_label = str(answer)
            lines.append(f"   答案：{answer_label}")
            lines.append(f"   解释：{item.get('explanation', '')}")
    else:
        lines.append("暂无")

    lines.extend(["", "## 来源与更新时间"])
    if sources:
        for item in sources:
            url = item.get("url", "")
            if url:
                lines.append(f"- [{item.get('title', url)}]({url})：{item.get('note', '')}")
            else:
                lines.append(f"- {item.get('title', '来源')}：{item.get('note', '')}")
    else:
        lines.append("- 暂无")
    lines.extend(["", f"别名：{aliases}"])
    return "\n".join(lines).strip() + "\n"


def render_quarkdown(record: Dict[str, Any]) -> str:
    """Render the canonical reading draft as Markdown-compatible Quarkdown."""
    body = render_markdown(record)
    preface = [
        f"# {record.get('title', '')}",
        "",
        "> Quarkdown 母稿：用于正式阅读、长期归档，以及给 Slidev 提炼讲稿。",
        "",
        "## 阅读入口",
        record.get("direct_answer", record.get("summary", "")),
        "",
        "## 正文",
        "",
    ]
    return "\n".join(preface).strip() + "\n\n" + body.split("\n", 1)[1]


def slide_bullets(items: Iterable[Any], limit: int = 4) -> str:
    rows = [f"- {str(item)}" for item in items if str(item).strip()]
    rows = rows[:limit]
    return "\n".join(rows) if rows else "- 暂无"


def render_slidev(record: Dict[str, Any]) -> str:
    """Render a compact Slidev deck source from the concept record."""
    title = record.get("title", "Concept")
    comparisons = record.get("comparisons", [])[:3]
    related = record.get("related", [])[:5]
    example = record.get("example") or {}
    takeaways = record.get("takeaways", [])[:3]
    title_json = json.dumps(str(title), ensure_ascii=False)

    compare_lines = []
    for item in comparisons:
        compare_lines.append(f"- **{item.get('name', '相近概念')}**：{item.get('difference') or item.get('summary', '')}")

    related_lines = []
    for item in related:
        relation = RELATION_LABELS.get(str(item.get("relation", "")), item.get("relation", "相关"))
        related_lines.append(f"- **{item.get('name', '')}**（{relation}）：{item.get('why', '')}")

    quiz = record.get("quiz", [])
    quiz_item = quiz[0] if quiz else {}
    quiz_options = quiz_item.get("options", []) if isinstance(quiz_item, dict) else []
    quiz_lines = [f"{i + 1}. {option}" for i, option in enumerate(quiz_options)]

    return f"""---
theme: default
title: {title_json}
class: text-left
transition: fade
drawings:
  enabled: true
---

# {title}

{record.get('direct_answer', record.get('summary', ''))}

<!--
开场：先用一句话让听众抓住这个概念，再进入结构。
-->

---
layout: two-cols
---

# 它是什么

{record.get('plain_explanation', '')}

::right::

# 为什么重要

{record.get('why_it_matters', '')}

---

# 它怎么工作

<v-clicks>

{slide_bullets(record.get('how_it_works', []))}

</v-clicks>

---

# 它不是什么

<v-clicks>

{slide_bullets(record.get('not_this', []))}

</v-clicks>

---

# 相近概念怎么分

{chr(10).join(compare_lines) if compare_lines else '- 暂无'}

---

# 放进知识地图里

{chr(10).join(related_lines) if related_lines else '- 暂无'}

---

# 一个具体例子

## {example.get('title', '例子')}

{example.get('body', '')}

---

# 现场小测

{quiz_item.get('question', '这个概念最应该记住什么？') if isinstance(quiz_item, dict) else '这个概念最应该记住什么？'}

<v-clicks>

{chr(10).join(quiz_lines) if quiz_lines else '- 暂无选项'}

</v-clicks>

<!--
答案：{quiz_item.get('explanation', '') if isinstance(quiz_item, dict) else ''}
-->

---
layout: center
---

# 三句话带走

<v-clicks>

{slide_bullets(takeaways, 3)}

</v-clicks>
"""


def write_slidev_project(workspace: Path, slug: str, record: Dict[str, Any]) -> Path:
    sdir = slidev_dir(workspace, slug)
    sdir.mkdir(parents=True, exist_ok=True)
    slides = sdir / "slides.md"
    slides.write_text(render_slidev(record), encoding="utf-8", newline="\n")
    package = {
        "private": True,
        "type": "module",
        "scripts": {
            "dev": "slidev slides.md",
            "build": "slidev build slides.md",
            "export": "slidev export slides.md",
        },
        "dependencies": {
            "@slidev/cli": "latest",
            "@slidev/theme-default": "latest",
            "vue": "latest",
        },
        "devDependencies": {},
    }
    write_json(sdir / "package.json", package)
    return slides


def render_list(items: Iterable[Any]) -> str:
    values = [str(x).strip() for x in items if str(x).strip()]
    if not values:
        return '<p class="muted">暂无</p>'
    return "<ul>" + "".join(f"<li>{e(v)}</li>" for v in values) + "</ul>"


def render_comparisons(items: List[Dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">还没有相近概念。</p>'
    cards = []
    for item in items:
        cards.append(
            f"""
            <article class="compare-card">
              <h3>{e(item.get('name', '相近概念'))}</h3>
              <p>{e(item.get('summary', ''))}</p>
              <button class="ghost" type="button" data-reveal>看区别</button>
              <div class="reveal"><strong>关键区别：</strong>{e(item.get('difference', ''))}</div>
            </article>
            """
        )
    return "\n".join(cards)


def render_related(items: List[Dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">暂无关联概念。</p>'
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for item in items:
        relation = str(item.get("relation") or "next")
        groups.setdefault(relation, []).append(item)
    chunks = []
    for relation, rel_items in groups.items():
        label = RELATION_LABELS.get(relation, relation)
        chips = "".join(
            f'<li><span>{e(x.get("name", ""))}</span><small>{e(x.get("why", ""))}</small></li>'
            for x in rel_items
        )
        chunks.append(f'<section class="map-group"><h3>{e(label)}</h3><ul>{chips}</ul></section>')
    return "\n".join(chunks)


def render_timeline(items: List[Dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">这个概念暂时没有明确时间线。</p>'
    return "\n".join(
        f'<div class="time-item"><b>{e(item.get("label", ""))}</b><p>{e(item.get("detail", ""))}</p></div>'
        for item in items
    )


def render_quiz(items: List[Dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">暂无小测验。</p>'
    blocks = []
    for i, item in enumerate(items):
        options = item.get("options", [])
        buttons = "".join(
            f'<button type="button" data-quiz="{i}" data-choice="{j}">{e(option)}</button>'
            for j, option in enumerate(options)
        )
        answer = int(item.get("answer", 0)) if str(item.get("answer", 0)).isdigit() else 0
        blocks.append(
            f"""
            <article class="quiz-card" data-answer="{answer}" data-explanation="{e(item.get('explanation', ''))}">
              <h3>{e(item.get('question', ''))}</h3>
              <div class="quiz-options">{buttons}</div>
              <p class="feedback" aria-live="polite"></p>
            </article>
            """
        )
    return "\n".join(blocks)


def render_sources(items: List[Dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">暂无外部来源。</p>'
    rows = []
    for item in items:
        title = e(item.get("title", "来源"))
        url = str(item.get("url") or "").strip()
        note = e(item.get("note", ""))
        if url:
            rows.append(f'<li><a href="{e(url)}" target="_blank" rel="noreferrer">{title}</a><span>{note}</span></li>')
        else:
            rows.append(f"<li><b>{title}</b><span>{note}</span></li>")
    return "<ul>" + "\n".join(rows) + "</ul>"


def render_html(record: Dict[str, Any]) -> str:
    title = record.get("title", "")
    example = record.get("example") or {}
    aliases = " · ".join(record.get("aliases", [])[1:6])
    updated = record.get("updated_at", now_date())
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(title)} | Concept Forge</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #667085;
      --paper: #fffdf8;
      --line: #dfdfd5;
      --blue: #2f6f9f;
      --green: #337357;
      --rose: #a33f4f;
      --gold: #b7791f;
      --violet: #6954a5;
      --shadow: 0 18px 45px rgba(23,32,42,.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
      line-height: 1.65;
    }}
    .wrap {{ width: min(1120px, calc(100% - 32px)); margin: 0 auto; }}
    header {{
      min-height: 78vh;
      display: grid;
      align-items: center;
      border-bottom: 1px solid var(--line);
      background:
        linear-gradient(90deg, rgba(47,111,159,.10), transparent 38%),
        linear-gradient(180deg, rgba(183,121,31,.10), transparent 54%);
    }}
    .hero {{ padding: 72px 0 48px; }}
    .eyebrow {{ color: var(--green); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    h1 {{ font-size: clamp(44px, 9vw, 104px); line-height: .95; margin: 12px 0 18px; letter-spacing: 0; }}
    .summary {{ font-size: clamp(19px, 2.4vw, 29px); max-width: 850px; }}
    .direct-answer {{
      max-width: 880px;
      margin: 22px 0 0;
      padding: 16px 18px;
      border-left: 6px solid var(--blue);
      background: rgba(255,255,255,.78);
      box-shadow: var(--shadow);
      border-radius: 8px;
      font-size: 18px;
    }}
    .hook {{ display: inline-flex; margin-top: 24px; padding: 12px 16px; border: 1px solid var(--line); background: rgba(255,255,255,.65); box-shadow: var(--shadow); }}
    main {{ padding: 36px 0 72px; }}
    section {{ margin: 40px 0; }}
    h2 {{ font-size: clamp(25px, 4vw, 42px); margin: 0 0 18px; }}
    h3 {{ margin: 0 0 8px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .card, .compare-card, .quiz-card, .map-group, .example {{
      background: rgba(255,255,255,.76);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 8px 24px rgba(23,32,42,.06);
    }}
    .card:nth-child(1) h3 {{ color: var(--blue); }}
    .card:nth-child(2) h3 {{ color: var(--green); }}
    .card:nth-child(3) h3 {{ color: var(--rose); }}
    .not-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }}
    .not-item {{ border-left: 5px solid var(--rose); background: #fff; padding: 14px; border-radius: 8px; }}
    .compare-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; }}
    .ghost, .quiz-options button {{
      border: 1px solid var(--ink);
      background: transparent;
      color: var(--ink);
      border-radius: 999px;
      padding: 8px 13px;
      cursor: pointer;
      font: inherit;
    }}
    .ghost:hover, .quiz-options button:hover {{ background: var(--ink); color: white; }}
    .reveal {{ display: none; margin-top: 12px; color: var(--muted); }}
    .reveal.open {{ display: block; }}
    .map {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }}
    .map-group ul, .sources ul {{ list-style: none; padding: 0; margin: 0; }}
    .map-group li {{ padding: 10px 0; border-top: 1px solid var(--line); }}
    .map-group span {{ display: block; font-weight: 750; color: var(--violet); }}
    .map-group small {{ color: var(--muted); }}
    .timeline {{ display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }}
    .time-item {{ min-width: 230px; border-top: 4px solid var(--gold); padding: 12px; background: white; border-radius: 8px; }}
    .example {{ border-left: 6px solid var(--green); }}
    .quiz-options {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 12px 0; }}
    .feedback.ok {{ color: var(--green); font-weight: 700; }}
    .feedback.no {{ color: var(--rose); font-weight: 700; }}
    .takeaways {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; counter-reset: take; }}
    .takeaway {{ position: relative; padding: 22px 18px 18px; background: var(--ink); color: white; border-radius: 8px; }}
    .takeaway:before {{ counter-increment: take; content: counter(take); position: absolute; top: -14px; left: 16px; background: var(--gold); color: #111; width: 32px; height: 32px; display: grid; place-items: center; border-radius: 50%; font-weight: 800; }}
    .sources li {{ display: grid; gap: 4px; padding: 10px 0; border-top: 1px solid var(--line); }}
    .sources a {{ color: var(--blue); font-weight: 700; }}
    .muted, footer {{ color: var(--muted); }}
    footer {{ border-top: 1px solid var(--line); padding: 24px 0 40px; }}
    @media (max-width: 760px) {{
      header {{ min-height: auto; }}
      .grid, .takeaways {{ grid-template-columns: 1fr; }}
      .summary {{ font-size: 18px; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="wrap hero">
      <div class="eyebrow">{e(record.get('category', '概念'))}</div>
      <h1>{e(title)}</h1>
      <p class="summary">{e(record.get('summary', ''))}</p>
      <div class="direct-answer"><strong>一句话先懂：</strong>{e(record.get('direct_answer', record.get('summary', '')))}</div>
      <div class="hook"><strong>记忆钩子：</strong>&nbsp;{e(record.get('memory_hook', ''))}</div>
      <p class="muted">{e(aliases)}</p>
    </div>
  </header>
  <main class="wrap">
    <section>
      <h2>先把它抓住</h2>
      <div class="grid">
        <article class="card"><h3>它是什么</h3><p>{e(record.get('plain_explanation', ''))}</p></article>
        <article class="card"><h3>它为什么重要</h3><p>{e(record.get('why_it_matters', ''))}</p></article>
        <article class="card"><h3>它怎么工作</h3>{render_list(record.get('how_it_works', []))}</article>
      </div>
    </section>
    <section>
      <h2>它不是什么</h2>
      <div class="not-list">{"".join(f'<div class="not-item">{e(x)}</div>' for x in record.get('not_this', [])) or '<p class="muted">暂无误区边界。</p>'}</div>
    </section>
    <section>
      <h2>和相近概念怎么分</h2>
      <div class="compare-grid">{render_comparisons(record.get('comparisons', []))}</div>
    </section>
    <section>
      <h2>放进知识地图里</h2>
      <div class="map">{render_related(record.get('related', []))}</div>
    </section>
    <section>
      <h2>它从哪里来</h2>
      <div class="timeline">{render_timeline(record.get('timeline', []))}</div>
    </section>
    <section>
      <h2>一个具体例子</h2>
      <article class="example"><h3>{e(example.get('title', '例子'))}</h3><p>{e(example.get('body', ''))}</p></article>
    </section>
    <section>
      <h2>小测一下</h2>
      <div class="quiz">{render_quiz(record.get('quiz', []))}</div>
    </section>
    <section>
      <h2>三句话带走</h2>
      <div class="takeaways">{"".join(f'<div class="takeaway">{e(x)}</div>' for x in record.get('takeaways', []))}</div>
    </section>
    <section class="sources">
      <h2>来源</h2>
      {render_sources(record.get('sources', []))}
    </section>
  </main>
  <footer>
    <div class="wrap">Concept Forge · 更新于 {e(updated)} · 本页为本地自包含 HTML，可直接打开复习。</div>
  </footer>
  <script>
    document.querySelectorAll('[data-reveal]').forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        var target = btn.parentElement.querySelector('.reveal');
        target.classList.toggle('open');
        btn.textContent = target.classList.contains('open') ? '收起区别' : '看区别';
      }});
    }});
    document.querySelectorAll('[data-choice]').forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        var card = btn.closest('.quiz-card');
        var answer = Number(card.dataset.answer);
        var choice = Number(btn.dataset.choice);
        var feedback = card.querySelector('.feedback');
        if (choice === answer) {{
          feedback.textContent = '答对了。' + card.dataset.explanation;
          feedback.className = 'feedback ok';
        }} else {{
          feedback.textContent = '还差一点。' + card.dataset.explanation;
          feedback.className = 'feedback no';
        }}
      }});
    }});
  </script>
</body>
</html>
"""


def update_index(workspace: Path, record: Dict[str, Any]) -> Dict[str, Any]:
    index = load_index(workspace)
    slug = record["slug"]
    entry = {
        "slug": slug,
        "title": record.get("title", ""),
        "aliases": record.get("aliases", []),
        "category": record.get("category", "概念"),
        "depth": record.get("depth", "standard"),
        "direct_answer": record.get("direct_answer", record.get("summary", "")),
        "summary": record.get("summary", ""),
        "updated_at": record.get("updated_at", now_date()),
        "concept_path": str(concept_dir(workspace, slug) / "concept.md"),
        "quarkdown_path": str(quarkdown_path(workspace, slug)),
        "json_path": str(concept_dir(workspace, slug) / "concept.json"),
        "html_path": str(html_path(workspace, slug)),
        "slidev_path": str(slidev_path(workspace, slug)),
    }
    entries = [x for x in index.get("entries", []) if x.get("slug") != slug]
    entries.append(entry)
    entries.sort(key=lambda x: normalize_text(x.get("title", "")))
    index["entries"] = entries
    save_index(workspace, index)
    return entry


def upsert(workspace: Path, record: Dict[str, Any]) -> Dict[str, str]:
    init_workspace(workspace)
    record = ensure_record(record)
    slug = record["slug"]
    cdir = concept_dir(workspace, slug)
    cdir.mkdir(parents=True, exist_ok=True)

    write_json(cdir / "concept.json", record)
    write_json(cdir / "sources.json", record.get("sources", []))
    (cdir / "concept.md").write_text(render_markdown(record), encoding="utf-8", newline="\n")
    quarkdown_path(workspace, slug).write_text(render_quarkdown(record), encoding="utf-8", newline="\n")
    html_file = html_path(workspace, slug)
    html_file.parent.mkdir(parents=True, exist_ok=True)
    html_file.write_text(render_html(record), encoding="utf-8", newline="\n")
    slides = write_slidev_project(workspace, slug, record)
    entry = update_index(workspace, record)
    return {
        "slug": slug,
        "concept_md": entry["concept_path"],
        "concept_qd": entry["quarkdown_path"],
        "concept_json": entry["json_path"],
        "html": entry["html_path"],
        "slidev": str(slides),
        "index": str(workspace_paths(workspace)["index"]),
    }


def validate(workspace: Path, slug: str) -> Tuple[bool, List[str]]:
    init_workspace(workspace)
    problems: List[str] = []
    cdir = concept_dir(workspace, slug)
    record_path = cdir / "concept.json"
    md_path = cdir / "concept.md"
    qd_path = quarkdown_path(workspace, slug)
    html_file = html_path(workspace, slug)
    slides = slidev_path(workspace, slug)

    if not record_path.exists():
        problems.append(f"missing {record_path}")
        return False, problems

    record = read_json(record_path, {})
    for field in REQUIRED_FIELDS:
        value = record.get(field)
        if value is None or value == "" or value == []:
            problems.append(f"missing or empty field: {field}")
    if not md_path.exists() or md_path.stat().st_size < 200:
        problems.append(f"concept.md missing or too small: {md_path}")
    if not qd_path.exists() or qd_path.stat().st_size < 200:
        problems.append(f"concept.qd missing or too small: {qd_path}")
    if not slides.exists() or slides.stat().st_size < 500:
        problems.append(f"slides.md missing or too small: {slides}")
    if not html_file.exists() or html_file.stat().st_size < 2000:
        problems.append(f"html missing or too small: {html_file}")
    else:
        content = html_file.read_text(encoding="utf-8", errors="ignore")
        for marker in ["一句话先懂", "小测一下", "三句话带走", "data-choice", "Concept Forge"]:
            if marker not in content:
                problems.append(f"html missing marker: {marker}")

    index = load_index(workspace)
    indexed = next((x for x in index.get("entries", []) if x.get("slug") == slug), None)
    if not indexed:
        problems.append("index missing slug")
    else:
        for field in ["direct_answer", "html_path", "quarkdown_path", "slidev_path"]:
            if not indexed.get(field):
                problems.append(f"index missing field: {field}")

    return not problems, problems


def doctor() -> Dict[str, Any]:
    quarkdown = shutil.which("quarkdown")
    slidev = shutil.which("slidev")
    npm = shutil.which("npm")
    pnpm = shutil.which("pnpm")
    return {
        "python": sys.executable,
        "version": VERSION,
        "optional_tools": {
            "quarkdown": quarkdown,
            "slidev": slidev,
            "node": shutil.which("node"),
            "npm": npm,
            "pnpm": pnpm,
        },
        "generated_without_optional_tools": [
            "concept.json",
            "concept.qd",
            "concept.md",
            "html/<slug>.html",
            "slidev/<slug>/slides.md",
        ],
        "install_or_compile_hints": {
            "quarkdown": "If installed, verify a mother draft with: quarkdown c concept.qd --strict --out <verify-dir>",
            "slidev": "Inside slidev/<slug>, run npm install or pnpm install once, then npm run dev/build/export as needed.",
        },
        "note": "Quarkdown and Slidev source files are first-class outputs. CLI tools are only needed when compiling or exporting.",
    }


def demo_record() -> Dict[str, Any]:
    return {
        "title": "Agent Skill",
        "slug": "agent-skill",
        "aliases": ["Agent Skill", "Skill", "Codex Skill", "AI Skill"],
        "category": "AI 工作流",
        "depth": "standard",
        "direct_answer": "一句话说，Agent Skill 像给 AI 准备的一本小手册：Prompt 是这次怎么做，Skill 是以后遇到同类任务都按这套做。",
        "summary": "Agent Skill 是一套可复用的任务说明书，让 AI 在特定场景里按稳定流程做事。",
        "plain_explanation": "它不是一次性的提问，而是把某类任务的经验、步骤、工具和检查标准打包起来，让以后遇到同类任务时可以直接调用。",
        "why_it_matters": "日常问题很零碎，如果每次都从头解释，知识会散掉。Skill 把可重复的做法固定下来，让 AI 的能力可以积累。",
        "how_it_works": ["描述什么时候触发", "规定执行步骤", "提供参考资料或脚本", "要求生成结果并检查质量"],
        "not_this": ["不是单句 Prompt", "不是插件本身", "不是只能用于写代码的东西"],
        "comparisons": [
            {
                "name": "Prompt",
                "summary": "Prompt 是一次对话里的指令。",
                "difference": "Prompt 更像临时吩咐；Skill 更像长期保存的工作手册。",
            },
            {
                "name": "Plugin",
                "summary": "Plugin 通常提供工具能力。",
                "difference": "Plugin 偏工具接入；Skill 偏任务流程和知识组织。",
            },
        ],
        "related": [
            {"name": "Prompt Engineering", "relation": "sibling", "why": "都在塑造 AI 行为，但 Skill 更强调复用。"},
            {"name": "Agent", "relation": "parent", "why": "Skill 通常服务于能执行多步骤任务的 Agent。"},
            {"name": "Knowledge Base", "relation": "next", "why": "Skill 产出的内容可以沉淀成知识库。"},
        ],
        "timeline": [
            {"label": "从 Prompt 到工作流", "detail": "单次提示越来越难承载复杂任务，于是可复用流程开始变重要。"},
            {"label": "从工作流到 Skill", "detail": "把触发条件、步骤、工具和检查标准放进同一个包里。"},
        ],
        "example": {
            "title": "一句话看懂",
            "body": "你可以每次都告诉 AI 怎么评估简历，也可以做一个简历评估 Skill，让它以后都按同一套标准处理。",
        },
        "memory_hook": "Prompt 是一句吩咐，Skill 是一本小手册。",
        "takeaways": ["Skill 解决的是复用问题。", "Skill 不是回答本身，而是产生回答的流程。", "好的 Skill 必须能触发、能执行、能检查。"],
        "quiz": [
            {
                "question": "Agent Skill 最像什么？",
                "options": ["一次聊天里的随口指令", "可复用的小手册", "浏览器标签页"],
                "answer": 1,
                "explanation": "它把某类任务的做法保存下来，方便反复调用。",
            }
        ],
        "sources": [{"title": "Local reasoning", "url": "", "note": "示例条目，用于测试 Concept Forge 工作流。"}],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Concept Forge workspace helper")
    parser.add_argument("--workspace", default=str(default_workspace()), help="Workspace directory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize workspace")

    lookup_p = sub.add_parser("lookup", help="Look up existing entries")
    lookup_p.add_argument("query")
    lookup_p.add_argument("--limit", type=int, default=5)

    plan_p = sub.add_parser("plan", help="Classify query depth and expected outputs")
    plan_p.add_argument("query")

    upsert_p = sub.add_parser("upsert", help="Store concept JSON and render artifacts")
    upsert_p.add_argument("--input", required=True, help="Path to concept JSON, or '-' for stdin")

    validate_p = sub.add_parser("validate", help="Validate one stored concept")
    validate_p.add_argument("--slug", required=True)

    sub.add_parser("doctor", help="Show optional tool availability")
    sub.add_parser("demo", help="Create demo Agent Skill concept")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).expanduser().resolve()

    try:
        if args.command == "init":
            print(json.dumps(init_workspace(workspace), ensure_ascii=False, indent=2))
            return 0

        if args.command == "lookup":
            print(json.dumps({"query": args.query, "matches": lookup(workspace, args.query, args.limit)}, ensure_ascii=False, indent=2))
            return 0

        if args.command == "plan":
            depth = classify_depth(args.query)
            payload = {"query": args.query, **output_plan(depth)}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "upsert":
            if args.input == "-":
                record = json.load(sys.stdin)
            else:
                record = read_json(Path(args.input), {})
            print(json.dumps(upsert(workspace, record), ensure_ascii=False, indent=2))
            return 0

        if args.command == "validate":
            ok, problems = validate(workspace, args.slug)
            print(json.dumps({"ok": ok, "problems": problems}, ensure_ascii=False, indent=2))
            return 0 if ok else 2

        if args.command == "doctor":
            print(json.dumps(doctor(), ensure_ascii=False, indent=2))
            return 0

        if args.command == "demo":
            result = upsert(workspace, demo_record())
            ok, problems = validate(workspace, result["slug"])
            result["validation_ok"] = ok
            result["validation_problems"] = problems
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if ok else 2

    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
