<p align="center">
  <a href="README.md">English</a> |
  <a href="README_ZH.md">簡體中文</a> |
  <a href="README_TW.md">繁體中文</a>
</p>

# 🔍 Zirflow Research Agent — 統一分層搜索系統

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/) [![狀態](https://img.shields.io/badge/Status-Public-brightgreen.svg)]](https://github.com/zirflow/zirflow-openclaw-zirflow-search)

**多源 AI 搜索系統 — 搜索一次，同時獲得來自 Tavily AI + Reddit + GitHub + V2EX + RSS + B站 + 微信公衆號等 16+ 平臺的結果。**

---

## 🎯 功能特性

| 層級 | 名稱 | 說明 |
|------|------|------|
| **Tier 0** | URL 抓取 | Jina Reader 四級降級，<1 秒 |
| **Tier 1** | Tavily AI 搜索 | 3 個 Key 自動故障轉移 |
| **Tier 2** | 平臺專項路由 | Reddit、GitHub、V2EX、RSS、B站、微信公衆號 |
| **Tier 3** | GitHub 深度分析 | 6 步倉庫完整分析 |
| **Tier 4** | 瀏覽器兜底 | Playwright，極慢易驗證碼 |

---

## 🚀 快速開始

```bash
# 標準搜索
python3 scripts/search.py "AI Agent 趨勢 2026"

# 多平臺聯動搜索（推薦複雜問題使用）
python3 scripts/search.py "AI Agent" --all --max 10

# 強制 GitHub 搜索
python3 scripts/search.py "OpenClaw agent" --tier 2 --engine github

# 新聞篩選
| `--topic` | Tavily 話題：`general` 或 `news` | general |
```

---

## ⚙️ 安裝配置

```bash
# 1. 安裝依賴
pip install tavily requests feedparser yt-dlp

# 2. 複製配置模板
cp config.env.template ~/.openclaw/skills/zirflow-search/config.env

# 3. 添加 Tavily API Key（免費額度：每天 1000 次）
# 申請地址：https://tavily.com
TAVILY_API_KEY_1=tvly-xxxxx
TAVILY_API_KEY_2=tvly-yyyyy
TAVILY_API_KEY_3=tvly-zzzzz
```

---

## 🔧 作爲 OpenClaw Skill 使用

將項目複製到 OpenClaw skills 目錄：

```bash
cp -r ~/.openclaw/skills/zirflow-search/
```

然後在任何 OpenClaw Agent 中調用：

```
search "AI Agent 創業融資 2026"
```

---

## 📊 參數說明

| 參數 | 說明 | 默認值 |
|------|------|------|
| `query` | 搜尋詞或 URL（位置參數） | — |
| `--all` | 🔥 多平臺聯動搜尋，所有平臺同時搜 | 關閉 |
| `--fetch-url` | 強制 Tier 0 URL 抓取 | 自動判斷 |
| `--tier <0-4>` | 指定起始層級 | 自動 |
| `--engine` | 強制平臺路由 (reddit/github/v2ex/rss/wechat) | auto |
| `--days <n>` | 時間範圍（天）| 7 |
| `--max <n>` | 最大結果數 | 10 |
| `--deep` | Tavily 深度研究模式 | 關閉 |
| `--topic` | Tavily 話題：`general` 或 `news` | general |
| `--lang` | 語言偏好：`auto`、`cn`、`en` | auto |
| `--output` | 輸出格式：`text` 或 `json` | text |
| `--no-tier1` | 跳過 Tavily（只用免費平臺）| false |

ls/zirflow-search/scripts/search.py "AI Agent" --all --max 10
```

### ✅ 學習成果檢驗

學完之後，你應該能回答以下問題：
1. Zirflow Search 的 Tier 0-4 分別是什麼？各自適用什麼場景？
2. 搜索 "reddit AI startup" 應該用哪個 Tier 和引擎？
3. 想深度研究一個 GitHub 倉庫，命令是什麼？
4. Tavily 額度用完了，怎麼免費搜索？
5. 可信度等級 🟢🟡🔵⚪ 分別代表什麼？

### 📂 目錄結構

```
zirflow-openclaw-zirflow-search/
├── SKILL.md              ← 核心文檔（必讀）
├── README_ZH.md         ← 本文件（簡體中文）
scripts/
│   └── search.py        ← 搜索入口腳本
├── config.env.template   ← Key 配置模板
└── tests/               ← 測試用例
```

### 🆘 常見問題

| 問題 | 解決方案 |
|------|---------|
| README 讀不懂 | 先讀 SKILL.md 的 Tier 決策樹 |
| API Key 報錯 | 檢查 `~/.openclaw/env` 是否寫入正確 |
| Tavily 報錯 | 用 `--no-tier1` 切換免費平臺 |
| 腳本報錯 | 確保 Python ≥ 3.10 |

### 🚀 學會之後

執行搜索：
```bash
python3 ~/.openclaw/skills/zirflow-search/scripts/search.py "你的問題"
```

---

## 📖 Skill 基本信息

| 字段 | 值 |
|------|-----|
| 名稱 | zirflow-search |
| 作者 | Zirflow 臻孚 |
| 版本 | 1.0.0 |
| 平臺 | OpenClaw |
| 許可證 | MIT-0 |

---

## 📜 許可證

MIT-0 — 可免費商用，無需署名。
