#!/usr/bin/env python3
"""
Zirflow Search — 统一分层搜索系统
=====================================
分层架构：
  Tier 0 → 已知URL（Jina Reader四级降级抓取）
  Tier 1 → 通用问题（ Tavily AI搜索，3Key自动轮换）
  Tier 2 → 平台专项（agent-reach 16平台智能路由）
  Tier 3 → 垂直深度（github-repo-search 6步分析）
  Tier 4 → 兜底（提供可打开的搜索链接）
"""

import sys
import os
import re
import json
import argparse
import subprocess
import time
import ssl
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

# === 加载 OpenClaw 环境变量 ===
_env_file = os.path.expanduser("~/.openclaw/env")
if os.path.exists(_env_file):
    with open(_env_file) as f:
        for line in f:
            line = line.strip()
            # 去掉注释（# 后面的内容）
            if "#" in line:
                line = line.split("#")[0].strip()
            if line and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k:
                    os.environ.setdefault(k, v)

# ============ 自动加载 Keys（供其他 Agent 使用）============
def load_env_config():
    """从 config.env 加载 API Keys"""
    import os
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.env")
    if os.path.exists(config_path):
        for line in open(config_path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k] = v
load_env_config()

# ============ 配置 ============

SMART_WEB_FETCH = os.path.expanduser("~/.openclaw/skills/smart-web-fetch/scripts/fetch.py")
BAIYU_URL_MD = os.path.expanduser("/home/zirflow/.bun/bin/bun run ~/.openclaw/skills/baoyu-url-to-markdown/scripts/main.ts")
TAVILY_SEARCH = os.path.expanduser("~/.openclaw/skills/tavily-search/scripts/search.mjs")
TAVILY_EXTRACT = os.path.expanduser("~/.openclaw/skills/tavily-search/scripts/extract.mjs")

# 搜索引擎已废弃，改用 agent-reach 平台 API
# ENGINES 已移除（multi-search-engine 已删除）

def jina_ai_search(query, max_results=10):
    """使用 Jina AI 搜索（无CAPTCHA，直接返回摘要）
    URL: https://s.jina.ai/{query}
    返回格式: Markdown，带来源标注
    """
    encoded_q = quote_plus(query)
    url = f"https://s.jina.ai/{encoded_q}"
    
    print(f"[TIER-2] Jina AI 搜索 → {url}", file=sys.stderr)
    
    cmd = f'curl -s --max-time 20 -H "Accept: application/json" "{url}"'
    out, err, code = run_cmd(cmd, timeout=25)
    
    if code == 0 and out:
        try:
            data = json.loads(out)
            results = []
            if "results" in data:
                for item in data["results"][:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")[:300],
                        "source": f"jina.ai",
                        "engine": "jina-ai",
                        "confidence": "🟡"
                    })
            if results:
                print(f"[TIER-2] Jina AI 返回 {len(results)} 条结果", file=sys.stderr)
                return results
        except json.JSONDecodeError:
            pass
    
    print(f"[TIER-2] Jina AI 搜索失败: {err[:100] if err else '无响应'}", file=sys.stderr)
    return []

# ============ 工具函数 ============

def run_cmd(cmd, timeout=30, capture=True):
    """执行shell命令，返回(stdout, stderr, returncode)"""
    try:
        if capture:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip(), r.stderr.strip(), r.returncode
        else:
            r = subprocess.run(cmd, shell=True, timeout=timeout)
            return "", "", r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except Exception as e:
        return "", str(e), -1


def is_url(text):
    """判断输入是否是URL"""
    text = text.strip()
    if text.startswith("http://") or text.startswith("https://"):
        return True
    if re.match(r"^[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}", text):
        return True
    return False


