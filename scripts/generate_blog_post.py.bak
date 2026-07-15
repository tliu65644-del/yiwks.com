#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金钥匙开锁店·每日锁具科普文章自动生成器

用法：
    python3 scripts/generate_blog_post.py

功能：
1. 随机选取主题，调用 Kimi API 生成一篇 800-1200 字的义乌本地锁具科普文章
2. 输出为 /blog/YYYY-MM-DD-主题slug/index.html
3. 更新 /blog/index.html 列表（在最上方插入新文章卡片）
4. 更新 sitemap.xml
5. 可选：自动 git commit + push

环境变量：
    KIMI_API_KEY  必填，Kimi 官方 API Key
"""

import os
import re
import json
import random
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path

# 配置
SITE_DIR = Path(__file__).resolve().parent.parent
BLOG_DIR = SITE_DIR / "blog"
SITE_URL = "https://yiwks.com"
API_KEY = os.environ.get("KIMI_API_KEY", "")
API_URL = "https://api.moonshot.cn/v1/chat/completions"
MODEL = "kimi-k2.7-code-highspeed"

# 文章主题库（可扩展）
TOPICS = [
    {
        "title": "义乌防盗门开锁要多少钱？价格怎么算的？",
        "slug": "yiwu-door-unlock-price",
        "category": "开锁常识",
        "keywords": "义乌防盗门开锁,义乌开锁多少钱,义乌开锁价格,防盗门开锁费用",
        "desc": "义乌防盗门开锁价格由上门费、技术开锁费、时间段决定。本文详细说明义乌市场行情，教你避开乱报价。",
    },
    {
        "title": "A级、B级、C级、D级锁芯到底什么区别？",
        "slug": "lock-cylinder-level-guide",
        "category": "换锁芯",
        "keywords": "锁芯级别,A级锁芯,B级锁芯,C级锁芯,D级锁芯,超C级锁芯,超D级锁芯",
        "desc": "锁芯级别直接决定家庭安全。本文用通俗语言讲清A、B、C、D级锁芯的防技术原理和选购建议。",
    },
    {
        "title": "义乌指纹锁哪个牌子好？凯迪仕、德施曼、小米怎么选？",
        "slug": "yiwu-fingerprint-lock-brand-compare",
        "category": "指纹锁",
        "keywords": "义乌指纹锁,凯迪仕指纹锁,德施曼指纹锁,小米智能锁,指纹锁品牌推荐",
        "desc": "义乌市面上常见指纹锁品牌对比：凯迪仕、德施曼、小米、鹿客、华为智选。从价格、功能、售后、适配性出发给出实用建议。",
    },
    {
        "title": "汽车钥匙被锁车里了怎么办？义乌开锁师傅能开车门吗？",
        "slug": "car-key-locked-inside-yiwu",
        "category": "汽车钥匙",
        "keywords": "汽车钥匙锁车里,义乌汽车开锁,汽车门开锁,钥匙锁车里怎么办",
        "desc": "钥匙被锁车内、孩子在车上、急着出门？本文讲解义乌汽车开锁的正确做法、注意事项和大概费用。",
    },
    {
        "title": "义乌门禁卡复制多少钱？物业和开锁店哪个划算？",
        "slug": "yiwu-access-card-copy-price",
        "category": "门禁电梯卡",
        "keywords": "义乌门禁卡复制,义乌电梯卡复制,门禁卡复制多少钱,电梯卡复制多少钱",
        "desc": "门禁卡丢了怎么办？物业补办收费高、等待久。本文对比物业补办和开锁店复制的成本、时效和合规性。",
    },
    {
        "title": "保险柜忘了密码怎么打开？义乌保险柜开锁注意什么？",
        "slug": "safe-unlock-password-forgot-yiwu",
        "category": "保险柜开锁",
        "keywords": "保险柜忘了密码,义乌保险柜开锁,保险柜开锁,电子保险柜密码重置",
        "desc": "保险柜密码忘记、钥匙丢失、电子锁没电？本文介绍义乌保险柜应急开锁流程、合规要求和常见保险柜类型处理方法。",
    },
]


def generate_article(topic: dict) -> str:
    """调用 Kimi API 生成文章正文"""
    if not API_KEY:
        raise RuntimeError("KIMI_API_KEY 环境变量未设置")

    system_prompt = (
        "你是金钥匙开锁店（义乌福田银海二区菜市场外围A-10号，电话15605799786）的本地化锁具科普作者。"
        "请用中文撰写一篇科普文章，要求："
        "1. 文章结构清晰，分小节，有标题；"
        "2. 语言通俗易懂，结合义乌本地场景；"
        "3. 内容实用，有实际建议，不要过度营销；"
        "4. 文章字数在 800 到 1200 字之间；"
        "5. 可在适当位置自然引入金钥匙开锁店的联系电话 15605799786 和地址，但不要每段都出现；"
        "6. 输出仅包含文章正文 HTML 段落（不要全站 HTML，只要 article 内的 p/h2/ul/li/div）。"
    )
    user_prompt = f"主题：{topic['title']}\n关键词：{topic['keywords']}\n摘要：{topic['desc']}\n\n请生成文章正文。"

    try:
        import requests
    except ImportError:
        raise RuntimeError("缺少 requests 依赖")

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 2500,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    # Remove markdown code fence if present
    content = re.sub(r"^```html\n?|```$", "", content, flags=re.MULTILINE).strip()
    return content


def build_post_html(topic: dict, date_str: str, body_html: str) -> str:
    """拼接单篇文章页面 HTML"""
    slug = topic["slug"]
    url = f"{SITE_URL}/blog/{date_str}-{slug}/"
    canonical = f"{SITE_URL}/blog/{date_str}-{slug}/"
    title = topic["title"]
    desc = topic["desc"]
    keywords = topic["keywords"]
    category = topic["category"]

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<title>{title} - 义乌金钥匙开锁店</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{keywords}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:type" content="article">
<meta property="og:locale" content="zh_CN">
<meta property="og:image" content="{SITE_URL}/images/store/store-front.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="675">
<link rel="icon" type="image/x-icon" href="/favicon.ico">
<link rel="icon" type="image/png" sizes="512x512" href="/favicon.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<meta name="theme-color" content="#1a1a2e">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif; color: #333; line-height: 1.8; background: #f8f8f8; }}
a {{ text-decoration: none; color: inherit; }}
img {{ max-width: 100%; height: auto; }}
.container {{ max-width: 800px; margin: 0 auto; padding: 0 16px; }}
.top-bar {{ position: fixed; top: 0; left: 0; right: 0; z-index: 1000; background: #d4262b; color: #fff; display: flex; justify-content: space-between; align-items: center; padding: 10px 16px; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }}
.top-bar .phone {{ font-size: 20px; font-weight: bold; color: #fff; }}
.top-bar .hours {{ font-size: 12px; opacity: 0.9; }}
nav {{ position: fixed; top: 48px; left: 0; right: 0; z-index: 999; background: #fff; border-bottom: 1px solid #e8e8e8; overflow-x: auto; white-space: nowrap; -webkit-overflow-scrolling: touch; }}
nav .nav-inner {{ display: flex; padding: 0 8px; }}
nav a {{ display: inline-block; padding: 12px 14px; font-size: 14px; color: #333; border-bottom: 2px solid transparent; }}
nav a:hover, nav a.active {{ color: #d4262b; border-bottom-color: #d4262b; }}
.page-banner {{ margin-top: 96px; background: linear-gradient(135deg, #1a1a2e, #0f3460); color: #fff; padding: 40px 16px; text-align: center; }}
.page-banner h1 {{ font-size: 24px; margin-bottom: 8px; line-height: 1.4; }}
.page-banner p {{ font-size: 13px; opacity: 0.9; }}
article {{ background: #fff; padding: 32px 16px; }}
article h2 {{ font-size: 20px; color: #1a1a2e; margin: 28px 0 12px; }}
article p {{ margin-bottom: 14px; font-size: 15px; color: #444; }}
article ul {{ margin: 12px 0 18px 24px; }}
article li {{ margin-bottom: 8px; font-size: 15px; color: #444; }}
article .tip {{ background: #fef2f2; border-left: 4px solid #d4262b; padding: 12px 16px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
article .tip strong {{ color: #d4262b; }}
.back {{ display: inline-block; margin-top: 20px; color: #d4262b; font-weight: bold; }}
footer {{ background: #1a1a2e; color: #fff; padding: 40px 16px 100px; }}
footer p {{ text-align: center; font-size: 12px; opacity: 0.6; }}
.bottom-bar {{ position: fixed; bottom: 0; left: 0; right: 0; z-index: 1000; background: #fff; border-top: 1px solid #e8e8e8; display: flex; }}
.bottom-bar a {{ flex: 1; text-align: center; padding: 12px 8px; font-size: 13px; color: #333; }}
.bottom-bar a.phone-btn {{ background: #d4262b; color: #fff; font-weight: bold; font-size: 18px; padding: 10px; }}
.wechat-popup {{ display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; background: rgba(0,0,0,0.6); justify-content: center; align-items: center; }}
.wechat-popup.show {{ display: flex; }}
.wechat-popup .card {{ background: #fff; padding: 24px; border-radius: 16px; text-align: center; max-width: 300px; }}
.wechat-popup .card img {{ width: 200px; height: 200px; margin-bottom: 12px; }}
.wechat-popup .card p {{ font-size: 14px; color: #333; }}
.wechat-popup .card .close {{ margin-top: 12px; padding: 8px 24px; background: #d4262b; color: #fff; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }}
@media (min-width: 768px) {{ .page-banner h1 {{ font-size: 30px; }} article {{ padding: 48px 40px; }} }}
</style>
</head>
<body>
<div class="top-bar"><span class="hours">24小时 · 福田10分钟到</span><a href="tel:15605799786" class="phone">📞 15605799786</a></div>
<nav>
  <div class="nav-inner container">
    <a href="/">首页</a>
    <a href="/services/">服务项目</a>
    <a href="/cases/">施工案例</a>
    <a href="/booking/">在线预约</a>
    <a href="/price/">参考价格</a>
    <a href="/about/">关于我们</a>
    <a href="/contact/">联系我们</a>
    <a href="/blog/" class="active">锁具知识</a>
  </div>
</nav>

<div class="page-banner">
  <div class="container">
    <h1>{title}</h1>
    <p>发布时间：{date_str} · 分类：{category}</p>
  </div>
</div>

<article class="container">
{body_html}
  <a href="/blog/" class="back">← 返回锁具知识列表</a>
</article>

<footer><div class="container"><p>© 2026 金钥匙开锁店 · yiwks.com</p></div></footer>
<div class="bottom-bar"><a href="tel:15605799786" class="phone-btn">📞 一键拨号 15605799786</a><a href="#" onclick="showWechat()">💬 微信</a><a href="/booking/">📝 预约</a></div>
<div class="wechat-popup" id="wechatPopup"><div class="card"><img src="/images/store/wechat-qr.jpg" alt="微信二维码"><p>微信：15605799786</p><button class="close" onclick="hideWechat()">关闭</button></div></div>
<script>
function showWechat(){{document.getElementById('wechatPopup').classList.add('show');return false;}}
function hideWechat(){{document.getElementById('wechatPopup').classList.remove('show');}}
document.addEventListener('DOMContentLoaded',function(){{
  var popup=document.getElementById('wechatPopup');
  if(popup){{
    popup.addEventListener('click',function(e){{if(e.target===popup)hideWechat();}});
    document.addEventListener('keydown',function(e){{if(e.key==='Escape')hideWechat();}});
  }}
}});
</script>
</body>
</html>
"""


