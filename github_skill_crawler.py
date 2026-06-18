"""GitHub 高星 Skill 项目爬虫 — Scrapling 框架

v2.1: 添加日期过滤，只保留近期活跃项目
"""

import json
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, List, Dict

try:
    from scrapling.fetchers import Fetcher
    HAS_SCRAPLING = True
except ImportError:
    HAS_SCRAPLING = False
    print("⚠️  Scrapling 未安装，使用备用方案")

STORE_DIR = Path(__file__).parent / "skill_store"
RAW_DATA_FILE = STORE_DIR / "github_raw.json"
SEARCH_URL = "https://github.com/search"
QUERIES = ["claude+code+skill", "claude+code+agent", "claude+skill+md", "ai+coding+agent+skill"]
MIN_STARS = 10
MAX_PAGES = 3
DELAY = 2.0
MAX_AGE_DAYS = 90  # 只保留最近90天内更新的项目


def parse_stars(text: str) -> int:
    """'1.2k' -> 1200"""
    if not text:
        return 0
    m = re.match(r"([\d.]+)\s*([km])?", text.strip().lower().replace(",", ""))
    if not m:
        return 0
    n = float(m.group(1))
    return int(n * {"k": 1000, "m": 1_000_000}.get(m.group(2), 1))


def is_recent(last_updated: str, max_days: int = MAX_AGE_DAYS) -> bool:
    """检查项目是否在 max_days 内更新过"""
    if not last_updated:
        return False
    try:
        dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_days)
        return dt >= cutoff
    except (ValueError, TypeError):
        return False


def get_system_time() -> datetime:
    """获取系统当前时间（UTC）"""
    return datetime.now(timezone.utc)


def _is_recent(date_str: str, max_age_days: int = MAX_AGE_DAYS) -> bool:
    """检查日期是否在 max_age_days 天内"""
    if not date_str:
        return True  # 无日期信息的项目放行
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt >= datetime.now(timezone.utc) - timedelta(days=max_age_days)
    except (ValueError, TypeError):
        return True  # 解析失败的放行


def extract_card(card, query: str) -> Optional[Dict]:
    """从搜索卡片提取仓库信息"""
    links = card.css("a[data-testid='results-list']") or card.css("a")
    if not links:
        return None

    repo_link = next(
        (el for el in links if el.attrib.get("href", "").count("/") == 2),
        links[0],
    )
    href = repo_link.attrib.get("href", "").strip("/")
    if not href or href.count("/") != 1:
        return None

    desc = card.css('[data-testid="results-list"] + p') or card.css("p")
    star_el = card.css('[href*="/stargazers"]') or card.css('[aria-label*="star"]')
    lang_el = card.css('[itemprop="programmingLanguage"]')
    time_el = card.css("relative-time")

    last_updated = time_el[0].attrib.get("datetime", "") if time_el else ""

    return {
        "name": href,
        "url": f"https://github.com/{href}",
        "description": desc[0].text.strip() if desc else "",
        "stars": parse_stars(star_el[0].text if star_el else "0"),
        "language": lang_el[0].text.strip() if lang_el else "",
        "topics": [],
        "last_updated": last_updated,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "source_query": query,
    }


def crawl_page(query: str, page: int = 1) -> List[Dict]:
    """爬取单页"""
    url = f"{SEARCH_URL}?q={query}&type=repositories&s=stars&o=desc&p={page}"
    try:
        resp = Fetcher.get(url, stealthy_headers=True)
        cards = resp.css('[data-testid="results-list"]') or resp.css(".Box-row") or resp.css("article")
        return [info for card in cards if (info := extract_card(card, query)) and info["stars"] >= MIN_STARS]
    except Exception as e:
        print(f"[爬虫] 失败: {url} — {e}")
        return []


def run_crawler() -> List[Dict]:
    """完整爬取流程 — 每次都重新爬取，过滤过旧项目"""
    now = get_system_time()
    print(f"[爬虫] 开始抓取 GitHub 高星 skill 项目 (系统时间: {now.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
    results, seen = [], set()
    for q in QUERIES:
        print(f"[爬虫] 搜索: {q}")
        for p in range(1, MAX_PAGES + 1):
            for item in crawl_page(q, p):
                if item["url"] not in seen:
                    seen.add(item["url"])
                    # 日期过滤：只保留近期活跃项目
                    if is_recent(item.get("last_updated", "")):
                        results.append(item)
                    else:
                        print(f"[爬虫] 跳过旧项目: {item['name']} (最后更新: {item.get('last_updated', 'N/A')})")
            time.sleep(DELAY)

    results.sort(key=lambda x: x["stars"], reverse=True)
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    # 完全替换缓存文件（不合并旧数据）
    RAW_DATA_FILE.write_text(json.dumps({
        "crawled_at": now.isoformat(),
        "total": len(results),
        "projects": results,
    }, ensure_ascii=False, indent=2))
    print(f"[爬虫] 完成: {len(results)} 个项目 (过滤了 {len(seen) - len(results)} 个过旧项目)")
    return results


def check_data_freshness() -> Dict:
    """检查缓存数据的新鲜度"""
    if not RAW_DATA_FILE.exists():
        return {"status": "no_data", "message": "无缓存数据，需要爬取"}

    data = json.loads(RAW_DATA_FILE.read_text())
    crawled_at = data.get("crawled_at", "")

    if not crawled_at:
        return {"status": "invalid", "message": "缓存数据无时间戳"}

    try:
        crawl_time = datetime.fromisoformat(crawled_at.replace("Z", "+00:00"))
        if crawl_time.tzinfo is None:
            crawl_time = crawl_time.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_hours = (now - crawl_time).total_seconds() / 3600

        if age_hours > 24:
            return {
                "status": "stale",
                "message": f"数据已过期 {age_hours:.1f} 小时，建议重新爬取",
                "crawled_at": crawled_at,
                "age_hours": round(age_hours, 1),
            }
        else:
            return {
                "status": "fresh",
                "message": f"数据新鲜 ( {age_hours:.1f} 小时前爬取)",
                "crawled_at": crawled_at,
                "age_hours": round(age_hours, 1),
            }
    except (ValueError, TypeError):
        return {"status": "error", "message": f"无法解析爬取时间: {crawled_at}"}


if __name__ == "__main__":
    run_crawler()
