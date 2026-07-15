#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""金钥匙开锁店·每日锁具科普文章自动生成器 v3

用法：
    python3 scripts/generate_blog_post.py

功能：
1. 每天从主题库中随机选取 3 个不同主题
2. 调用 Kimi API 生成 3 篇 800-1200 字的义乌本地锁具科普文章
3. 输出为 /blog/YYYY-MM-DD-主题slug/index.html
4. 更新 /blog/index.html 列表（在最上方插入新文章卡片）
5. 更新 sitemap.xml
6. 自动 git commit + push 到 Cloudflare Pages

环境变量：
    KIMI_API_KEY  必填，Kimi 官方 API Key
"""

import os
import re
import json
import random
import subprocess
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("blog_generator")

# 配置
SITE_DIR = Path(__file__).resolve().parent.parent
BLOG_DIR = SITE_DIR / "blog"
DATA_DIR = SITE_DIR / "scripts" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = DATA_DIR / "blog_history.json"
SITE_URL = "https://yiwks.com"
def _load_env_key(path: Path = Path.home() / ".hermes" / ".env") -> str:
    """从~/.hermes/.env加载KIMI_API_KEY"""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("KIMI_API_KEY="):
            value = line[len("KIMI_API_KEY="):]
            value = value.strip().strip('"').strip("'")
            return value
    return ""


API_KEY = os.environ.get("KIMI_API_KEY") or _load_env_key()
API_URL = "https://api.moonshot.cn/v1/chat/completions"
MODEL = os.environ.get("MOONSHOT_MODEL", "kimi-k2.7-code-highspeed")
ARTICLES_PER_DAY = 3

# 文章主题库（30+主题，保证长期不重复）
TOPICS = [
    {
        "title": "义乌防盗门开锁要多少钱？价格怎么算的？",
        "slug": "yiwu-door-unlock-price",
        "category": "开锁常识",
        "keywords": "义乌防盗门开锁,义乌开锁多少钱,义乌开锁价格,防盗门开锁费用",
        "desc": "义乌防盗门开锁价格由上门费、技术开锁费、时间段决定。本文详细说明义乌市场行情，教你避开乱报价。",
    },
    {
        "title": "A级、B级、C级锁芯到底什么区别？",
        "slug": "lock-cylinder-level-guide",
        "category": "换锁芯",
        "keywords": "锁芯级别,A级锁芯,B级锁芯,C级锁芯,超C级锁芯",
        "desc": "锁芯级别直接决定家庭安全。本文用通俗语言讲清A、B、C级锁芯的防技术原理和选购建议。",
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
    {
        "title": "防盗门开锁为什么要找公安备案师傅？",
        "slug": "why-call-police-recorded-locksmith",
        "category": "开锁常识",
        "keywords": "义乌公安备案开锁,防盗门开锁师傅,开锁备案,义乌正规开锁",
        "desc": "应急开锁不是谁都能做。选择公安备案的开锁师傅，既能保证技术专业、不损坏门体，也能避免个人信息泄露和后续纠纷。",
    },
    {
        "title": "汽车钥匙全丢了怎么办？义乌配一把多少钱？",
        "slug": "car-key-lost-cost",
        "category": "汽车钥匙",
        "keywords": "义乌汽车钥匙全丢,义乌配汽车钥匙,汽车钥匙丢了怎么办,汽车钥匙匹配",
        "desc": "汽车钥匙全部丢失不用慌。只要提供车辆信息，专业设备可以现场匹配芯片钥匙和遥控器。不同车型价格差异大。",
    },
    {
        "title": "指纹锁安装前必须知道的3件事",
        "slug": "fingerprint-lock-install-tips",
        "category": "指纹锁",
        "keywords": "义乌指纹锁安装,指纹锁安装注意事项,智能锁安装,指纹锁安装要求",
        "desc": "门的厚度、锁体导向片尺寸、天地钩是否保留，这三个细节决定了指纹锁能不能顺利安装。",
    },
    {
        "title": "电梯卡为什么有的能复制，有的不能？",
        "slug": "elevator-card-copy-guide",
        "category": "门禁电梯卡",
        "keywords": "义乌电梯卡复制,电梯卡复制,门禁卡复制,电梯卡解密",
        "desc": "普通IC/ID卡可以直接复制；加密卡需要先破解密钥；带滚动码的梯控卡则需要专用设备写卡。本文帮你分清三种卡的区别和费用。",
    },
    {
        "title": "租房换锁芯，房东会扣押金吗？",
        "slug": "rental-lock-cylinder-deposit",
        "category": "换锁芯",
        "keywords": "义乌租房换锁,换锁芯押金,租房安全,锁芯更换",
        "desc": "租房换锁芯是保护自己安全的必要措施。本文讲解如何与房东沟通、保留旧锁芯、避免退租纠纷。",
    },
    {
        "title": "汽车钥匙进水了还能用吗？",
        "slug": "car-key-water-damage",
        "category": "汽车钥匙",
        "keywords": "汽车钥匙进水,车钥匙泡水,遥控钥匙维修,义乌汽车钥匙",
        "desc": "车钥匙掉水里不要慌。正确处理可以救回钥匙，处理不当可能直接报废芯片。本文教你应急处理和维修建议。",
    },
    {
        "title": "指纹锁电池没电了怎么办？",
        "slug": "fingerprint-lock-dead-battery",
        "category": "指纹锁",
        "keywords": "指纹锁没电,智能锁应急供电,指纹锁电池,义乌指纹锁维修",
        "desc": "指纹锁提示电量低、完全没电进不了门？本文介绍应急供电方法和电池更换注意事项。",
    },
    {
        "title": "半夜门锁坏了该打119还是开锁公司？",
        "slug": "midnight-lock-emergency",
        "category": "开锁常识",
        "keywords": "义乌半夜开锁,24小时开锁,门锁坏了,消防开门",
        "desc": "半夜遇到门锁故障、家人被困等紧急情况，什么时候该找消防，什么时候该找开锁公司？本文给出明确建议。",
    },
    {
        "title": "防盗门猫眼真的安全吗？",
        "slug": "door-viewer-security",
        "category": "开锁常识",
        "keywords": "防盗门猫眼,猫眼开锁,猫眼防盗,义乌开锁",
        "desc": "传统猫眼存在被工具勾开的风险。本文讲解猫眼的隐患和升级方案，提升入户门安全性。",
    },
    {
        "title": "义乌哪里配电动车遥控器钥匙？",
        "slug": "e-scooter-remote-key-yiwu",
        "category": "汽车钥匙",
        "keywords": "义乌电动车钥匙,电动车遥控器,电瓶车钥匙匹配,遥控器复制",
        "desc": "电动车遥控器丢了可以现场匹配。本文介绍义乌配电动车遥控器的流程、价格和注意事项。",
    },
    {
        "title": "密码锁改密码怎么操作？",
        "slug": "password-lock-change-code",
        "category": "指纹锁",
        "keywords": "密码锁改密码,指纹锁改密码,智能锁设置,义乌智能锁",
        "desc": "机械密码锁和电子密码锁改密码方法不同。本文汇总常见品牌的改密步骤和忘记管理员密码的处理办法。",
    },
    {
        "title": "锁芯卡住转不动怎么办？",
        "slug": "lock-cylinder-stuck-fix",
        "category": "换锁芯",
        "keywords": "锁芯卡住,钥匙转不动,锁芯维修,义乌换锁芯",
        "desc": "钥匙插进去转不动、锁芯生锈卡住？先别急着换锁，试试这几个方法，可能几分钟就能解决。",
    },
    {
        "title": "办公室玻璃门指纹锁怎么选？",
        "slug": "office-glass-door-lock",
        "category": "指纹锁",
        "keywords": "玻璃门指纹锁,办公室智能锁,义乌指纹锁安装,玻璃门锁",
        "desc": "办公室玻璃门装指纹锁要考虑门型、有无框、开门方向等因素。本文帮你选对型号和安装方案。",
    },
    {
        "title": "车钥匙按键没反应是什么问题？",
        "slug": "car-key-button-not-working",
        "category": "汽车钥匙",
        "keywords": "车钥匙按键没反应,遥控钥匙失灵,汽车钥匙维修,义乌汽车钥匙",
        "desc": "遥控钥匙按键失灵可能是电池、按键磨损或信号丢失。本文教你逐步排查和处理。",
    },
    {
        "title": "智能锁有必要装猫眼摄像头吗？",
        "slug": "smart-lock-door-camera",
        "category": "指纹锁",
        "keywords": "智能锁猫眼,可视门铃,指纹锁摄像头,义乌智能锁",
        "desc": "带摄像头的智能锁能看门外、对讲、录像，但价格和安装要求更高。本文分析是否值得加装。",
    },
    {
        "title": "老式防盗门锁能换指纹锁吗？",
        "slug": "old-door-fingerprint-lock",
        "category": "指纹锁",
        "keywords": "老式防盗门换指纹锁,旧门智能锁,指纹锁适配,义乌指纹锁",
        "desc": "十几年的老式防盗门能不能装指纹锁？主要看锁体尺寸和门厚。本文讲清改装条件和常见难点。",
    },
    {
        "title": "钥匙断在锁里了怎么取出来？",
        "slug": "broken-key-extraction",
        "category": "开锁常识",
        "keywords": "钥匙断锁里,断钥匙取出,开锁技巧,义乌开锁",
        "desc": "钥匙拧断在锁芯里是常见问题。本文讲解自救方法和什么情况下必须找专业师傅。",
    },
    {
        "title": "装指纹锁要预留什么尺寸？",
        "slug": "fingerprint-lock-size-requirements",
        "category": "指纹锁",
        "keywords": "指纹锁尺寸,智能锁安装尺寸,锁体导向片,义乌指纹锁安装",
        "desc": "买指纹锁前量好门厚、锁体长宽、导向片尺寸，能避免退换货和安装失败。",
    },
    {
        "title": "汽车一键启动钥匙丢了怎么办？",
        "slug": "push-start-key-lost",
        "category": "汽车钥匙",
        "keywords": "一键启动钥匙丢失,智能钥匙匹配,义乌配车钥匙,汽车钥匙全丢",
        "desc": "一键启动车型钥匙全丢也能配，但需要专用设备解码防盗系统。本文说明流程和费用。",
    },
    {
        "title": "民宿酒店刷卡锁坏了怎么应急？",
        "slug": "hotel-card-lock-emergency",
        "category": "门禁电梯卡",
        "keywords": "酒店刷卡锁,民宿门锁,感应锁维修,义乌锁具维修",
        "desc": "酒店刷卡锁故障会影响客人入住。本文讲解常见故障原因和应急处理方案。",
    },
    {
        "title": "家用保险柜选电子锁还是机械锁？",
        "slug": "safe-electronic-vs-mechanical",
        "category": "保险柜开锁",
        "keywords": "保险柜选购,电子保险柜,机械保险柜,义乌保险柜",
        "desc": "电子保险柜和机械保险柜各有利弊。本文从安全性、耐用性、维护成本角度给出选购建议。",
    },
    {
        "title": "防盗门密封条老化会导致锁不上吗？",
        "slug": "door-seal-lock-problem",
        "category": "开锁常识",
        "keywords": "防盗门密封条,门关不上,门锁不上,义乌修锁",
        "desc": "密封条膨胀老化会让门难开关，甚至导致锁舌对不上锁扣。本文教你判断和处理。",
    },
    {
        "title": "指纹锁指纹识别不灵敏怎么办？",
        "slug": "fingerprint-not-recognized",
        "category": "指纹锁",
        "keywords": "指纹锁识别不灵,指纹锁故障,指纹识别率低,义乌指纹锁维修",
        "desc": "指纹锁识别率低可能跟手指状态、指纹录入、传感器脏污有关。本文给出优化方法。",
    },
    {
        "title": "义乌汽车钥匙匹配需要多长时间？",
        "slug": "car-key-matching-time-yiwu",
        "category": "汽车钥匙",
        "keywords": "义乌配汽车钥匙时间,汽车钥匙匹配多久,车钥匙现场匹配,义乌汽车钥匙",
        "desc": "普通车型增加钥匙30分钟到1小时，全丢车型需要1-3小时。本文说明影响时间的因素。",
    },
    {
        "title": "门禁卡可以复制到手机里吗？",
        "slug": "access-card-to-phone",
        "category": "门禁电梯卡",
        "keywords": "门禁卡复制手机,NFC门禁卡,手机模拟门禁卡,义乌门禁卡",
        "desc": "部分未加密的IC卡可以用手机NFC模拟，但加密卡和CPU卡通常不行。本文讲清原理和限制。",
    },
]


def load_history() -> dict:
    """加载已生成文章历史"""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("[WARN] Failed to load history: %s", e)
    return {}


def save_history(history: dict) -> None:
    """保存生成历史"""
    try:
        HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        logger.warning("[WARN] Failed to save history: %s", e)


def select_topics(history: dict, today: str) -> list:
    """选择今天生成的3个主题，尽量不与近期重复"""
    used_slugs = set()
    for date_str, slugs in history.items():
        # 近7天已用主题不再使用
        if isinstance(slugs, list):
            used_slugs.update(slugs)

    available = [t for t in TOPICS if t["slug"] not in used_slugs]
    if len(available) < ARTICLES_PER_DAY:
        logger.warning("[WARN] Not enough fresh topics, reusing older ones")
        available = TOPICS[:]

    return random.sample(available, min(ARTICLES_PER_DAY, len(available)))


def generate_article(topic: dict) -> str:
    """调用 Kimi API 生成文章正文"""
    if not API_KEY:
        raise RuntimeError("KIMI_API_KEY environment variable not set")

    system_prompt = (
        "你是金钥匙开锁店（义乌福田银海二区菜市场外围A-10号，电话15605799786）的本地化锁具科普作者。"
        "请用中文撰写一篇科普文章，要求："
        "1. 文章结构清晰，分小节，有h2标题；"
        "2. 语言通俗易懂，结合义乌本地场景；"
        "3. 内容实用，有实际建议，不要过度营销；"
        "4. 文章字数在800到1200字之间；"
        "5. 可在文章末尾自然引入金钥匙开锁店的联系电话15605799786和地址，但不要每段都出现；"
        "6. 不要出现emoji、特殊符号或圈号；"
        "7. 输出仅包含文章正文HTML段落（只要article内的p/h2/ul/li/div，不要完整网页HTML）。"
    )
    user_prompt = f"主题：{topic['title']}\n关键词：{topic['keywords']}\n摘要：{topic['desc']}\n\n请生成文章正文。"

    try:
        import requests
    except ImportError as e:
        raise RuntimeError("Missing requests dependency") from e

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 1.0,
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
<div class="top-bar"><span class="hours">24小时 · 福田10分钟到</span><a href="tel:15605799786" class="phone">电话 15605799786</a></div>
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
  <a href="/blog/" class="back">返回锁具知识列表</a>
</article>

<footer><div class="container"><p>&copy; 2026 金钥匙开锁店 · yiwks.com</p></div></footer>
<div class="bottom-bar"><a href="tel:15605799786" class="phone-btn">一键拨号 15605799786</a><a href="#" onclick="showWechat()">微信</a><a href="/booking/">预约</a></div>
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


def update_blog_index(new_articles: list):
    """在 blog/index.html 最上方插入新文章卡片"""
    index_path = BLOG_DIR / "index.html"
    html = index_path.read_text(encoding="utf-8")

    cards = ""
    for topic, date_str, slug in new_articles:
        cards += f"""    <article class="blog-card">
      <h2><a href="/blog/{date_str}-{slug}/">{topic['title']}</a></h2>
      <div class="meta">发布日期：{date_str} · 分类：{topic['category']}</div>
      <p>{topic['desc']}</p>
      <a href="/blog/{date_str}-{slug}/" class="readmore">阅读全文 &rarr;</a>
    </article>