def update_blog_index(topic: dict, date_str: str, slug: str):
    """在 blog/index.html 最上方插入新文章卡片"""
    index_path = BLOG_DIR / "index.html"
    html = index_path.read_text(encoding="utf-8")

    card = f"""    <article class="blog-card">
      <h2><a href="/blog/{date_str}-{slug}/">{topic['title']}</a></h2>
      <div class="meta">发布日期：{date_str} · 分类：{topic['category']}</div>
      <p>{topic['desc']}</p>
      <a href="/blog/{date_str}-{slug}/" class="readmore">阅读全文 →</a>
    </article>

"""
    # Insert after <div class="container"> inside blog-list section
    marker = '<section class="blog-list">\n  <div class="container">\n'
    if marker in html:
        html = html.replace(marker, marker + card)
    else:
        # fallback
        html = html.replace('<section class="blog-list">\n  <div class="container">', '<section class="blog-list">\n  <div class="container">\n' + card)
    index_path.write_text(html, encoding="utf-8")


def update_sitemap(date_str: str, slug: str):
    """更新 sitemap.xml"""
    sitemap_path = SITE_DIR / "sitemap.xml"
    html = sitemap_path.read_text(encoding="utf-8")
    entry = f"""  <url>\n    <loc>{SITE_URL}/blog/{date_str}-{slug}/</loc>\n    <lastmod>{date_str}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"""
    if f"/blog/{date_str}-{slug}/" not in html:
        html = html.replace("</urlset>", entry + "</urlset>")
        sitemap_path.write_text(html, encoding="utf-8")


def git_push(message: str):
    """自动提交并推送"""
    try:
        subprocess.run(["git", "add", "."], cwd=SITE_DIR, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=SITE_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_DIR, check=True)
        print("[OK] Git push completed")
    except subprocess.CalledProcessError as e:
        print(f"[WARN] Git operation failed: {e}")


def main():
    topic = random.choice(TOPICS)
    today = datetime.now().strftime("%Y-%m-%d")
    slug = topic["slug"]
    post_dir = BLOG_DIR / f"{today}-{slug}"
    post_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Generating article: {topic['title']}")
    body = generate_article(topic)
    post_html = build_post_html(topic, today, body)
    (post_dir / "index.html").write_text(post_html, encoding="utf-8")

    update_blog_index(topic, today, slug)
    update_sitemap(today, slug)

    print(f"[OK] Article saved to {post_dir}/index.html")

    # Auto git push
    git_push(f"blog: add {today} article - {topic['title']}")


if __name__ == "__main__":
    main()