def extract_links_from_html(html, engine="duckduckgo"):
    """从搜索引擎HTML结果中提取链接标题
    
    ⚠️ 大多数搜索引擎有 CAPTCHA/UA 检测，提取结果可能不完整
    建议优先使用 Jina AI Search（s.jina.ai）作为 Tier-2 主要方式
    """
    links = []
    html_lower = html.lower()
    
    # DuckDuckGo HTML 提取（Lite版本）
    if engine == "duckduckgo":
        # 匹配 DuckDuckGo Lite 结果
        patterns = [
            r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>',
            r'<p class="result__snippet"[^>]*>([^<]+)</p>',
            r'<a href="(/d/\?uddg=([^"]+)"[^>]*>[^<]+</a>',  # redirect URLs
        ]
        for pat in patterns:
            for match in re.finditer(pat, html):
                if len(match.groups()) == 2 and match.group(2):
                    url = match.group(1)
                    title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                    if url.startswith("/"):
                        url = "https://duckduckgo.com" + url
                    if url.startswith("http") and title and len(title) > 5:
                        links.append({"url": url, "title": title[:200], "engine": "duckduckgo"})
    
    # 百度提取
    elif engine == "baidu":
        patterns = [
            r'<h3[^>]*class="[^"]*c-title[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            r'<div[^>]*class="[^"]*c-abstract[^"]*"[^>]*>([^<]+)</div>',
            r'<a[^>]*class="[^"]*c-showurl[^"]*"[^>]*href="([^"]+)"',  # URL link
        ]
        for pat in patterns:
            for match in re.finditer(pat, html, re.DOTALL):
                groups = match.groups()
                if len(groups) >= 2:
                    url = groups[0]
                    title = re.sub(r'<[^>]+>', '', groups[1]).strip()
                    if url and title and len(title) > 3:
                        links.append({"url": url, "title": title[:200], "engine": "baidu"})
    
    # Bing 提取（Bing 使用不同的 HTML 结构）
    elif engine == "bing":
        patterns = [
            # 标准结果: <h2><a href="URL" ...>Title</a></h2>
            r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            # Bing 的结果列表中的链接
            r'<li[^>]*class="[^"]*sa-element[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        ]
        for pat in patterns:
            for match in re.finditer(pat, html, re.DOTALL):
                url = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                if url.startswith("http") and title and len(title) > 5:
                    links.append({"url": url, "title": title[:200], "engine": "bing"})
    
    # Brave 提取（使用 result-content 结构）
    elif engine == "brave":
        # Brave 使用 <a class="title"> 或 h3 + a
        patterns = [
            r'<a[^>]*class="[^"]*title[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            r'<h3[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        ]
        for pat in patterns:
            for match in re.finditer(pat, html, re.DOTALL):
                url = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                # 过滤 Brave 自家链接
                if url.startswith("http") and "brave.com" not in url.lower() and title and len(title) > 5:
                    links.append({"url": url, "title": title[:200], "engine": "brave"})
    
    # Startpage 提取
    elif engine == "startpage":
        patterns = [
            r'<a[^>]*class="[^"]*title[^"]*"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
            r'<h3[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',
        ]
        for pat in patterns:
            for match in re.finditer(pat, html, re.DOTALL):
                url = match.group(1)
                title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
                if url.startswith("http") and title and len(title) > 5:
                    links.append({"url": url, "title": title[:200], "engine": "startpage"})
    
    # 去重+过滤
    seen = set()
    result = []
    for link in links:
        key = link["url"].split("?")[0][:100]  # 去重基础URL
        if key not in seen and "search?" not in link["url"]:
            seen.add(key)
            result.append(link)
    
    return result[:15]


# ============ Tier 0: URL 抓取（Jina 四级降级，增强版）============

def jina_fetch(url, timeout=20):
    """使用 Jina Reader 抓取 URL（smart-web-fetch 精华版）"""
    # URL 预处理：去空格、补协议
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    jina_url = f"https://r.jina.ai/{url}"

    # SSL context（处理证书问题）
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    try:
        req = Request(
            jina_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "text/plain, text/markdown, */*",
            }
        )
        with urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            if content and len(content) > 50:
                return content, "jina"
    except Exception:
        pass
    return None, None


def smart_fetch_fallback(url, timeout=20):
    """smart-web-fetch 四级降级抓取（增强版）

    合并 smart-web-fetch 精华：
    - URL 预处理（去空格、补协议）
    - SSL context 处理
    - urllib 直连（跳过 curl subprocess，更快更稳）
    - 四级降级：Jina → markdown.new → defuddle → raw
    """
    # URL 预处理
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    # SSL context
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    # 四级降级服务
    services = [
        ("jina",         lambda u: f"https://r.jina.ai/{u}"),
        ("markdown.new", lambda u: f"https://markdown.new/{u}"),
        ("defuddle.md",  lambda u: f"https://defuddle.md/{u}"),
    ]

    for service_name, url_builder in services:
        try:
            clean_url = url_builder(url)
            req = Request(
                clean_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; zirflow-search/1.0)",
                    "Accept": "text/plain, text/markdown, */*",
                }
            )
            with urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
                content = resp.read().decode("utf-8", errors="ignore")
                if content and len(content) > 100:
                    return content, service_name, service_name
        except Exception:
            continue

    # 最终降级：raw
    try:
        raw_url = url
        req = Request(
            raw_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            return content[:5000], "raw", "raw"
    except Exception:
        pass

    return None, None, None


    """使用指定搜索引擎搜索
    
    ⚠️ 大多数搜索引擎有 CAPTCHA/UA 检测，此函数作为降级方案
    实际使用时优先使用 Bing International（ensearch=1）
    """
    if engine_name not in ENGINES:
        print(f"[WARN] 未知引擎: {engine_name}，切换到 bing", file=sys.stderr)
        engine_name = "bing"
    
    url_template = ENGINES[engine_name]
    encoded_q = quote_plus(query)
    
    # 添加时间过滤器
    time_params = ""
    if days and engine_name == "baidu":
        td_map = {1: "h", 7: "w", 30: "m"}
        td = td_map.get(days, "y")
        time_params = f"&gqdr={td}"
    elif days and engine_name == "bing":
        td_map = {1: "d", 7: "w", 30: "m", 365: "y"}
        td = td_map.get(days, "y")
        time_params = f"&fd={td}"
    
    url = url_template.format(q=encoded_q) + time_params
    
    print(f"[TIER-2] 搜索引擎: {engine_name} → {url[:80]}...", file=sys.stderr)
    
    # 使用真实浏览器 UA 避免被拦截
    UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ACCEPT = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    cmd = f'curl -s --max-time 15 -L -A "{UA}" -H "Accept: {ACCEPT}" -H "Accept-Language: en-US,en;q=0.9" "{url}"'
    out, err, code = run_cmd(cmd, timeout=20)
    
    if code == 0 and out and len(out) > 500:
        links = extract_links_from_html(out, engine_name)
        print(f"[TIER-2] {engine_name} 返回 {len(links)} 条结果", file=sys.stderr)
        return links
    else:
        print(f"[TIER-2] {engine_name} 失败: {'被拦截/无响应' if not out else err[:80]}", file=sys.stderr)
        return []


def tavily_search(query, deep=False, topic="general", max_results=8):
    """使用 Tavily AI 搜索（多Key自动轮换）"""
    
    # 收集所有可用Key
    keys = []
    for i in [1, 2, 3]:
        k = os.environ.get(f"TAVILY_API_KEY_{i}")
        if k:
            keys.append((i, k))
    
    if not keys:
        print("[TIER-1] 无 TAVILY_API_KEY，跳过 Tavily", file=sys.stderr)
        return []
    
    # 读取当前Key索引
    idx = int(os.environ.get("TAVILY_KEY_INDEX", "1"))
    
    # 按优先级尝试（当前Key → 后续Key → 兜底Key）
    tried_keys = []
    for offset in range(len(keys)):
        key_idx = ((idx - 1 + offset) % len(keys)) + 1
        key_pair = next(((i, k) for i, k in keys if i == key_idx), None)
        if not key_pair or key_idx in tried_keys:
            continue
        tried_keys.append(key_idx)
        key_num, api_key = key_pair
        
        print(f"[TIER-1] Tavily 尝试 Key-{key_num}: {query} {'(deep模式)' if deep else ''}", file=sys.stderr)
        
        # 直接用 Python request 调用 Tavily（绕过 Node 脚本的 Key 固定问题）
        data = json.dumps({
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced" if deep else "basic",
            "topic": topic,
            "max_results": max_results
        }).encode()
        
        req = Request(
            "https://api.tavily.com/search",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        
        try:
            with urlopen(req, timeout=30) as resp:
                result_data = json.loads(resp.read())
            
            results = []
            for item in result_data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:300],
                    "source": f"tavily-key{key_num}",
                    "engine": "tavily"
                })
            
            if results:
                # 更新成功使用的Key索引
                if key_num != idx:
                    update_key_index(key_num)
                print(f"[TIER-1] Key-{key_num} 成功，返回 {len(results)} 条结果", file=sys.stderr)
                return results
            
        except Exception as e:
            err_str = str(e)
            if "432" in err_str or "exceeds" in err_str or "limit" in err_str.lower():
                print(f"[TIER-1] Key-{key_num} 限额超限，尝试下一个Key...", file=sys.stderr)
                # 标记当前Key为不可用
                if key_num == idx:
                    next_idx = ((idx % len(keys)) + 1)
                    update_key_index(next_idx)
                continue
            else:
                print(f"[TIER-1] Key-{key_num} 失败: {err_str[:80]}", file=sys.stderr)
                continue
    
    print("[TIER-1] 所有Tavily Key均失败，跳过", file=sys.stderr)
    return []


