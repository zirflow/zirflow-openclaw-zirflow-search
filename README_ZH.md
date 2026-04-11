<p align="center">
  <a href="README.md">English</a> |
  <a href="README_ZH.md">简体中文</a> |
  <a href="README_TW.md">繁體中文</a>
</p>

# 🔍 Zirflow Research Agent — 统一分层搜索系统

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/) [![状态](https://img.shields.io/badge/Status-Public-brightgreen.svg)]](https://github.com/zirflow/zirflow-openclaw-zirflow-search)

**多源 AI 搜索系统 — 搜索一次，同时获得来自 Tavily AI + Reddit + GitHub + V2EX + RSS + B站 + 微信公众号等 16+ 平台的结果。**

---

## 🎯 功能特性

| 层级 | 名称 | 说明 |
|------|------|------|
| **Tier 0** | URL 抓取 | Jina Reader 四级降级，<1 秒 |
| **Tier 1** | Tavily AI 搜索 | 3 个 Key 自动故障转移 |
| **Tier 2** | 平台专项路由 | Reddit、GitHub、V2EX、RSS、B站、微信公众号 |
| **Tier 3** | GitHub 深度分析 | 6 步仓库完整分析 |
| **Tier 4** | 浏览器兜底 | Playwright，极慢易验证码 |

---

## 🚀 快速开始

```bash
# 标准搜索
python3 scripts/search.py "AI Agent 趋势 2026"

# 多平台联动搜索（推荐复杂问题使用）
python3 scripts/search.py "AI Agent" --all --max 10

# 强制 GitHub 搜索
python3 scripts/search.py "OpenClaw agent" --tier 2 --engine github

# 新闻筛选
python3 scripts/search.py "AI startup" --tier 1 --topic news --days 7
```

---

## ⚙️ 安装配置

```bash
# 1. 安装依赖
pip install tavily requests feedparser yt-dlp

# 2. 复制配置模板
cp config.env.template ~/.openclaw/skills/zirflow-search/config.env

# 3. 添加 Tavily API Key（免费额度：每天 1000 次）
# 申请地址：https://tavily.com
TAVILY_API_KEY_1=tvly-xxxxx
TAVILY_API_KEY_2=tvly-yyyyy
TAVILY_API_KEY_3=tvly-zzzzz
```

---

## 🔧 作为 OpenClaw Skill 使用

将项目复制到 OpenClaw skills 目录：

```bash
cp -r ~/.openclaw/skills/zirflow-search/
```

然后在任何 OpenClaw Agent 中调用：

```
search "AI Agent 创业融资 2026"
```

---

## 📊 参数说明

| 参数 | 说明 | 默认值 |
|------|------|------|
| `--all` | 🔥 多平台联动搜索，所有平台同时搜 | 关闭 |
| `--fetch-url` | 强制 Tier 0 URL 抓取 | 自动判断 |
| `--tier <0-4>` | 指定起始层级 | 自动 |
| `--engine` | 强制平台路由 (reddit/github/v2ex/rss/wechat) | auto |
| `--max <n>` | 最大结果数 | 10 |
| `--days <n>` | 时间范围（天）| 7 |
| `--deep` | Tavily 深度研究模式 | 关闭 |
| `--topic` | Tavily 话题：`general` 或 `news` | general |
| `--lang` | 语言偏好：`auto`、`cn`、`en` | auto |
| `--output` | 输出格式：`text` 或 `json` | text |
| `--no-tier1` | 跳过 Tavily（只用免费平台）| false |

---

## 🗂️ 项目结构

```
zirflow-openclaw-zirflow-search/
├── SKILL.md              ← 核心文档（必读）
├── README.md             ← 英文文档
├── README_ZH.md         ← 简体中文文档
├── README_TW.md         ← 繁体中文文档
├── scripts/
│   └── search.py        ← 搜索入口脚本
├── config.env.template   ← Key 配置模板
└── tests/               ← 测试用例
```

---

## 🤖 AI Agent 自学指南

本节帮助其他 AI Agent 自主学习安装和使用 Zirflow Search。

### 🎯 学习任务

学习和安装本项目：

**项目地址**：https://github.com/zirflow/zirflow-openclaw-zirflow-search

### 📋 学习步骤（按顺序执行）

**第一步 — 阅读 README**
打开上方链接，阅读 README_ZH.md（简体中文版）。

**第二步 — 阅读 SKILL.md**
在项目根目录找到 SKILL.md 并阅读。包含：
- Tier 0/1/2/3/4 完整架构和适用场景
- 每个层级的速度、成本、数据来源
- 决策流程图
- 各平台触发关键词
- 可信度分级说明

**第三步 — 安装依赖**
```bash
pip install tavily requests feedparser yt-dlp
```

**第四步 — 配置 API Keys**
1. 在 https://tavily.com 注册获取免费 API Key（每天 1000 次）
2. 写入 `~/.openclaw/env`：
   ```
   TAVILY_API_KEY_1=你的key
   ```

**第五步 — 运行测试**
```bash
# 标准搜索
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent 趋势 2026"

# 多平台联动搜索（推荐复杂研究使用）
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "AI Agent" --all --max 10
```

### ✅ 学习成果检验

学完之后，你应该能回答以下问题：
1. Zirflow Search 的 Tier 0-4 分别是什么？各自适用什么场景？
2. 搜索 "reddit AI startup" 应该用哪个 Tier 和引擎？
3. 想深度研究一个 GitHub 仓库，命令是什么？
4. Tavily 额度用完了，怎么免费搜索？
5. 可信度等级 🟢🟡🔵⚪ 分别代表什么？

### 📂 目录结构

```
zirflow-openclaw-zirflow-search/
├── SKILL.md              ← 核心文档（必读）
├── README_ZH.md         ← 本文件（简体中文）
scripts/
│   └── search.py        ← 搜索入口脚本
├── config.env.template   ← Key 配置模板
└── tests/               ← 测试用例
```

### 🆘 常见问题

| 问题 | 解决方案 |
|------|---------|
| README 读不懂 | 先读 SKILL.md 的 Tier 决策树 |
| API Key 报错 | 检查 `~/.openclaw/env` 是否写入正确 |
| Tavily 报错 | 用 `--no-tier1` 切换免费平台 |
| 脚本报错 | 确保 Python ≥ 3.10 |

### 🚀 学会之后

执行搜索：
```bash
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "你的问题"
```

---

## 📖 Skill 基本信息

| 字段 | 值 |
|------|-----|
| 名称 | zirflow-search |
| 作者 | Zirflow 臻孚 |
| 版本 | 1.0.0 |
| 平台 | OpenClaw |
| 许可证 | MIT-0 |

---

## 📜 许可证

MIT-0 — 可免费商用，无需署名。
