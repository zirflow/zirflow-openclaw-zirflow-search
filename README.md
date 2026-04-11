<p align="center">
  <a href="README.md">English</a> |
  <a href="README_ZH.md">简体中文</a> |
  <a href="README_TW.md">繁體中文</a>
</p>

# 🔍 Zirflow Research Agent
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/) [![Status](https://img.shields.io/badge/Status-Public-brightgreen.svg)]


Multi-source AI search system with tiered architecture — search once, get results from Tavily AI + Reddit + GitHub + V2EX + RSS + YouTube + WeChat simultaneously.

## Features

- **Tier 0**: URL Fetch (Jina Reader 4-level fallback, <1s)
- **Tier 1**: Tavily AI Search (3 API Keys auto-failover)
- **Tier 2**: Platform Router — Reddit, GitHub, V2EX, RSS, B站, YouTube, WeChat
- **Tier 3**: Deep GitHub Analysis (6-step repo analysis)
- **Tier 4**: Browser Fallback (Playwright)

## Quick Start

```bash
# Standard search
python3 scripts/search.py "AI Agent trends 2026"

# Multi-platform simultaneous search
python3 scripts/search.py "AI Agent" --all --max 10

# Force GitHub search
python3 scripts/search.py "OpenClaw agent" --tier 2 --engine github

# News filter
python3 scripts/search.py "AI startup" --tier 1 --topic news --days 7
```

## Setup

```bash
# 1. Install dependencies
pip install tavily requests feedparser yt-dlp

# 2. Copy config
cp config.env.template ~/.openclaw/skills/zirflow-search/config.env

# 3. Add your Tavily API keys (free tier: 1000 searches/day)
# Get keys at: https://tavily.com
TAVILY_API_KEY_1=tvly-xxxxx
TAVILY_API_KEY_2=tvly-yyyyy
TAVILY_API_KEY_3=tvly-zzzzz
```

## Use as OpenClaw Skill

Copy this folder to your OpenClaw skills directory:

```bash
cp -r ~/.openclaw/skills/zirflow-search/
```

Then call it from any OpenClaw agent:

```
search "AI Agent startup funding 2026"
```

## Skill Info

| Field | Value |
|-------|-------|
| Name | zirflow-search |
| Author | Zirflow 臻孚 |
| Version | 1.0.0 |
| Platform | OpenClaw |
| License | MIT-0 |

---

## 🤖 For AI Agents — Self-Learning Guide

This section helps other AI agents learn to install and use Zirflow Search autonomously.

### 🎯 Learning Task

Study and install this project:

**Repo**: https://github.com/zirflow/zirflow-openclaw-zirflow-search

### 📋 Steps (execute in order)

**Step 1 — Read README.md**
Review the project overview, features (Tier 0-4), quick start commands, and installation.

**Step 2 — Read SKILL.md**
Located in the project root. It contains:
- Full Tier 0/1/2/3/4 architecture and use cases
- Speed, cost, and data sources per tier
- Decision flow diagram
- Platform trigger keywords
- Credibility rating system

**Step 3 — Install dependencies**
```bash
pip install tavily requests feedparser yt-dlp
```

**Step 4 — Configure API Keys**
1. Get a free Tavily API key at https://tavily.com (1000 searches/day)
2. Write to `~/.openclaw/env`:
   ```
   TAVILY_API_KEY_1=your_key_here
   ```

**Step 5 — Run a test**
```bash
# Standard search
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent trends 2026"

# Multi-platform simultaneous search (recommended for complex research)
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent" --all --max 10
```

### ✅ Learning Checklist

After learning, you should be able to answer:
1. What are Tier 0-4 in Zirflow Search, and when does each apply?
2. Which tier and engine should you use for "reddit AI startup"?
3. What's the command for deep GitHub repo analysis?
4. How do you search for free when Tavily quota runs out?
5. What do credibility ratings 🟢🟡🔵⚪ mean?

### 📂 Project Structure

```
zirflow-openclaw-zirflow-search/
├── SKILL.md              ← Core documentation (required reading)
├── README.md             ← This file	scripts/
│   └── search.py         ← Search entry script
├── config.env.template   ← Key config template
└── tests/                ← Test cases
```

### 🆘 Common Issues

| Problem | Solution |
|---------|----------|
| README unclear | Read SKILL.md Tier decision tree first |
| API Key error | Check `~/.openclaw/env` is written correctly |
| Tavily error | Use `--skip-tier1` to switch to free platforms |
| Script error | Ensure Python ≥ 3.10 |

### 🚀 After Learning

You can now execute searches:
```bash
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "your query"
```

---

## License

MIT-0 — Free for commercial use, no attribution required.
