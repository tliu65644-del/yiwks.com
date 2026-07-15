#!/usr/bin/env python3
"""Insert Baidu Tongji analytics and Baidu site-verification meta into all HTML pages."""

import argparse
import re
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent


def make_baidu_script(stats_id: str) -> str:
    return (
        '<script>\n'
        'var _hmt = _hmt || [];\n'
        '(function() {\n'
        '  var hm = document.createElement("script");\n'
        f'  hm.src = "https://hm.baidu.com/hm.js?{stats_id}";\n'
        '  var s = document.getElementsByTagName("script")[0];\n'
        '  s.parentNode.insertBefore(hm, s);\n'
        '})();\n'
        '</script>\n'
    )


def iter_html_pages():
    """Yield all HTML files under SITE_DIR, excluding node_modules and hidden dirs."""
    for p in sorted(SITE_DIR.rglob("*.html")):
        # skip hidden dirs and common build dirs
        parts = {x.lower() for x in p.relative_to(SITE_DIR).parts}
        if parts & {"node_modules", ".git", ".venv", "venv", "__pycache__"}:
            continue
        if any(part.startswith(".") for part in p.parts):
            continue
        yield p.relative_to(SITE_DIR)


def normalize_head_tag(html: str) -> str:
    """Ensure <head> is on its own line for easy insertion."""
    # collapse whitespace around <head> to a single newline
    html = re.sub(r"\s*<head>\s*", "\n<head>\n", html, count=1, flags=re.IGNORECASE)
    return html


def insert_code(stats_id: str, verify_tag: str = ""):
    script = make_baidu_script(stats_id)
    for rel in iter_html_pages():
        p = SITE_DIR / rel
        html = p.read_text(encoding="utf-8")

        # Avoid duplicate Baidu stats
        if "hm.baidu.com/hm.js" in html:
            print(f"[SKIP] {rel} already has Baidu stats")
            continue

        html = normalize_head_tag(html)

        # Insert verify tag right after <head> (only if provided and not present)
        if verify_tag and verify_tag.strip() not in html:
            html = html.replace("<head>", "<head>\n" + verify_tag.strip(), 1)

        # Insert stats script before </head>
        if "</head>" in html:
            html = html.replace("</head>", script + "</head>", 1)
        else:
            # fallback: prepend before </body> if </head> missing
            if "</body>" in html:
                html = html.replace("</body>", script + "</body>", 1)
            else:
                html = html + "\n" + script

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
