# 🔍 Zirflow Research Agent

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

## License

MIT-0 — Free for commercial use, no attribution required.
