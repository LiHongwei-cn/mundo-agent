"""GitHub 高星 Skill 项目爬虫 — GitHub API 版

v2.2.6: 改用 GitHub REST API，不再依赖 Scrapling CSS 选择器。
GitHub 页面频繁改版导致 CSS 选择器失效，API 更稳定。
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

STORE_DIR = Path(__file__).parent / "skill_store"
RAW_DATA_FILE = STORE_DIR / "github_raw.json"
INDEX_FILE = STORE_DIR / "github_high_star_skills.json"

QUERIES = [
    "claude code skill",
    "claude code agent",
    "claude skill md",
    "ai coding agent skill",
    "cursor rules",
    "copilot instruction",
    "ai agent framework",
    "llm agent tool",
    "mcp server",
    "hermes agent",
    "prompt engineering",
    "rag framework",
    "langchain",
    "autogen",
    "crewai",
    "coding assistant",
    "code generation ai",
    "openai agent",
    "anthropic claude",
    "deepseek agent",
]

MIN_STARS = 10


def search_github(query: str, page: int = 1, per_page: int = 30) -> dict:
    url = (
        f"https://api.github.com/search/repositories"
        f"?q={urllib.parse.quote(query)}&sort=stars&order=desc"
        f"&page={page}&per_page={per_page}"
    )
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MundoAgent/2.2.6",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [爬虫] 失败: {query} — {e}")
        return {}


def run_crawler() -> List[Dict]:
    print("[爬虫] 开始抓取 GitHub 高星 skill 项目...")
    all_repos = {}

    for q in QUERIES:
        print(f"[爬虫] 搜索: {q}")
        data = search_github(q)
        if not data or "items" not in data:
            continue
        for item in data["items"]:
            full_name = item["full_name"]
            if full_name in all_repos:
                continue
            stars = item.get("stargazers_count", 0)
            if stars < MIN_STARS:
                continue
            all_repos[full_name] = {
                "name": full_name,
                "url": item["html_url"],
                "description": (item.get("description") or "")[:200],
                "stars": stars,
                "language": item.get("language") or "",
                "topics": item.get("topics", []),
                "last_updated": item.get("updated_at", ""),
                "crawled_at": datetime.now(timezone.utc).isoformat(),
                "license": (item.get("license") or {}).get("spdx_id", ""),
            }

    sorted_repos = sorted(all_repos.values(), key=lambda x: x["stars"], reverse=True)
    now = datetime.now(timezone.utc).isoformat()

    STORE_DIR.mkdir(parents=True, exist_ok=True)

    RAW_DATA_FILE.write_text(json.dumps({
        "crawled_at": now,
        "total": len(sorted_repos),
        "projects": sorted_repos,
    }, ensure_ascii=False, indent=2))

    INDEX_FILE.write_text(json.dumps({
        "metadata": {
            "version": "2.0.0",
            "last_updated": now[:10],
            "total_skills": len(sorted_repos),
            "source": "github-api",
            "queries": len(QUERIES),
        },
        "skills": sorted_repos,
    }, ensure_ascii=False, indent=2))

    print(f"[爬虫] 完成: {len(sorted_repos)} 个项目")
    return sorted_repos


if __name__ == "__main__":
    run_crawler()
