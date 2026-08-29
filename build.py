#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
build.py v8 - 全自动博客构建脚本

功能：
  1) 扫描 posts/*.md，从 YAML front matter 自动提取元数据
  2) 校验格式（title/date/tags/excerpt），出错明明白白提醒
  3) 自动生成 index.json（再也不用手写）
  4) 把每篇 .md 渲染成独立静态 HTML
     - 代码块保护后原样保留，交给前端 highlight.js 高亮
     - LaTeX 公式保护后原样保留，交给前端 MathJax 渲染
     - 自动给 ## 二级标题加 id，生成左侧 TOC 目录
  5) 更新首页静态文章列表
  6) 生成 sitemap.xml（含 lastmod）+ robots.txt
  7) 每篇文章输出到 html/ 子目录，.md 和图片保持原位
  8) 三栏布局：左 TOC + 中内容 + 右边栏（头像/导航/同标签推荐）

原则：
  - 绝不修改 .md 源文件
  - excerpt 从纯 Markdown 正文提取，不依赖渲染结果

v8 新增：
  - 去掉顶栏，改为右侧边栏（头像+导航+推荐文章）
  - 首页：右侧栏显示最新文章
  - 文章页：右侧栏显示同标签文章
  - 主要内容居中

用法：
  python build.py
  python build.py D:/我的/Python程序/网站/我的博客
  set SITE_URL=https://ling-nine.github.io  (Windows CMD)
  $env:SITE_URL="https://ling-nine.github.io"  (PowerShell)
"""

import sys, os, re, json, uuid
from datetime import datetime, timezone
from pathlib import Path

import markdown as md
import yaml

# ── 路径配置 ───────────────────────────────────────
if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()
else:
    ROOT = Path(__file__).resolve().parent

POSTS_DIR = ROOT / "posts"
HTML_DIR = ROOT / "html"
INDEX_JSON = POSTS_DIR / "index.json"
SITE_URL = os.environ.get("SITE_URL", "https://ling-nine.github.io").rstrip("/")
SITE_NAME = "彾九平"
SITE_DESC = "记录学习心得、技术笔记与生活感悟"
AVATAR_PATH = "posts/images/test/头像.png"

# ── Markdown 配置 ────────────────────────────────────
MD_EXTENSIONS = ["extra", "fenced_code", "tables"]
MD_EXT_CONFIG = {}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# ═════════════════════════════════════════════════
#  日志
# ═════════════════════════════════════════════════
class Log:
    def __init__(self):
        self.errors, self.warnings = [], []
    def ok(self, m):   print(f"  ✅ {m}")
    def info(self, m):  print(f"  ℹ️  {m}")
    def warn(self, m):
        print(f"  ⚠️  {m}"); self.warnings.append(m)
    def err(self, m):
        print(f"  ❌ {m}"); self.errors.append(m)

log = Log()

# ═════════════════════════════════════════════════
#  Front Matter 解析
# ═════════════════════════════════════════════════
def parse_front_matter(text, filename):
    if not text.lstrip().startswith("---"):
        log.err(f"[{filename}] 缺少 front matter（文件开头必须是 ---）")
        return None, text
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", text, re.DOTALL)
    if not m:
        log.err(f"[{filename}] front matter 格式错误（缺少结束的 ---）")
        return None, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        log.err(f"[{filename}] YAML 解析失败：{e}")
        return None, m.group(2)
    return meta, m.group(2)

# ═════════════════════════════════════════════════
#  从纯 Markdown 源提取 excerpt
# ═════════════════════════════════════════════════
def _extract_excerpt_from_markdown(body, max_len=80):
    text = body
    text = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', text, flags=re.DOTALL)
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    text = re.sub(r'(?m)^( {4,}|\t+).*$', ' ', text)
    text = re.sub(r'`[^`]+`', ' ', text)
    text = re.sub(r'\$\$.*?\$\$', ' ', text, flags=re.DOTALL)
    text = re.sub(r'\$[^$\n]+?\$', ' ', text)
    text = re.sub(r'\\[\(\[].*?\\\)[\])]', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'[*_~]', '', text)
    text = re.sub(r'^[\->*\d+\.]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + '...'
    return text

# ═════════════════════════════════════════════════
#  格式校验
# ═════════════════════════════════════════════════
def validate_meta(meta, filename, body):
    c = dict(meta)

    if "title" not in c or not str(c["title"]).strip():
        log.err(f"[{filename}] 缺少 title 字段")
        c["title"] = Path(filename).stem
    else:
        c["title"] = str(c["title"]).strip()

    if "date" not in c or not str(c["date"]).strip():
        log.err(f"[{filename}] 缺少 date 字段")
        c["date"] = datetime.now().strftime("%Y-%m-%d")
    else:
        dv = str(c["date"]).strip()
        if hasattr(c["date"], "strftime"):
            dv = c["date"].strftime("%Y-%m-%d")
        if not DATE_PATTERN.match(dv):
            log.err(f"[{filename}] date 格式错误: {dv}，应为 YYYY-MM-DD")
            fixed = re.sub(r"[年/]", "-", dv).replace("月", "-").replace("日", "").strip("-")
            dv = fixed if DATE_PATTERN.match(fixed) else datetime.now().strftime("%Y-%m-%d")
        c["date"] = dv

    if "tags" not in c:
        log.warn(f"[{filename}] 缺少 tags，默认空数组")
        c["tags"] = []
    else:
        t = c["tags"]
        if isinstance(t, str):
            if "，" in t:
                log.warn(f"[{filename}] tags 中文逗号已自动拆分")
            c["tags"] = [x.strip() for x in re.split(r"[,，]", t) if x.strip()]
        elif isinstance(t, list):
            out = []
            for x in t:
                x = str(x).strip()
                if "，" in x:
                    log.warn(f"[{filename}] 标签「{x}」含中文逗号，已拆分")
                    out.extend([y.strip() for y in x.split("，") if y.strip()])
                else:
                    out.append(x)
            c["tags"] = out
        else:
            log.warn(f"[{filename}] tags 类型异常（{type(t).__name__}），重置为空数组")
            c["tags"] = []

    if "excerpt" not in c or not str(c["excerpt"]).strip():
        exc = _extract_excerpt_from_markdown(body)
        log.info(f"[{filename}] 自动 excerpt: {exc[:50]}...")
        c["excerpt"] = exc
    else:
        c["excerpt"] = str(c["excerpt"]).strip()

    return c

# ═════════════════════════════════════════════════
#  代码块智能保护 / 还原
# ═════════════════════════════════════════════════
def protect_code_blocks(text):
    lines = text.split('\n')
    store = []
    result = []
    in_code = False
    code_buffer = []
    fence_len = 0

    for line in lines:
        if not in_code:
            m = re.match(r'^(`{3,})\s*([\w-]*)\s*$', line)
            if m:
                fence_len = len(m.group(1))
                in_code = True
                code_buffer = []
                result.append(line)
            else:
                result.append(line)
        else:
            m = re.match(r'^(`{3,})\s*$', line)
            if m and len(m.group(1)) == fence_len:
                code_content = '\n'.join(code_buffer)
                token = f"\x00CODE{uuid.uuid4().hex}\x00"
                store.append((token, code_content))
                result.append(token)
                result.append(line)
                in_code = False
                fence_len = 0
                code_buffer = []
            else:
                code_buffer.append(line)

    if in_code:
        code_content = '\n'.join(code_buffer)
        token = f"\x00CODE{uuid.uuid4().hex}\x00"
        store.append((token, code_content))
        result.append(token)
        result.append('`' * fence_len)

    return '\n'.join(result), store

def restore_code_blocks(text, store):
    for token, code in store:
        text = text.replace(token, code)
    return text

# ═════════════════════════════════════════════════
#  LaTeX 公式保护 / 还原
# ═════════════════════════════════════════════════
_MATH_PATTERN = re.compile(r'(\$\$.*?\$\$|\$.*?\$|\\[\(\[].*?\\\)[\])])', re.DOTALL)

def protect_math(text):
    store = []
    def repl(match):
        token = f"\x00MATH{uuid.uuid4().hex}\x00"
        store.append((token, match.group(0)))
        return token
    return _MATH_PATTERN.sub(repl, text), store

def restore_math(text, store):
    for token, formula in store:
        text = text.replace(token, formula)
    return text

# ═════════════════════════════════════════════════
#  TOC 提取 + h2 加 id
# ═════════════════════════════════════════════════
def extract_toc(md_text):
    toc = []
    body = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', md_text, flags=re.DOTALL)
    body = re.sub(r'```.*?```', '', body, flags=re.DOTALL)
    for line in body.split('\n'):
        m = re.match(r'^##\s+(.+?)\s*$', line)
        if m:
            text = m.group(1).strip()
            anchor = text.lower()
            anchor = re.sub(r'[^\w\u4e00-\u9fff-]', '-', anchor)
            anchor = re.sub(r'-+', '-', anchor).strip('-')
            toc.append({"id": anchor, "text": text})
    return toc

def add_heading_ids(html, toc):
    for item in toc:
        pattern = rf'(<h2\b[^>]*)>(.*?{re.escape(item["text"])}.*?</h2>)'
        replacement = rf'<h2 id="{item["id"]}">\2'
        html = re.sub(pattern, replacement, html)
    return html

def build_toc_html(toc):
    if not toc:
        return ""
    items = "\n".join(
        f'        <li><a href="#{item["id"]}">{item["text"]}</a></li>'
        for item in toc
    )
    return f"""    <aside class="toc-sidebar">
        <div class="toc-title">📑 目录</div>
        <ul class="toc-list">
{items}
        </ul>
    </aside>
"""

# ═════════════════════════════════════════════════
#  Markdown → HTML
# ═════════════════════════════════════════════════
def md_to_html(body, toc_out=None):
    protected_code, code_store = protect_code_blocks(body)
    protected_math, math_store = protect_math(protected_code)
    html = md.markdown(
        protected_math,
        extensions=MD_EXTENSIONS,
        extension_configs=MD_EXT_CONFIG
    )
    html = restore_math(html, math_store)
    html = restore_code_blocks(html, code_store)
    if toc_out:
        html = add_heading_ids(html, toc_out)
    return html

# ═════════════════════════════════════════════════
#  工具
# ═════════════════════════════════════════════════
def slugify(name):
    return re.sub(r"\.md$", "", name, flags=re.I)

def format_date(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").strftime("%Y年%-m月%-d日")
    except ValueError:
        return str(s)

def format_date_short(s):
    """短日期格式 2026-08-04"""
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return str(s)

# ═════════════════════════════════════════════════
#  MathJax 脚本
# ═════════════════════════════════════════════════
MATHJAX_SCRIPT = r"""
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    tags: 'none'
  },
  svg: { fontCache: 'global' },
  startup: { typeset: true }
};
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js" async></script>
"""

# ═════════════════════════════════════════════════
#  highlight.js 脚本
# ═════════════════════════════════════════════════
HLJS_SCRIPTS = """
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/vs.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/javascript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/cpp.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/c.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/java.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/go.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/rust.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/sql.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/markdown.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/typescript.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/languages/plaintext.min.js"></script>
    <script>document.addEventListener('DOMContentLoaded', () => hljs.highlightAll());</script>
"""

# ═════════════════════════════════════════════════
#  推荐文章 HTML 生成（同标签文章）
# ═════════════════════════════════════════════════
def build_recommend_html(current_post, all_posts_sorted):
    """
    根据当前文章的 tags，从 all_posts_sorted 中找出同标签的其他文章。
    只返回有相同标签的文章，按匹配数降序、日期倒序，最多 5 篇。
    如果一篇文章都没有同标签，返回空字符串（不显示推荐区）。
    """
    current_tags = set(current_post.get("tags", []))
    current_filename = current_post.get("filename", "")

    if not current_tags:
        return ""

    scored = []
    for p in all_posts_sorted:
        if p.get("filename", "") == current_filename:
            continue
        p_tags = set(p.get("tags", []))
        overlap = len(current_tags & p_tags)
        if overlap > 0:
            scored.append((overlap, p))

    # 按标签匹配数降序，再按日期降序
    scored.sort(key=lambda x: (-x[0], str(x[1].get("date", ""))), reverse=True)
    top = [s[1] for s in scored[:5]]

    if not top:
        return ""

    items = []
    for p in top:
        slug = slugify(p["filename"])
        # 文章页在 html/ 子目录下，所以推荐链接只需 "slug.html"
        href = f"{slug}.html"
        short_date = format_date_short(p.get("date", ""))
        items.append(
            f'                    <li><a href="{href}">{p["title"]}'
            f'<span class="recommend-date">{short_date}</span></a></li>'
        )

    return "\n".join(items)

# ═════════════════════════════════════════════════
#  HTML 模板 — 文章页（三栏布局）
# ═════════════════════════════════════════════════
def build_post_html(post_html, meta, prev_post, next_post, toc, all_posts_sorted):
    title = meta["title"]
    date = meta["date"]
    tags = meta.get("tags", [])
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

    # 文章页位于 html/ 子目录下，所以同目录链接不需要加 html/ 前缀
    prev_href = f"{slugify(prev_post['filename'])}.html" if prev_post else "#"
    next_href = f"{slugify(next_post['filename'])}.html" if next_post else "#"
    prev_text = f"← {prev_post['title']}" if prev_post else "← 上一篇"
    next_text = f"{next_post['title']} →" if next_post else "下一篇 →"

    toc_html = build_toc_html(toc) if toc else ""

    # 推荐文章（文章页在 html/ 目录下，链接已为相对路径）
    recommend_items = build_recommend_html(meta, all_posts_sorted)
    if recommend_items:
        recommend_html = f"""
        <div class="recommend-section">
            <div class="recommend-title">📌 相关推荐</div>
            <ul class="recommend-list">
{recommend_items}
            </ul>
        </div>"""
    else:
        recommend_html = ""
    # 无同标签文章时显示提示
    if not recommend_items:
        recommend_html = """
        <div class="recommend-section">
            <div class="recommend-title">📌 相关推荐</div>
            <p style="font-size:0.85rem;color:var(--secondary-color);padding:0.4rem 0.5rem;">
                暂无同标签文章
            </p>
        </div>"""

    tags_html = " ".join(f"<span class='tag'>{t}</span>" for t in tags)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {SITE_NAME}</title>
    <meta name="description" content="{meta.get('excerpt', '')}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta.get('excerpt', '')}">
    <meta property="og:type" content="article">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=ZCOOL+XiaoWei&display=swap">
    <link rel="stylesheet" href="../../css/style.css">
    {HLJS_SCRIPTS}
    <link rel="icon" type="image/x-icon" href="../../favicon.ico">
    {MATHJAX_SCRIPT}
</head>
<body>
    <div class="main-layout">
{toc_html}
        <main class="content-area">
            <article class="post-container">
                <div class="post-header">
                    <h1 id="post-title">{title}</h1>
                    <div class="post-meta">
                        <span>📅 {format_date(date)}</span>
                        <span>🏷️ {tags_html}</span>
                    </div>
                </div>
                <div class="post-content" id="post-content">
{post_html}
                </div>
                <div class="post-navigation">
                    <a href="{prev_href}">{prev_text}</a>
                    <a href="../../index.html">返回首页</a>
                    <a href="{next_href}">{next_text}</a>
                </div>
            </article>
        </main>

        <aside class="right-sidebar">
            <div class="profile-section">
                <img class="profile-avatar" src="../../{AVATAR_PATH}" alt="{SITE_NAME}">
                <div class="profile-name">{SITE_NAME}</div>
                <div class="profile-desc">{SITE_DESC}</div>
            </div>
            <nav class="sidebar-nav">
                <a href="../../index.html">🏠 首页</a>
                <a href="../../index.html#about">📖 关于</a>
                <a href="../../links/index.html">🔗 友链</a>
                <a href="../../index.html#contact">✉️ 联系</a>
            </nav>
{recommend_html}
        </aside>
    </div>

    <footer>
        <p>&copy; 2026 {SITE_NAME} | <a href="../../index.html">返回首页</a></p>
    </footer>
</body>
</html>"""

# ═════════════════════════════════════════════════
#  首页文章列表 HTML
# ═════════════════════════════════════════════════
def build_index_html(posts_sorted):
    items = []
    for p in posts_sorted:
        slug = slugify(p["filename"])
        href = f"html/{slug}.html"
        tags_html = " ".join(f"<span class='tag'>{t}</span>" for t in p.get("tags", []))
        items.append(f"""
            <article class="post-item">
                <h3><a href="{href}">{p['title']}</a></h3>
                <div class="post-meta">
                    <span>📅 {format_date(p['date'])}</span>
                    <span>🏷️ {tags_html}</span>
                </div>
                <div class="post-excerpt">{p.get('excerpt', '点击阅读全文...')}</div>
                <a href="{href}" class="read-more">阅读全文 →</a>
            </article>""")
    return "\n".join(items)

# ═════════════════════════════════════════════════
#  sitemap
# ═════════════════════════════════════════════════
def build_sitemap(posts_sorted):
    if not SITE_URL:
        return None
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines.append(f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod></url>")
    lines.append(f"  <url><loc>{SITE_URL}/links/index.html</loc><lastmod>{today}</lastmod></url>")
    for p in posts_sorted:
        slug = slugify(p["filename"])
        url = f"{SITE_URL}/html/{slug}.html"
        lastmod = p.get("date") or today
        lines.append(f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>")
    lines.append("</urlset>")
    return "\n".join(lines)

# ═════════════════════════════════════════════════
#  首页更新
# ═════════════════════════════════════════════════
def update_index_html(posts_sorted):
    index_path = ROOT / "index.html"
    if not index_path.exists():
        log.warn("找不到 index.html，跳过首页更新")
        return
    content = index_path.read_text(encoding="utf-8")
    new_list = build_index_html(posts_sorted)
    # 只替换 posts-container 内的内容，到 </div> 就停（不吞掉后面的 about/contact 区域）
    new_content = re.sub(
        r'(<div id="posts-container">).*?(</div>\s*\n\s*</section>)',
        rf'\1{new_list}\2',
        content, flags=re.DOTALL
    )
    # 如果上面的正则没匹配到，尝试匹配带缩进的 </div>
    if "post-item" not in new_content.split('id="about"')[0] if 'id="about"' in new_content else True:
        # 兜底：直接替换 loading 占位符
        pass
    if "正在加载文章" in new_content and "post-item" not in new_content:
        new_content = new_content.replace(
            '<div class="loading">正在加载文章...</div>',
            new_list
        )
    # 确保 about 和 contact 锚点存在
    if 'id="about"' not in new_content:
        new_content = re.sub(r'<section class="about-section">',
                             '<section class="about-section" id="about">',
                             new_content)
    if 'id="contact"' not in new_content:
        new_content = re.sub(r'<section class="contact-section">',
                             '<section class="contact-section" id="contact">',
                             new_content)
    index_path.write_text(new_content, encoding="utf-8")
    log.ok("首页 index.html 已更新")

# ═════════════════════════════════════════════════
#  生成首页右侧栏的推荐文章 HTML
# ═════════════════════════════════════════════════
def build_home_recommend_html(posts_sorted, count=5):
    """首页右侧栏显示最新文章（首页在根目录，链接用 html/ 前缀）"""
    top = posts_sorted[:count]
    items = []
    for p in top:
        slug = slugify(p["filename"])
        href = f"html/{slug}.html"
        short_date = format_date_short(p.get("date", ""))
        items.append(
            f'                    <li><a href="{href}">{p["title"]}'
            f'<span class="recommend-date">{short_date}</span></a></li>'
        )
    return "\n".join(items)

# ═════════════════════════════════════════════════
#  更新首页右侧栏推荐文章
# ═════════════════════════════════════════════════
def update_home_sidebar(posts_sorted):
    """替换首页右侧栏的推荐文章列表"""
    index_path = ROOT / "index.html"
    if not index_path.exists():
        return
    content = index_path.read_text(encoding="utf-8")
    new_recommend = build_home_recommend_html(posts_sorted)
    # 替换 recommend-list 中的内容
    new_content = re.sub(
        r'(<ul class="recommend-list">).*?(</ul>)',
        rf'\1\n{new_recommend}\n                \2',
        content, flags=re.DOTALL
    )
    index_path.write_text(new_content, encoding="utf-8")
    log.ok("首页右侧栏推荐文章已更新")

# ═════════════════════════════════════════════════
#  主流程
# ═════════════════════════════════════════════════
def main():
    print(f"📂 项目根目录: {ROOT}")
    print(f"📂 文章目录:   {POSTS_DIR}")
    print(f"📂 HTML 输出:   {HTML_DIR}")
    print(f"🌐 站点 URL:   {SITE_URL}")
    print()

    if not POSTS_DIR.is_dir():
        print(f"❌ 找不到 {POSTS_DIR}")
        sys.exit(1)

    HTML_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted([f for f in POSTS_DIR.glob("*.md") if not f.name.startswith("_")])

    if not md_files:
        print("❌ posts/ 下没有 .md 文件")
        sys.exit(1)

    print(f"📄 发现 {len(md_files)} 个 Markdown 文件\n")

    posts = []
    for md_path in md_files:
        filename = md_path.name
        text = md_path.read_text(encoding="utf-8")

        meta, body = parse_front_matter(text, filename)
        if meta is None:
            meta = {"title": md_path.stem, "date": datetime.now().strftime("%Y-%m-%d"),
                    "tags": [], "excerpt": ""}
            body = text
        else:
            meta = validate_meta(meta, filename, body)

        toc = extract_toc(text)
        meta["toc"] = toc
        meta["filename"] = filename
        posts.append(meta)
        log.ok(f"{filename} → \"{meta['title']}\" ({meta['date']}) tags={meta['tags']} toc={len(toc)}")

    print()
    posts_sorted = sorted(posts, key=lambda p: str(p.get("date", "")), reverse=True)

    # ── index.json ──
    json_data = [
        {"filename": p["filename"], "title": p["title"], "date": p["date"],
         "tags": p.get("tags", []), "excerpt": p.get("excerpt", "")}
        for p in posts_sorted
    ]
    INDEX_JSON.write_text(
        json.dumps(json_data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8"
    )
    log.ok(f"index.json 已生成（{len(json_data)} 篇）")

    # ── 每篇文章 → HTML ──
    for i, post in enumerate(posts_sorted):
        fname = post["filename"]
        md_path = POSTS_DIR / fname
        text = md_path.read_text(encoding="utf-8")
        _, body = parse_front_matter(text, fname)
        if not body:
            body = text

        toc = post.get("toc", [])
        html_body = md_to_html(body, toc if toc else None)

        # 验证 <pre> 标签匹配
        pre_open = html_body.count("<pre>")
        pre_close = html_body.count("</pre>")
        if pre_open != pre_close:
            log.err(f"[{fname}] <pre> 标签不匹配！开={pre_open} 关={pre_close}")
        else:
            log.ok(f"[{fname}] <pre> 标签匹配 ({pre_open} 个)")

        prev_p = posts_sorted[i + 1] if i + 1 < len(posts_sorted) else None
        next_p = posts_sorted[i - 1] if i - 1 >= 0 else None

        page = build_post_html(html_body, post, prev_p, next_p, toc, posts_sorted)

        slug = slugify(fname)
        out = HTML_DIR / f"{slug}.html"
        out.write_text(page, encoding="utf-8")
        log.ok(f"{fname} → html/{slug}.html")

    # ── 首页 ──
    update_index_html(posts_sorted)
    update_home_sidebar(posts_sorted)

    # ── sitemap ──
    sm = build_sitemap(posts_sorted)
    if sm:
        (ROOT / "sitemap.xml").write_text(sm, encoding="utf-8")
        log.ok(f"sitemap.xml → {SITE_URL}/sitemap.xml")

    # ── robots.txt ──
    rb = ROOT / "robots.txt"
    if not rb.exists():
        rb.write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
        log.ok("robots.txt 已生成")
    else:
        log.info("robots.txt 已存在，跳过")

    # ── 汇总 ──
    print()
    if log.errors:
        print(f"❌ {len(log.errors)} 个错误：")
        for e in log.errors: print(f"     {e}")
    if log.warnings:
        print(f"⚠️  {len(log.warnings)} 个警告（已自动修复）：")
        for w in log.warnings: print(f"     {w}")

    if log.errors:
        print("\n💥 构建完成但有错误！"); sys.exit(1)
    elif log.warnings:
        print("\n✨ 构建完成（有警告已处理）")
    else:
        print("\n🎉 构建完成，一切正常！")

if __name__ == "__main__":
    main()
    input()