def update_key_index(new_idx):
    """持久化Key索引到env文件"""
    env_path = os.path.expanduser("~/.openclaw/env")
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("TAVILY_KEY_INDEX="):
                    f.write(f"TAVILY_KEY_INDEX={new_idx}  # 自动更新\n")
                else:
                    f.write(line)
    except Exception as e:
        print(f"[WARN] 无法更新Key索引: {e}", file=sys.stderr)
        print(f"[TIER-1] Tavily 返回 {len(results)} 条结果", file=sys.stderr)
        return results
    else:
        print(f"[TIER-1] Tavily 失败: {err[:100]}", file=sys.stderr)
        return []


# ============ 分层搜索主逻辑 ============

def tier0_url_fetch(url, options):
    """Tier 0: 已知URL抓取（Jina四级降级）"""
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[TIER-0] URL抓取: {url}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    content, src, tier = smart_fetch_fallback(url)
    
    if content:
        print(f"[TIER-0] ✅ 抓取成功 (source: {src}, length: {len(content)})", file=sys.stderr)
        return {
            "tier": 0,
            "source": src,
            "url": url,
            "title": extract_title(content) or url,
            "content": content[:3000],
            "confidence": "🟢",  # 直接URL来源，可信度高
            "type": "content"
        }
    else:
        print(f"[TIER-0] ❌ 抓取失败，降级至 baoyu-url-to-markdown", file=sys.stderr)
        # 尝试 Chrome CDP
        return tier4_playwright_scrape(url, options)


