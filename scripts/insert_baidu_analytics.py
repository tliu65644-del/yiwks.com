#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键插入百度统计 + 百度站长验证代码

用法：
    python3 scripts/insert_baidu_analytics.py --stats-id 0123456789abcdef0123456789abcdef --verify-tag <meta>

参数：
    --stats-id    百度统计 hm.js 的 ID（登录 https://tongji.baidu.com 获取）
    --verify-tag  百度搜索资源平台的站点验证 meta 标签（可选）

示例：
    python3 scripts/insert_baidu_analytics.py --stats-id abcdef0123456789abcdef0123456789
"""

import argparse
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent
PAGES = [
    "index.html",
    "services/index.html",
    "cases/index.html",
    "booking/index.html",
    "price/index.html",
    "about/index.html",
    "contact/index.html",
    "privacy/index.html",
    "blog/index.html",
    "blog/why-call-police-recorded-locksmith/index.html",
    "blog/car-key-lost-cost/index.html",
    "blog/fingerprint-lock-install-tips/index.html",
    "blog/elevator-card-copy-guide/index.html",
]


def make_baidu_script(stats_id: str) -> str:
    return f"""<!-- 百度统计 -->
<script>
var _hmt = _hmt || [];
(function() {{
  var hm = document.createElement("script");
  hm.src = "https://hm.baidu.com/hm.js?{stats_id}";
  var s = document.getElementsByTagName("script")[0];
  s.parentNode.insertBefore(hm, s);
}})();
</script>
"""


def insert_code(stats_id: str, verify_tag: str = ""):
    script = make_baidu_script(stats_id)
    for rel in PAGES:
        p = SITE_DIR / rel
        if not p.exists():
            print(f"[SKIP] {rel} not found")
            continue
        html = p.read_text(encoding="utf-8")
        # Avoid duplicate insertion
        if "hm.baidu.com/hm.js" in html:
            print(f"[SKIP] {rel} already has Baidu stats")
            continue
        # Insert verify tag right after <head>
        if verify_tag and verify_tag not in html:
            html = html.replace("<head>", "<head>\n" + verify_tag, 1)
        # Insert stats script before </head>
        html = html.replace("</head>", script + "</head>", 1)
        p.write_text(html, encoding="utf-8")
        print(f"[OK] {rel}")


def main():
    parser = argparse.ArgumentParser(description="Insert Baidu Analytics and verification code")
    parser.add_argument("--stats-id", required=True, help="Baidu Tongji hm.js ID")
    parser.add_argument("--verify-tag", default="", help="Baidu site verification meta tag")
    args = parser.parse_args()
    insert_code(args.stats_id, args.verify_tag)


if __name__ == "__main__":
    main()
