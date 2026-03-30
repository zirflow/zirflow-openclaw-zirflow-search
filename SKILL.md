---
name: zirflow-search
description: >
  Zirflow 臻孚公司专属统一搜索 SKILL。
  整合所有搜索能力：Tier 0(Jina URL抓取) → Tier 1(Tavily AI) → Tier 2(agent-reach 16平台) → Tier 3(GitHub专项) → Tier 4(兜底)。
  以搜索专家身份运作：多源交叉验证，结构化输出，可信度分级。
---

# Zirflow Search — 统一分层搜索系统

## 架构原则

```
用户查询
    │
    ├─ 已知URL？  → Tier 0（Jina四级降级，<1秒完成）
    │
    ├─ 通用问题？  → Tier 1（Tavily AI，3Key自动轮换）
    │
    ├─ 平台专项？  → Tier 2（agent-reach 免费平台API）
    │                Reddit · GitHub · V2EX · RSS · B站 · 微信公众号
    │
    ├─ GitHub深度？→ Tier 3（github-repo-search 6步分析）
    │
    └─ 全部失败？  → Tier 4（返回可打开的搜索链接）
```

---

## Tier 详解

### Tier 0 — 已知URL抓取 ✅（增强版）
- **原理**：smart-web-fetch 精华版（urllib直连 + SSL处理 + URL自动预处理）
- **四级降级**：Jina Reader → markdown.new → defuddle.md → raw
- **增强点**：自动trim空格、自动补https、自动处理SSL证书
- **速度**：< 1秒
- **成本**：0
- **适用**：用户提供URL，或从Tier 1结果中二次抓取详情

### Tier 1 — Tavily AI 搜索 ✅（优先）
- **原理**：Tavily API，AI去噪音结构化摘要
- **Key轮换**：3 Key 自动故障转移（chenfei5873 → aki → yuanguojun0769）
- **速度**：2-5秒
- **成本**：免费额度 1000次/天/Key
- **适用**：通用搜索、新闻、研究问题

### Tier 2 — agent-reach 平台专项 ✅（免费）
- **原理**：平台原生免费API，无CAPTCHA
- **成本**：0
- **平台路由**：

| 关键词触发 | 平台 | API | 状态 |
|-----------|------|-----|------|
| `reddit` / `r/` | Reddit | JSON API | ✅ |
| `github` / `repo` | GitHub | REST API (免Key) | ✅ |
| `v2ex` | V2EX | 公开API | ✅ |
| `rss:` / `feed` | RSS | feedparser | ✅ |
| `youtube` / `b站` / `bilibili` | 视频 | yt-dlp | ✅ |
| `公众号` / `微信` | 微信公众号 | miku_ai | ✅ |
| `播客` / `podcast` | 播客 | Groq Whisper | ⚠️ 需配置Key |
| *(通用)* | 综合 | Reddit+GitHub+V2EX聚合 | ✅ |

### Tier 3 — GitHub 深度分析
- **工具**：github-repo-search 完整6步法
- **适用**：GitHub项目详细分析（README、Stars趋势、贡献者、Issues）

### Tier 4 — 浏览器兜底
- **工具**：Playwright
- **⚠️**：极慢、易CAPTCHA，仅在其他全失败时使用

---

## 快速使用

```bash
# 标准搜索（自动分层，优先Tier 1）
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent最新动态2026"

# 🔥 联动搜索（多平台同时搜，推荐复杂问题用）
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent" --all --max 10
# 同时搜：Tavily AI + Reddit + GitHub + V2EX，结果并行抓取合并去重

# 强制URL抓取
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "https://github.com/langgenius/dify" --fetch-url

# 指定平台路由
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent" --tier 2 --engine github
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "reddit AI trends" --tier 2 --engine reddit

# 新闻搜索
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent" --tier 1 --topic news --days 7

# 深度研究
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent trends 2026" --tier 1 --deep
```

---

## 参数说明