"""

    marker = '<section class="blog-list">\n  <div class="container">\n'
    if marker in html:
        html = html.replace(marker, marker + cards)
    else:
        html = html.replace('<section class="blog-list">\n  <div class="container">', '<section class="blog-list">\n  <div class="container">\n' + cards)
    index_path.write_text(html, encoding="utf-8")


def update_sitemap(new_articles: list):
    """更新 sitemap.xml"""
    sitemap_path = SITE_DIR / "sitemap.xml"
    html = sitemap_path.read_text(encoding="utf-8")
    entries = ""
    for topic, date_str, slug in new_articles:
        if f"/blog/{date_str}-{slug}/" in html:
            continue
        entries += f"""  <url>\n    <loc>{SITE_URL}/blog/{date_str}-{slug}/</loc>\n    <lastmod>{date_str}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n"""
    if entries:
        html = html.replace("</urlset>", entries + "</urlset>")
        sitemap_path.write_text(html, encoding="utf-8")


def git_push(message: str) -> bool:
    """自动提交并推送"""
    try:
        subprocess.run(["git", "add", "."], cwd=SITE_DIR, check=True, capture_output=True, text=True)
        result = subprocess.run(["git", "status", "--short"], cwd=SITE_DIR, check=True, capture_output=True, text=True)
        if not result.stdout.strip():
            logger.info("[INFO] No changes to commit")
            return True
        subprocess.run(["git", "commit", "-m", message], cwd=SITE_DIR, check=True, capture_output=True, text=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=SITE_DIR, check=True, capture_output=True, text=True)
        logger.info("[OK] Git push completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error("[FAIL] Git operation failed: %s", e)
        logger.error("[FAIL] stdout: %s", e.stdout if e.stdout else "")
        logger.error("[FAIL] stderr: %s", e.stderr if e.stderr else "")
        return False


def main():
    # 使用香港时区
    os.environ.setdefault("TZ", "Asia/Hong_Kong")
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info("[INFO] Starting daily blog generation for %s", today)

    if not API_KEY:
        logger.error("[FAIL] KIMI_API_KEY not set")
        raise RuntimeError("KIMI_API_KEY not set")

    history = load_history()
    topics = select_topics(history, today)
    logger.info("[INFO] Selected %d topics for today", len(topics))

    new_articles = []
    used_slugs = []
    for topic in topics:
        slug = topic["slug"]
        post_dir = BLOG_DIR / f"{today}-{slug}"
        post_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[INFO] Generating article: %s", topic["title"])
        try:
            body = generate_article(topic)
        except Exception as e:
            logger.error("[FAIL] Failed to generate article '%s': %s", topic["title"], e)
            continue

        post_html = build_post_html(topic, today, body)
        (post_dir / "index.html").write_text(post_html, encoding="utf-8")
        new_articles.append((topic, today, slug))
        used_slugs.append(slug)
        logger.info("[OK] Article saved: %s", post_dir / "index.html")

    if not new_articles:
        logger.error("[FAIL] No articles generated today")
        return

    update_blog_index(new_articles)
    update_sitemap(new_articles)

    # 记录历史
    history[today] = used_slugs
    save_history(history)

    # Git push
    success = git_push(f"blog: add {today} {len(new_articles)} articles")
    if success:
        logger.info("[OK] Daily blog generation completed: %d articles", len(new_articles))
    else:
        logger.error("[FAIL] Articles generated but git push failed")


if __name__ == "__main__":
    main()
