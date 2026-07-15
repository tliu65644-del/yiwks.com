#!/usr/bin/env python3
"""Generate RSS/Atom feed for yiwks.com blog articles."""

import re
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

SITE_DIR = Path(__file__).resolve().parent.parent
BLOG_DIR = SITE_DIR / "blog"
SITE_URL = "https://yiwks.com"
FEED_PATH = SITE_DIR / "feed.xml"


def extract_meta(html: str, name: str) -> str:
    """Extract content of a <meta name=...> tag."""
    pattern = rf'<meta\s+name=["\']{re.escape(name)}["\']\s+content=["\']([^"\']+)["\']'
    m = re.search(pattern, html, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # try reversed attribute order
    pattern2 = rf'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']{re.escape(name)}["\']'
    m2 = re.search(pattern2, html, re.IGNORECASE)
    return m2.group(1).strip() if m2 else ""


def extract_title(html: str) -> str:
    m = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    return m.group(1).strip() if m else "无标题"


def parse_date_from_slug(slug: str, mtime: float) -> datetime:
    """Try to extract YYYY-MM-DD from slug like 2026-07-15-xxx, fallback to file mtime."""
    m = re.match(r"(\d{4}-\d{2}-\d{2})", slug)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def iter_articles():
    if not BLOG_DIR.exists():
        return
    for post_dir in sorted(BLOG_DIR.iterdir()):
        if not post_dir.is_dir():
            continue
        if post_dir.name == "index.html" or post_dir.name.startswith("."):
            continue
        html_path = post_dir / "index.html"
        if not html_path.exists():
            continue
        html = html_path.read_text(encoding="utf-8")
        title = extract_title(html)
        description = extract_meta(html, "description") or title
        mtime = html_path.stat().st_mtime
        pub_date = parse_date_from_slug(post_dir.name, mtime)
        url = f"{SITE_URL}/blog/{post_dir.name}/"
        yield {
            "title": title,
            "description": description,
            "url": url,
            "pub_date": pub_date,
        }


def format_rfc2821(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def generate_feed():
    articles = sorted(iter_articles(), key=lambda x: x["pub_date"], reverse=True)
    now = datetime.now(timezone.utc)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
        "<channel>",
        f"  <title>{escape('金钥匙开锁店 - 义乌锁具知识博客')}</title>",
        f"  <link>{SITE_URL}/blog/</link>",
        "  <description>义乌金钥匙开锁店每日锁具知识科普：开锁、换锁芯、汽车钥匙、指纹锁、门禁电梯卡等实用指南。</description>",
        f"  <lastBuildDate>{format_rfc2821(now)}</lastBuildDate>",
        f"  <atom:link href=\"{SITE_URL}/feed.xml\" rel=\"self\" type=\"application/rss+xml\" />",
        "  <language>zh-CN</language>",
    ]

    for art in articles:
        lines.append("  <item>")
        lines.append(f"    <title>{escape(art['title'])}</title>")
        lines.append(f"    <link>{art['url']}</link>")
        lines.append(f"    <guid isPermaLink=\"true\">{art['url']}</guid>")
        lines.append(f"    <pubDate>{format_rfc2821(art['pub_date'])}</pubDate>")
        lines.append(f"    <description>{escape(art['description'])}</description>")
        lines.append("  </item>")

    lines.extend(["</channel>", "</rss>"])
    FEED_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] Generated {FEED_PATH} with {len(articles)} articles")


if __name__ == "__main__":
    generate_feed()