| 参数 | 说明 | 默认 |
|------|------|------|
| `--all` | 🔥 联动搜索：所有平台同时搜，结果合并去重 | 关闭 |
| `--fetch-url` | 强制Tier 0 URL抓取 | 自动判断 |
| `--tier <0-4>` | 指定起始层级 | 自动（1或2）|
| `--engine` | 强制平台路由 (reddit/github/v2ex/rss/wechat) | auto |
| `--max <n>` | 最大结果数 | 10 |
| `--days <n>` | 时间范围（天）| 7 |
| `--deep` | Tavily 深度研究模式 | 关闭 |
| `--topic news` | Tavily 新闻话题 | general |
| `--lang` | 语言偏好 (cn/en/auto) | auto |
| `--skip-tier1` | 跳过 Tavily（只用免费平台）| false |

---

## 参数说明

| 参数 | 说明 | 默认 |
|------|------|------|
| `--fetch-url` | 强制Tier 0 URL抓取 | 自动判断 |
| `--tier <0-4>` | 指定起始层级 | 自动（1或2）|
| `--engine` | 强制平台路由 | auto |
| `--max <n>` | 最大结果数 | 10 |
| `--days <n>` | 时间范围（天）| 7 |
| `--deep` | Tavily深度研究模式 | false |
| `--topic` | Tavily话题 (general/news) | general |
| `--lang` | 语言偏好 (cn/en/auto) | auto |
| `--skip-tier1` | 跳过Tavily，直接Tier 2 | false |

---

## 可信度分级

| 等级 | 含义 | 示例 |
|------|------|------|
| 🟢 | 官方/权威/直接API | GitHub API、Reddit JSON |
| 🟡 | 专业媒体/社区 | Tavily整理结果 |
| 🔵 | 开源/公开数据 | V2EX热门话题 |
| ⚪ | 未验证/兜底 | fallback链接 |

---

## 输出示例

```
📡 Zirflow Search | TIER-1 | 查询: AI Agent最新动态2026
============================================================

1. 《AI Agent智能体技术发展报告》正式发布
   🟢 可信度: 🟡 | 来源: tavily-key1
   📝 2026年AI Agent趋势全景图...
   🔗 https://example.com/article

2. ★146,292 langflow-ai/langflow
   🟢 可信度: 🟢 | 来源: github-rest-api
   📝 Multi-Agent Framework...
   🔗 https://github.com/langflow-ai/langflow
```

---

## 核心文件

```
~/.openclaw/skills/zirflow-search/
├── SKILL.md              ← 本文件
└── scripts/
    └── search.py         ← 统一入口（Python 3）
```

---

## 依赖配置

| 依赖 | 必需 | 配置位置 |
|------|------|---------|
| Python 3 | ✅ | 系统自带 |
| TAVILY_API_KEY_1/2/3 | ✅ 已配置 | `~/.openclaw/env` |
| agent-reach | ✅ 已安装 | `~/.openclaw/skills/agent-reach/` |
| github-repo-search | ✅ 已安装 | `~/.agents/skills/github-repo-search/` |
| yt-dlp | ✅ 系统自带 | pip |

---

## Agent 调用规范

```python
# === 决策流程 ===

if is_url(query):
    # → Tier 0
    result = tier0_url_fetch(url)
    
elif has_tavily_key():
    # → Tier 1（优先）
    result = tier1_tavily(query, deep=..., topic=...)
    
elif "github" in query or "repo" in query.lower():
    # → Tier 2 GitHub专项
    result = tier2_github(query)
    
elif "reddit" in query.lower() or "r/" in query:
    # → Tier 2 Reddit
    result = tier2_reddit(query)
    
elif "v2ex" in query.lower():
    # → Tier 2 V2EX
    result = tier2_v2ex(query)
    
elif "公众号" in query or "微信" in query:
    # → Tier 2 微信公众号
    result = tier2_wechat(query)
    
else:
    # → Tier 2 agent-reach综合路由
    result = tier2_agent_reach(query)
```

---

## License

Zirflow Internal — All Rights Reserved
