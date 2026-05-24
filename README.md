# Concept Forge

Concept Forge 是一个 Codex Skill：把用户随口问出的概念、关键词、陌生名词或比较问题，转成可复用的个人知识资产。

它的核心输出不是一段一次性回答，而是一套可以沉淀和复用的内容：

- 一句直接解释：先让用户立刻听懂。
- Quarkdown 母稿：作为统一、可长期维护的知识库文本。
- 互动 HTML：适合快速复习、记忆和分享。
- Slidev 演示稿源码：适合公开讲解或二次整理成演示。
- JSON 索引：让同一问题下次直接复用，不重复劳动。

## Skill 描述

将日常问题、概念、关键词、陌生术语，以及“X 是什么 / X 和 Y 有什么区别”这类请求，转换为中文知识卡片、Quarkdown 母稿、Slidev 演示稿源码和互动 HTML 解释页。适合碎片化知识整理、概念记忆、工具理解、术语对比、个人知识库沉淀和可复用学习材料生成。

## 关键词

概念解释、知识卡片、互动 HTML、Quarkdown、Slidev、知识库、个人知识库、概念地图、术语对比、AI 学习助手、碎片知识整理、Prompt 对比、工具解释、横纵分析、轻量研究、记忆钩子、复用索引、中文知识管理、学习页面、演示稿生成。

## 安装

把这个仓库复制到 Codex 的 skills 目录即可：

```powershell
Copy-Item -Recurse . "$env:USERPROFILE\.codex\skills\concept-forge"
```

如果你从 GitHub 克隆：

```powershell
git clone https://github.com/FeixueCode/concept-forge.git "$env:USERPROFILE\.codex\skills\concept-forge"
```

重启 Codex 后，Skill 会出现在可用 skills 中。

## 使用方式

直接提问即可，例如：

```text
Harness 工程是什么
Skill 和 Prompt 有什么区别
Obsidian 是什么，适合什么人
RAG 和 Agent 的区别
```

推荐默认工作目录：

```text
<当前工作目录>/concept-forge-workspace
```

第一次使用时初始化：

```powershell
python scripts/concept_forge.py init --workspace ./concept-forge-workspace
```

测试示例：

```powershell
python scripts/concept_forge.py --workspace ./concept-forge-workspace demo
python scripts/concept_forge.py --workspace ./concept-forge-workspace validate --slug agent-skill
python scripts/concept_forge.py --workspace ./concept-forge-workspace lookup "Skill 是什么"
```

## 产物结构

```text
concept-forge-workspace/
  knowledge/
    index.json
    concepts/<slug>/
      concept.json
      concept.qd
      concept.md
      sources.json
  html/<slug>.html
  slidev/<slug>/slides.md
  slidev/<slug>/package.json
```

## 工具依赖

基础生成只需要 Python 标准库。

Quarkdown 和 Slidev 是正式产物格式的一部分，但命令行工具只在“编译、预览、导出”时需要：

- Quarkdown：用于把 `concept.qd` 编译成正式阅读页或 PDF。
- Slidev：用于把 `slides.md` 预览、构建或导出演示稿。

检查环境：

```powershell
python scripts/concept_forge.py doctor
```

## 文档

- `docs/PRD.md`：产品需求文档。
- `docs/DESIGN.md`：设计思路与系统逻辑。
- `docs/KEYWORDS.md`：技能描述、触发词和关键词。
- `examples/harness-engineering/`：一次真实测试产物。
