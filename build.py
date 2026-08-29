#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
build.py v10 - 全自动博客构建脚本

核心渲染器：markdown-it-py（严格 CommonMark）
TOC 和 HTML id 统一从同一份 Token 流生成，彻底解决数量不一致问题。
"""

import sys, os, re, json, uuid
from datetime import datetime, timezone
from pathlib import Path

from markdown_it import MarkdownIt
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

# ── Markdown-it-py 配置 ────────────────────────────
MDIT = MarkdownIt("commonmark", {"html": False}) \
    .enable("table") \
    .enable("strikethrough")

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

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
        log.err(f"[{filename}] 缺少 front matter")
        return None, text
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", text, re.DOTALL)
    if not m:
        log.err(f"[{filename}] front matter 格式错误")
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
            log.err(f"[{filename}] date 格式错误: {dv}")
            fixed = re.sub(r"[年/]", "-", dv).replace("月", "-").replace("日", "").strip("-")
            dv = fixed if DATE_PATTERN.match(fixed) else datetime.now().strftime("%Y-%m-%d")
        c["date"] = dv

    if "tags" not in c:
        log.warn(f"[{filename}] 缺少 tags，默认空数组")
        c["tags"] = []
    else:
        t = c["tags"]
        if isinstance(t, str):
            c["tags"] = [x.strip() for x in re.split(r"[,，]", t) if x.strip()]
        elif isinstance(t, list):
            out = []
            for x in t:
                x = str(x).strip()
                if "，" in x:
                    out.extend([y.strip() for y in x.split("，") if y.strip()])
                else:
                    out.append(x)
            c["tags"] = out
        else:
            c["tags"] = []

    if "excerpt" not in c or not str(c["excerpt"]).strip():
        exc = _extract_excerpt_from_markdown(body)
        c["excerpt"] = exc
    else:
        c["excerpt"] = str(c["excerpt"]).strip()

    return c

# ═════════════════════════════════════════════════
#  LaTeX 公式保护 / 还原
# ═════════════════════════════════════════════════
# 分两阶段保护，避免 `$...$` 与 `$$...$$` 互相误配对：
#   阶段1：块级 `$$...$$`（要求 $$ 前后不是 $，避免 $$$$ 被拆成空公式）
#   阶段2：行内 `$...$`（要求 $ 前后不是 $，且不含换行）
# 若混成一条 `\$\$.*?\$\$` 非贪婪正则，`$$` 会被当成"空公式"瞬间闭合，
# 导致整块公式(含 cases/矩阵)完全暴露给 markdown-it → & 被转成 &amp;、
# \\ 被当转义吞掉，公式渲染全部报错。
_MATH_BLOCK = re.compile(r'(?<!\$)\$\$(?!\$)(.*?)(?<!\$)\$\$(?!\$)', re.DOTALL)
_MATH_INLINE = re.compile(r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)')
_MATH_PAREN = re.compile(r'(\\[\(\[].*?\\\)[\])])')

def _make_math_token():
    return f"MATHMARKER_{uuid.uuid4().hex}_END"

def _split_fences(text):
    """
    按 Markdown 代码块（``` 或 ~~~ 围栏）切分文本。
    返回 [("code", 内容), ("text", 内容), ...]，保证相邻片段交替。
    围栏行本身归入 "text"，避免把 ``` 吃掉。
    """
    lines = text.split("\n")
    parts = []
    buf = []
    in_fence = False
    for ln in lines:
        is_fence = ln.strip().startswith("```") or ln.strip().startswith("~~~")
        if is_fence:
            if in_fence:      # 结束围栏
                in_fence = False
                parts.append(("code", "\n".join(buf)))
                buf = []
                parts.append(("text", ln))   # 围栏行作为普通文本（不参与公式匹配）
                continue
            else:             # 开始围栏
                in_fence = True
                if buf:
                    parts.append(("text", "\n".join(buf)))
                    buf = []
                buf.append(ln)
                continue
        if in_fence:
            buf.append(ln)
        else:
            buf.append(ln)
    if buf:
        parts.append(("code" if in_fence else "text", "\n".join(buf)))
    return parts

def protect_math(text):
    store = []
    def register(formula):
        token = _make_math_token()
        store.append((token, formula))
        return token
    def repl_block(m):
        return register("$$" + m.group(1) + "$$")
    def repl_inline(m):
        return register("$" + m.group(1) + "$")
    def repl_paren(m):
        return register(m.group(0))
    # 只对非代码块区域做数学保护，防止公式匹配吞掉 fence 内容
    out_parts = []
    for kind, content in _split_fences(text):
        if kind == "text":
            # 顺序很重要：先块级 $$，再行内 $，最后 \( \) \[ \]
            content = _MATH_BLOCK.sub(repl_block, content)
            content = _MATH_INLINE.sub(repl_inline, content)
            content = _MATH_PAREN.sub(repl_paren, content)
        out_parts.append(content)
    return "\n".join(out_parts), store

def restore_math(text, store):
    for token, formula in store:
        text = text.replace(token, formula)
    return text

# ═════════════════════════════════════════════════
#  TOC 提取（从 Token 流）
# ═════════════════════════════════════════════════
def _make_slug(text):
    text = re.sub(r'<[^>]+>', '', text)
    slug = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', text.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or 'section'

def extract_toc_from_tokens(tokens):
    """从 Token 流提取 h2 标题，返回 [{"id": slug, "text": title}, ...]"""
    result = []
    slug_counts = {}
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag == 'h2':
            title = ''
            for j in range(i + 1, min(i + 4, len(tokens))):
                if tokens[j].type == 'inline':
                    title = tokens[j].content
                    break
            base_slug = _make_slug(title)
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                final_id = f'{base_slug}-{slug_counts[base_slug]}'
            else:
                slug_counts[base_slug] = 0
                final_id = base_slug
            result.append({"id": final_id, "text": title})
    return result

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
#  Markdown → HTML + TOC（统一从同一份 Token 流生成）
# ═════════════════════════════════════════════════
def md_to_html(body, filename="<unknown>"):
    """
    解析 Markdown，提取 TOC，给 h2 加 id，渲染 HTML。
    返回 (html, toc)，两者永远一致。
    """
    # 1) 保护 LaTeX
    protected, math_store = protect_math(body)
    # 2) 解析 Token 流（只解析一次）
    tokens = MDIT.parse(protected)
    # 3) 提取 TOC 并给 h2 加 id
    toc = []
    slug_counts = {}
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag == 'h2':
            title = ''
            for j in range(i + 1, min(i + 4, len(tokens))):
                if tokens[j].type == 'inline':
                    title = tokens[j].content
                    break
            base_slug = _make_slug(title)
            if base_slug in slug_counts:
                slug_counts[base_slug] += 1
                final_id = f'{base_slug}-{slug_counts[base_slug]}'
            else:
                slug_counts[base_slug] = 0
                final_id = base_slug
            toc.append({"id": final_id, "text": title})
            token.attrs['id'] = final_id
    # 4) 渲染
    html = MDIT.renderer.render(tokens, MDIT.options, {})
    # 5) 还原 LaTeX
    html = restore_math(html, math_store)
    # 6) 自检
    leftover = re.findall(r'MATHMARKER_[0-9a-f]+_END', html)
    if leftover:
        log.err(f"[{filename}] LaTeX 占位符还原失败，残留 {len(leftover)} 个")
    return html, toc

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
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return str(s)

# ═════════════════════════════════════════════════
#  MathJax / highlight.js 脚本
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
    <script src="https://cdnjs.cloudflare.com/ajax/libiv.com/ajax/libs/highlight.js/11.11.1/languages/java.min.js"></script>
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
#  推荐文章 / HTML 模板
# ═════════════════════════════════════════════════
def build_recommend_html(current_post, all_posts_sorted):
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
    scored.sort(key=lambda x: (-x[0], str(x[1].get("date", ""))), reverse=True)
    top = [s[1] for s in scored[:5]]
    if not top:
        return ""
    items = []
    for p in top:
        slug = slugify(p["filename"])
        href = f"{slug}.html"
        short_date = format_date_short(p.get("date", ""))
        items.append(f'                    <li><a href="{href}">{p["title"]}<span class="recommend-date">{short_date}</span></a></li>')
    return "\n".join(items)

def build_post_html(post_html, meta, prev_post, next_post, toc, all_posts_sorted):
    title = meta["title"]
    date = meta["date"]
    tags = meta.get("tags", [])
    prev_href = f"{slugify(prev_post['filename'])}.html" if prev_post else "#"
    next_href = f"{slugify(next_post['filename'])}.html" if next_post else "#"
    prev_text = f"← {prev_post['title']}" if prev_post else "← 上一篇"
    next_text = f"{next_post['title']} →" if next_post else "下一篇 →"
    toc_html = build_toc_html(toc) if toc else ""
    recommend_items = build_recommend_html(meta, all_posts_sorted)
    if recommend_items:
        recommend_html = f"""        <div class="recommend-section">
            <div class="recommend-title">📌 相关推荐</div>
            <ul class="recommend-list">
{recommend_items}
            </ul>
        </div>"""
    else:
        recommend_html = """        <div class="recommend-section">
            <div class="recommend-title">📌 相关推荐</div>
            <p style="font-size:0.85rem;color:var(--secondary-color);padding:0.4rem 0.5rem;">暂无同标签文章</p>
        </div>"""
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
                        <span>🏷️ {" ".join(f"<span class='tag'>{t}</span>" for t in tags)}</span>
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

def build_index_html(posts_sorted):
    items = []
    for p in posts_sorted:
        slug = slugify(p["filename"])
        href = f"html/{slug}.html"
        tags_html = " ".join(f"<span class='tag'>{t}</span>" for t in p.get("tags", []))
        items.append(f"""            <article class="post-item">
                <h3><a href="{href}">{p['title']}</a></h3>
                <div class="post-meta">
                    <span>📅 {format_date(p['date'])}</span>
                    <span>🏷️ {tags_html}</span>
                </div>
                <div class="post-excerpt">{p.get('excerpt', '点击阅读全文...')}</div>
                <a href="{href}" class="read-more">阅读全文 →</a>
            </article>""")
    return "\n".join(items)

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
        lines.append(f"  <url><loc>{SITE_URL}/html/{slug}.html</loc><lastmod>{p.get('date', today)}</lastmod></url>")
    lines.append("</urlset>")
    return "\n".join(lines)

def update_index_html(posts_sorted):
    index_path = ROOT / "index.html"
    if not index_path.exists():
        log.warn("找不到 index.html，跳过首页更新")
        return
    content = index_path.read_text(encoding="utf-8")
    new_list = build_index_html(posts_sorted)
    new_content = re.sub(r'(<div id="posts-container">).*?(</div>\s*\n\s*</section>)', rf'\1{new_list}\2', content, flags=re.DOTALL)
    if "正在加载文章" in new_content and "post-item" not in new_content:
        new_content = new_content.replace('<div class="loading">正在加载文章...</div>', new_list)
    index_path.write_text(new_content, encoding="utf-8")
    log.ok("首页 index.html 已更新")

def build_home_recommend_html(posts_sorted, count=5):
    items = []
    for p in posts_sorted[:count]:
        slug = slugify(p["filename"])
        short_date = format_date_short(p.get("date", ""))
        items.append(f'                    <li><a href="html/{slug}.html">{p["title"]}<span class="recommend-date">{short_date}</span></a></li>')
    return "\n".join(items)

def update_home_sidebar(posts_sorted):
    index_path = ROOT / "index.html"
    if not index_path.exists():
        return
    content = index_path.read_text(encoding="utf-8")
    new_recommend = build_home_recommend_html(posts_sorted)
    new_content = re.sub(r'(<ul class="recommend-list">).*?(</ul>)', rf'\1\n{new_recommend}\n                \2', content, flags=re.DOTALL)
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
    print(f"🔧 渲染器:     markdown-it-py (CommonMark)")
    print()

    if not POSTS_DIR.is_dir():
        print(f"❌ 找不到 {POSTS_DIR}"); sys.exit(1)

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    md_files = sorted([f for f in POSTS_DIR.glob("*.md") if not f.name.startswith("_")])
    if not md_files:
        print("❌ posts/ 下没有 .md 文件"); sys.exit(1)
    print(f"📄 发现 {len(md_files)} 个 Markdown 文件\n")

    posts = []
    for md_path in md_files:
        filename = md_path.name
        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text, filename)
        if meta is None:
            meta = {"title": md_path.stem, "date": datetime.now().strftime("%Y-%m-%d"), "tags": [], "excerpt": ""}
            body = text
        else:
            meta = validate_meta(meta, filename, body)

        meta["filename"] = filename
        posts.append(meta)
        log.ok(f"{filename} → \"{meta['title']}\" ({meta['date']}) tags={meta['tags']}")

    print()
    posts_sorted = sorted(posts, key=lambda p: str(p.get("date", "")), reverse=True)

    # index.json
    json_data = [{"filename": p["filename"], "title": p["title"], "date": p["date"],
                  "tags": p.get("tags", []), "excerpt": p.get("excerpt", "")} for p in posts_sorted]
    INDEX_JSON.write_text(json.dumps(json_data, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    log.ok(f"index.json 已生成（{len(json_data)} 篇）")

    # 渲染每篇文章
    for i, post in enumerate(posts_sorted):
        fname = post["filename"]
        md_path = POSTS_DIR / fname
        text = md_path.read_text(encoding="utf-8")
        _, body = parse_front_matter(text, fname)
        if not body:
            body = text

        # ★ 只解析一次，TOC 和 HTML 全部从 Token 流来
        html_body, toc = md_to_html(body, filename=fname)
        post["toc"] = toc

        # 验证
        h2_all = re.findall(r'<h2\b[^>]*>', html_body)
        h2_with_id = re.findall(r'<h2[^>]*id="([^"]+)"', html_body)
        toc_ids = [t["id"] for t in toc]
        if len(h2_all) != len(toc):
            log.err(f"[{fname}] <h2> 数量({len(h2_all)}) 与 TOC 条目({len(toc)}) 不一致！")
        elif h2_with_id != toc_ids:
            log.err(f"[{fname}] TOC 锚点顺序不匹配！")
        else:
            log.ok(f"[{fname}] TOC 锚点全部匹配 ({len(toc)} 个)")

        prev_p = posts_sorted[i + 1] if i + 1 < len(posts_sorted) else None
        next_p = posts_sorted[i - 1] if i - 1 >= 0 else None
        page = build_post_html(html_body, post, prev_p, next_p, toc, posts_sorted)

        slug = slugify(fname)
        out = HTML_DIR / f"{slug}.html"
        out.write_text(page, encoding="utf-8")
        log.ok(f"{fname} → html/{slug}.html")

    update_index_html(posts_sorted)
    update_home_sidebar(posts_sorted)

    sm = build_sitemap(posts_sorted)
    if sm:
        (ROOT / "sitemap.xml").write_text(sm, encoding="utf-8")
        log.ok("sitemap.xml 已生成")

    rb = ROOT / "robots.txt"
    if not rb.exists():
        rb.write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
        log.ok("robots.txt 已生成")

    print()
    if log.errors:
        print(f"❌ {len(log.errors)} 个错误")
        for e in log.errors: print(f"     {e}")
    if log.warnings:
        print(f"⚠️  {len(log.warnings)} 个警告")
    if not log.errors:
        print("\n🎉 构建完成，一切正常！")

if __name__ == "__main__":
    main()
    input()