def tier1_tavily(query, options):
    """Tier 1: Tavily AI 搜索（最高质量）"""
    if options.get("skip_tier1"):
        print("[TIER-1] 跳过 Tavily（无API Key）", file=sys.stderr)
        return []
    
    results = tavily_search(
        query,
        deep=options.get("deep", False),
        topic=options.get("topic", "general"),
        max_results=options.get("max_results", 10)
    )
    return results


def tier2_multi_engine(query, options):
    """Tier 2: agent-reach 平台专项智能路由
    
    根据查询内容自动识别平台类型，调用对应的免费 API：
    - Reddit → Reddit JSON API（无需 Key）
    - GitHub → GitHub REST API（无需 Key）
    - V2EX → V2EX 公开 API（无需 Key）
    - RSS → feedparser
    - YouTube/B站 → yt-dlp
    - 微信公众号 → miku_ai / Jina Reader
    - 通用 → agent-reach Exa（需 mcporter，未装则跳过）
    
    ⚠️ 完全免费，0 API 成本，无 CAPTCHA
    """
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[TIER-2] agent-reach 智能路由: {query}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    max_results = options.get("max_results", 10)
    results = []
    
    # ── Reddit ────────────────────────────────────────────────
    if "reddit" in query.lower() or any(k in query for k in ["reddit", "r/", "r/"]):
        print(f"[TIER-2] 路由 → Reddit JSON API", file=sys.stderr)
        results = tier2_reddit(query, max_results)
    
    # ── GitHub ────────────────────────────────────────────────
    elif any(k in query.lower() for k in ["github", "repo", "github.com", "star", "fork"]):
        print(f"[TIER-2] 路由 → GitHub REST API", file=sys.stderr)
        results = tier2_github(query, max_results)
    
    # ── V2EX ─────────────────────────────────────────────────
    elif "v2ex" in query.lower() or any(k in query for k in ["v2ex", "V2EX"]):
        print(f"[TIER-2] 路由 → V2EX 公开 API", file=sys.stderr)
        results = tier2_v2ex(query, max_results)
    
    # ── RSS 订阅源 ────────────────────────────────────────────
    elif query.lower().startswith("rss:") or "feed" in query.lower():
        feed_url = query.replace("rss:", "").strip()
        print(f"[TIER-2] 路由 → RSS ({feed_url})", file=sys.stderr)
        results = tier2_rss(feed_url or "https://hnrss.org/frontpage", max_results)
    
    # ── YouTube / B站 ─────────────────────────────────────────
    elif any(k in query.lower() for k in ["youtube", "b站", "bilibili", "b站视频"]):
        print(f"[TIER-2] 路由 → yt-dlp 视频", file=sys.stderr)
        results = tier2_video(query, max_results)
    
    # ── 微信公众号 ────────────────────────────────────────────
    elif any(k in query for k in ["公众号", "微信文章", "微信", "mp.weixin"]):
        print(f"[TIER-2] 路由 → 微信公众号", file=sys.stderr)
        results = tier2_wechat(query, max_results)
    
    # ── 播客 ─────────────────────────────────────────────────
    elif any(k in query.lower() for k in ["播客", "podcast", "小宇宙", "xiaoyuzhou"]):
        print(f"[TIER-2] 路由 → 播客（需配置Groq Key）", file=sys.stderr)
        results = [{"title": "播客功能需配置 Groq API Key", "url": "", "content": "运行: agent-reach configure groq-key YOUR_KEY", "source": "agent-reach", "engine": "agent-reach", "confidence": "⚪"}]
    
    # ── 通用 → agent-reach Exa（若可用）─────────────────────
    else:
        results = tier2_agent_reach(query, max_results)
    
    if results:
        print(f"[TIER-2] agent-reach 返回 {len(results)} 条结果", file=sys.stderr)
    else:
        print(f"[TIER-2] agent-reach 全渠道无结果，降级 Tier 3", file=sys.stderr)
    
    return results


def tier2_reddit(query, max_results):
    """Reddit 搜索 via JSON API"""
    q = quote_plus(query.replace("reddit", "").replace("r/", "").strip())
    url = f"https://www.reddit.com/search.json?q={q}&limit={max_results}&sort=relevance"
    cmd = f'curl -s --max-time 15 -H "User-Agent: zirflow-search/1.0" "{url}"'
    out, err, code = run_cmd(cmd, timeout=20)
    if code != 0 or not out:
        return []
    try:
        data = json.loads(out)
        results = []
        for c in data.get("data", {}).get("children", [])[:max_results]:
            d = c["data"]
            results.append({
                "title": d.get("title", "")[:100],
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "content": d.get("selftext", "")[:300] or d.get("link_title", ""),
                "source": f"reddit/{d.get('subreddit', '')}",
                "engine": "agent-reach-reddit",
                "confidence": "🟢"
            })
        return results
    except Exception as e:
        print(f"[TIER-2] Reddit 解析失败: {e}", file=sys.stderr)
        return []


def tier2_github(query, max_results):
    """GitHub 搜索 via REST API"""
    q = quote_plus(query.replace("github", "").replace("github.com", "").strip())
    url = f"https://api.github.com/search/repositories?q={q}&sort=stars&per_page={max_results}"
    cmd = f'curl -s --max-time 15 -H "Accept: application/vnd.github.v3+json" "{url}"'
    out, err, code = run_cmd(cmd, timeout=20)
    if code != 0 or not out:
        return []
    try:
        data = json.loads(out)
        results = []
        for r in data.get("items", [])[:max_results]:
            results.append({
                "title": f"★{r['stargazers_count']:,} {r['full_name']}",
                "url": r.get("html_url", ""),
                "content": r.get("description", "")[:300] or "",
                "source": "github-rest-api",
                "engine": "agent-reach-github",
                "confidence": "🟢"
            })
        return results
    except Exception as e:
        print(f"[TIER-2] GitHub 解析失败: {e}", file=sys.stderr)
        return []


def tier2_v2ex(query, max_results):
    """V2EX 热门主题 via 公开 API"""
    # 提取关键词（去掉v2ex）
    q = query.replace("v2ex", "").replace("V2EX", "").replace("V2ex", "").strip()
    url = "https://www.v2ex.com/api/topics/hot.json" if not q else f"https://www.v2ex.com/api/topics/hot.json"
    cmd = f'curl -s --max-time 15 -H "User-Agent: zirflow-search/1.0" "{url}"'
    out, err, code = run_cmd(cmd, timeout=20)
    if code != 0 or not out:
        return []
    try:
        data = json.loads(out)
        results = []
        for t in data[:max_results]:
            results.append({
                "title": f"[{t.get('node',{}).get('title','')}] {t.get('title','')}",
                "url": f"https://www.v2ex.com/t/{t.get('id','')}",
                "content": t.get("content", "")[:300],
                "source": "v2ex-api",
                "engine": "agent-reach-v2ex",
                "confidence": "🟢"
            })
        return results
    except Exception as e:
        print(f"[TIER-2] V2EX 解析失败: {e}", file=sys.stderr)
        return []


def tier2_rss(feed_url, max_results):
    """RSS 订阅源"""
    cmd = f'python3 -c "import feedparser; [print(e.get(\'title\',\'\'),\'|\',e.get(\'link\',\'\')) for e in feedparser.parse(\'{feed_url}\').entries[:{max_results}]]" 2>/dev/null'
    out, err, code = run_cmd(cmd, timeout=15)
    if code != 0 or not out:
        return []
    results = []
    for line in out.strip().split("\n"):
        if "|" in line:
            parts = line.split("|", 1)
            title = parts[0].strip()
            url = parts[1].strip() if len(parts) > 1 else ""
            if title:
                results.append({
                    "title": title[:100],
                    "url": url,
                    "content": "",
                    "source": f"rss/{feed_url[:30]}",
                    "engine": "agent-reach-rss",
                    "confidence": "🟢"
                })
    return results


def tier2_video(query, max_results):
    """YouTube/B站 视频搜索"""
    # YouTube 搜索
    if "youtube" in query.lower():
        q = quote_plus(query.replace("youtube", "").replace("视频", "").strip())
        url = f"https://www.youtube.com/results?search_query={q}"
        content, src, _ = smart_fetch_fallback(url, timeout=15)
        if content and len(content) > 200:
            # 简单提取标题
            titles = re.findall(r'"title":"([^"]{10,100})"', content)
            results = []
            for t in titles[:max_results]:
                results.append({
                    "title": t,
                    "url": f"https://www.youtube.com/results?search_query={q}",
                    "content": f"YouTube 搜索: {query}",
                    "source": "youtube-search",
                    "engine": "agent-reach-youtube",
                    "confidence": "🟡"
                })
            return results
    # B站搜索
    elif "b站" in query.lower() or "bilibili" in query.lower():
        q = quote_plus(query.replace("b站", "").replace("bilibili", "").replace("B站", "").strip())
        url = f"https://api.bilibili.com/v1/search/main?keyword={q}&page=1&pagesize={max_results}"
        cmd = f'curl -s --max-time 15 "{url}"'
        out, err, code = run_cmd(cmd, timeout=20)
        if code == 0 and out:
            try:
                data = json.loads(out)
                results = []
                for v in data.get("data", {}).get("video", [])[:max_results]:
                    results.append({
                        "title": f"[B站] {v.get('title','')} ★{v.get('play',0)}",
                        "url": f"https://www.bilibili.com/video/{v.get('bvid','')}",
                        "content": f"作者:{v.get('author','')} 播放:{v.get('play',0)}",
                        "source": "bilibili-api",
                        "engine": "agent-reach-bilibili",
                        "confidence": "🟢"
                    })
                return results
            except:
                pass
    return []


def tier2_wechat(query, max_results):
    """微信公众号文章搜索"""
    q = query.replace("公众号", "").replace("微信文章", "").replace("微信", "").replace("mp.weixin", "").strip()
    # 尝试 miku_ai（微信公众号搜索）
    try:
        cmd = f'python3 -c "import asyncio; from miku_ai import get_wexin_article; asyncio.run(get_wexin_article(\'{q}\', {max_results}))" 2>/dev/null'
        out, err, code = run_cmd(cmd, timeout=20)
        if code == 0 and out.strip():
            results = []
            for line in out.strip().split("\n"):
                if "|" in line:
                    parts = line.split("|", 1)
                    title = parts[0].strip()
                    url = parts[1].strip() if len(parts) > 1 else ""
                    if title:
                        results.append({
                            "title": f"[微信] {title}",
                            "url": url,
                            "content": "",
                            "source": "miku-ai",
                            "engine": "agent-reach-wechat",
                            "confidence": "🟢"
                        })
            if results:
                return results
    except:
        pass
    # 兜底：用搜索引擎方式搜索
    return []


def tier2_agent_reach(query, max_results):
    """通用平台路由 → 尝试各种免费渠道"""
    results = []
    
    # 1. Reddit（通用关键词搜索，捕捉社区讨论）
    reddit_results = tier2_reddit(query, max_results)
    if reddit_results:
        results.extend(reddit_results[:3])
    
    # 2. GitHub（捕捉相关开源项目）
    if not any(k in query.lower() for k in ["怎么", "如何", "为什么", "what is", "how to"]):
        gh_results = tier2_github(query, max_results)
        if gh_results:
            results.extend(gh_results[:3])
    
    # 3. V2EX（捕捉中文社区讨论）
    if is_chinese(query):
        v2ex_results = tier2_v2ex(query, max_results)
        if v2ex_results:
            results.extend(v2ex_results[:3])
    
    # 去重（按URL）
    seen = set()
    unique = []
    for r in results:
        key = r["url"].split("?")[0][:80]
        if key not in seen and r["url"]:
            seen.add(key)
            unique.append(r)
    
    return unique[:max_results]


def tier3_vertical(query, options):
    """Tier 3: 垂直平台搜索（GitHub/X/金融）"""
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[TIER-3] 垂直平台: {query}", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    results = []
    
    # GitHub 相关 → 直接用 GitHub API
    if any(k in query.lower() for k in ["github", "开源项目", "开源", "github repo"]):
        print("[TIER-3] → GitHub REST API", file=sys.stderr)
        gh_results = tier2_github(query, options.get("max_results", 5))
        for r in gh_results:
            r["engine"] = "github-api"
            r["source"] = "github-rest-api"
        results.extend(gh_results)
    
    # 检测是否X/Twitter相关
    if any(k in query.lower() for k in ["twitter", "x.com", "tweet", "推特"]):
        print("[TIER-3] X/Twitter专项 → 请使用 baoyu-danger-x-to-markdown", file=sys.stderr)
    
    return results


def tier4_playwright_scrape(url_or_query, options):
    """Tier 4: Playwright 浏览器兜底（最后手段）"""
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"[TIER-4] Playwright 浏览器兜底: {url_or_query}", file=sys.stderr)
    print(f"[TIER-4] ⚠️ 注意：这是最后手段，CAPTCHA风险高", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    
    # 注意：Playwright Tier 4 需要 playwright 技能配合
    # 这里只是尝试基础抓取，完整能力参考 playwright skill
    try:
        import subprocess
        # 尝试用 node 执行 playwright 基础脚本
        script = '''
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('%s', { timeout: 30000 });
  const text = await page.textContent('body');
  console.log(text.slice(0, 3000));
  await browser.close();
})().catch(e => { console.error('PLAYWRIGHT_ERROR:', e.message); process.exit(1); });
''' % url_or_query
        
        # 简化：直接用curl尝试，不启动完整浏览器
        print("[TIER-4] 浏览器未安装或不可用，跳过Playwright", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[TIER-4] Playwright 出错: {e}", file=sys.stderr)
        return []


def is_chinese(text):
    """简单检测是否包含中文"""
    return bool(re.search(r'[\u4e00-\u9fff]', text))


def extract_title(content):
    """从Markdown/content中提取标题"""
    if not content:
        return None
    lines = content.strip().split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line.startswith('#'):
            return line.lstrip('#').strip()
        if line and len(line) < 100 and not line.startswith('http'):
            return line
    return None


def format_output(results, tier, query):
    """格式化输出"""
    output_lines = []
    
    if not results:
        return f"⚠️ 在 Tier-{tier} 未找到结果，请尝试其他查询或更大时间范围。"
    
    output_lines.append(f"\n{'='*60}")
    output_lines.append(f"📡 Zirflow Search | TIER-{tier} | 查询: {query}")
    output_lines.append(f"{'='*60}\n")
    
    if tier == 0:
        # URL抓取结果（results 是包含单个 dict 的 list）
        r = results[0] if results else {}
        output_lines.append(f"🟢 可信度: {r.get('confidence', '🟢')} | 来源: {r.get('source', 'unknown')}")
        output_lines.append(f"📄 标题: {r.get('title', 'N/A')}")
        output_lines.append(f"🔗 URL: {r.get('url', 'N/A')}")
        output_lines.append(f"\n内容预览:")
        output_lines.append(f"{'─'*40}")
        output_lines.append(r.get('content', '')[:1500])
        output_lines.append(f"{'─'*40}")
    
    else:
        # 搜索结果列表
        for i, r in enumerate(results, 1):
            title = r.get('title', 'N/A')[:80]
            url = r.get('url', '')
            content = r.get('content', r.get('snippet', ''))[:200]
            engine = r.get('engine', 'unknown')
            source = r.get('source', engine)
            
            confidence = r.get('confidence', '🟡')
            
            output_lines.append(f"{i}. {title}")
            output_lines.append(f"   🟢 可信度: {confidence} | 来源: {source}")
            if content:
                output_lines.append(f"   📝 {content}...")
            if url:
                output_lines.append(f"   🔗 {url}")
            output_lines.append("")
    
    return "\n".join(output_lines)


# ============ 主程序 ============

def main():
    parser = argparse.ArgumentParser(description="Zirflow 统一分层搜索")
    parser.add_argument("query", nargs="?", help="搜索词或URL")
    parser.add_argument("--fetch-url", action="store_true", help="强制当作URL抓取（Tier 0）")
    parser.add_argument("--tier", type=int, default=None, help="指定起始层级 (0-4)")
    parser.add_argument("--engine", default=None, help="强制平台路由 (reddit/github/v2ex/rss/wechat)")
    parser.add_argument("--days", type=int, default=7, help="时间范围（天），默认7")
    parser.add_argument("--max", type=int, dest="max_results", default=10, help="最大结果数")
    parser.add_argument("--deep", action="store_true", help="使用 Tavily deep 模式")
    parser.add_argument("--topic", default="general", choices=["general", "news"], help="Tavily 话题")
    parser.add_argument("--lang", default="auto", choices=["auto", "cn", "en"], help="语言偏好")
    parser.add_argument("--output", choices=["text", "json"], default="text", help="输出格式")
    parser.add_argument("--no-tier1", action="store_true", dest="skip_tier1", help="跳过 Tier 1 (Tavily)")
    parser.add_argument("--all", action="store_true", help="联动搜索：所有Tier同时搜，结果合并去重")
    
    args = parser.parse_args()
    
    if not args.query:
        print("用法: search.py <查询词或URL> [选项]")
        print("示例: search.py 'AI Agent 最新动态'")
        print("     search.py 'https://example.com/article' --fetch-url")
        print("     search.py 'LLM trends' --tier 2 --lang en")
        sys.exit(0)
    
    query = args.query.strip()
    options = vars(args)
    
    results = []
    used_tier = None
    
    # ========== Tier 0: URL抓取 ==========
    if args.fetch_url or is_url(query):
        used_tier = 0
        results = tier0_url_fetch(query, options)
        if results:
            print(format_output([results] if isinstance(results, dict) else results, 0, query))
            sys.exit(0)
    
    # ========== 联动搜索：所有Tier同时搜 ==========
    if getattr(args, "all", False):
        import concurrent.futures
        print("\n" + "="*60, file=sys.stderr)
        print("🔍 联动搜索：Tier 1 + Tier 2 多平台 同时搜", file=sys.stderr)
        print("="*60 + "\n", file=sys.stderr)
        
        all_results = []
        seen_urls = set()
        max_per_tier = max(3, args.max_results // 3)
        
        def fetch_tier1():
            if not args.skip_tier1:
                return tier1_tavily(query, options)
            return []
        
        def fetch_reddit():
            return tier2_reddit(query, max_per_tier)
        
        def fetch_github():
            return tier2_github(query, max_per_tier)
        
        def fetch_v2ex():
            return tier2_v2ex(query, max_per_tier)
        
        # 并行抓所有平台
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                "Tavily AI": executor.submit(fetch_tier1),
                "Reddit": executor.submit(fetch_reddit),
                "GitHub": executor.submit(fetch_github),
                "V2EX": executor.submit(fetch_v2ex),
            }
            for name, future in futures.items():
                try:
                    results = future.result(timeout=25)
                    print(f"[联动] {name} → {len(results)} 条", file=sys.stderr)
                    for r in results:
                        url_key = r.get("url", "").split("?")[0][:80]
                        if url_key and url_key not in seen_urls:
                            seen_urls.add(url_key)
                            r["source"] = f"ALL:{name}|{r.get("source","")}"
                            all_results.append(r)
                        elif not url_key:
                            all_results.append(r)
                except Exception as e:
                    print(f"[联动] {name} → 失败: {e}", file=sys.stderr)
        
        # 去重+排序（优先可信度高）
        def sort_key(r):
            conf_order = {"🟢": 0, "🟡": 1, "🔵": 2, "⚪": 3}
            return (conf_order.get(r.get("confidence","⚪"), 4), -len(r.get("content","")))
        all_results.sort(key=sort_key)
        
        print(f"[联动] 共 {len(all_results)} 条去重后结果", file=sys.stderr)
        print(format_output(all_results[:args.max_results], 99, query))
        sys.exit(0)
    
    # ========== 自动分层决策 ==========
    if args.tier is not None:
        start_tier = args.tier
    else:
        # 自动：从 Tier 1 开始（有Tavily Key）或 Tier 2
        start_tier = 1 if os.environ.get("TAVILY_API_KEY_1") else 2
    
    # ========== Tier 1: Tavily ==========
    if start_tier <= 1 and not args.skip_tier1:
        used_tier = 1
        results = tier1_tavily(query, options)
        if results:
            print(format_output(results, 1, query))
            sys.exit(0)
    
    # ========== Tier 2: agent-reach 平台专项 ==========
    if start_tier <= 2:
        used_tier = 2
        
        # 如果指定了平台
        if args.engine:
            opts = dict(options)
            if args.engine == "reddit":
                results = tier2_reddit(query, args.max_results)
            elif args.engine == "github":
                results = tier2_github(query, args.max_results)
            elif args.engine == "v2ex":
                results = tier2_v2ex(query, args.max_results)
            elif args.engine == "rss":
                results = tier2_rss(query, args.max_results)
            elif args.engine == "wechat":
                results = tier2_wechat(query, args.max_results)
            elif args.engine == "video":
                results = tier2_video(query, args.max_results)
            else:
                results = tier2_multi_engine(query, opts)
            for r in results:
                r["confidence"] = "🟢"
            print(format_output(results, 2, query))
        else:
            results = tier2_multi_engine(query, options)
            for r in results:
                r["confidence"] = r.get("confidence", "🟢")
            print(format_output(results, 2, query))
        sys.exit(0)
    
    # ========== Tier 3: 垂直平台 ==========
    if start_tier <= 3:
        used_tier = 3
        results = tier3_vertical(query, options)
        if results:
            print(format_output(results, 3, query))
            sys.exit(0)
    
    # ========== Tier 4: 浏览器兜底 ==========
    if start_tier <= 4:
        used_tier = 4
        results = tier4_playwright_scrape(query, options)
        if results:
            print(format_output(results, 4, query))
        else:
            print(f"❌ 所有层级均未找到结果。请尝试：")
            print(f"   1. 更通用的关键词")
            print(f"   2. 更长的时间范围 (--days 30)")
            print(f"   3. 配置 TAVILY_API_KEY 提升 Tier-1 质量")
        sys.exit(1)


if __name__ == "__main__":
    main()
