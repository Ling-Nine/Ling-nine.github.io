#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
build.py v6 - 全自动博客构建脚本

功能：
  1) 扫描 posts/*.md，从 YAML front matter 自动提取元数据
  2) 校验格式（title/date/tags/excerpt），出错明明白白提醒
  3) 自动生成 index.json（再也不用手写）
  4) 把每篇 .md 渲染成独立静态 HTML
     - 代码高亮（highlight.js，纯前端渲染，构建期不做高亮）
     - LaTeX 公式保护后原样保留，交给前端 MathJax 渲染
  5) 更新首页静态文章列表
  6) 生成 sitemap.xml（含 lastmod）+ robots.txt

原则：
  - 绝不修改 .md 源文件
  - excerpt 从纯 Markdown 正文提取，不依赖渲染结果

v5 新增：
  - LaTeX 公式保护机制：在 Markdown 渲染前把 $...$ / $$...$$ 公式
    替换为占位符，渲染完再还原，避免 \\ & 等被 Markdown 破坏

v6 新增：
  - excerpt 改为从纯 Markdown 源提取（剥离公式/代码/标记后取前80字）
  - 移除 codehilite 后端高亮，统一交给前端 highlight.js
  - sitemap.xml 每篇 URL 补充 <lastmod> 字段

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

# ── 路径配置 ────────────────────────────────────────
if len(sys.argv) > 1:
    ROOT = Path(sys.argv[1]).resolve()
else:
    ROOT = Path(__file__).resolve().parent

POSTS_DIR = ROOT / "posts"
INDEX_JSON = POSTS_DIR / "index.json"
SITE_URL = os.environ.get("SITE_URL", "https://ling-nine.github.io").rstrip("/")

# ── Markdown 配置 ────────────────────────────────────
# 注意：不加 "toc"，避免给标题自动加 id 时和 MathJax 冲突
# 注意：不加 "codehilite"，代码高亮完全交给前端 highlight.js
MD_EXTENSIONS = ["extra", "fenced_code", "tables"]
MD_EXT_CONFIG = {}

DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# ═══════════════════════════════════════════════════
#  日志
# ═══════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════
#  Front Matter 解析
# ═══════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════
#  从纯 Markdown 源提取 excerpt（不依赖渲染结果）
# ═══════════════════════════════════════════════════
def _extract_excerpt_from_markdown(body, max_len=80):
    """
    步骤：
      1) 去掉 YAML front matter（如有）
      2) 去掉代码块（```...``` 和缩进代码块）
      3) 去掉行内代码 `...`
      4) 去掉 LaTeX 公式 $...$ / $$...$$
      5) 去掉 HTML 标签
      6) 去掉 Markdown 标记符号
      7) 合并空白，截取前 max_len 字符
    """
    text = body

    # 1) 去掉 front matter
    text = re.sub(r'^---\s*\n.*?\n---\s*\n?', '', text, flags=re.DOTALL)

    # 2) 去掉代码块（```...```）
    text = re.sub(r'```.*?```', ' ', text, flags=re.DOTALL)
    # 缩进代码块（行首 4 空格或 1 tab 开头）
    text = re.sub(r'(?m)^( {4,}|\t+).*$', ' ', text)

    # 3) 去掉行内代码
    text = re.sub(r'`[^`]+`', ' ', text)

    # 4) 去掉 LaTeX 公式
    text = re.sub(r'\$\$.*?\$\$', ' ', text, flags=re.DOTALL)  # 块级
    text = re.sub(r'\$[^$\n]+?\$', ' ', text)                   # 行内
    text = re.sub(r'\\[\(\[].*?\\\)[\])]', ' ', text, flags=re.DOTALL)  # \(...\) \[...\]

    # 5) 去掉 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', text)

    # 6) 去掉 Markdown 标记符号
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'!\[.*?\]\(.*?\)', ' ', text)   # 图片
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 链接 → 保留文字
    text = re.sub(r'[*_~]', '', text)               # 强调符号
    text = re.sub(r'^[\->*\d+\.]\s*', '', text, flags=re.MULTILINE)  # 列表/引用
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)  # 水平线

    # 7) 清理空白并截断
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len].rstrip() + '...'
    return text

# ═══════════════════════════════════════════════════
#  格式校验
# ═══════════════════════════════════════════════════
def validate_meta(meta, filename, body):
    c = dict(meta)

    # title
    if "title" not in c or not str(c["title"]).strip():
        log.err(f"[{filename}] 缺少 title 字段")
        c["title"] = Path(filename).stem
    else:
        c["title"] = str(c["title"]).strip()

    # date
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

    # tags
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

    # excerpt：从纯 Markdown 源提取，绝不依赖渲染结果
    if "excerpt" not in c or not str(c["excerpt"]).strip():
        exc = _extract_excerpt_from_markdown(body)
        log.info(f"[{filename}] 自动 excerpt: {exc[:50]}...")
        c["excerpt"] = exc
    else:
        c["excerpt"] = str(c["excerpt"]).strip()

    return c

# ═══════════════════════════════════════════════════
#  LaTeX 公式保护 / 还原
# ═══════════════════════════════════════════════════
_MATH_PATTERN = re.compile(r'(\$\$.*?\$\$|\$.*?\$|\\[\(\[].*?\\\)[\])])', re.DOTALL)

def protect_math(text):
    """把文本中的 LaTeX 公式替换为占位符，返回 (新文本, 公式列表)"""
    store = []
    def repl(match):
        formula = match.group(0)
        token = f"\x00MATH{uuid.uuid4().hex}\x00"
        store.append((token, formula))
        return token
    protected = _MATH_PATTERN.sub(repl, text)
    return protected, store

def restore_math(text, store):
    """把占位符还原为原始 LaTeX 公式"""
    for token, formula in store:
        text = text.replace(token, formula)
    return text

# ═══════════════════════════════════════════════════
#  Markdown → HTML
# ═══════════════════════════════════════════════════
def md_to_html(body):
    protected, math_store = protect_math(body)
    html = md.markdown(protected, extensions=MD_EXTENSIONS, extension_configs=MD_EXT_CONFIG)
    html = restore_math(html, math_store)
    return html

# ═══════════════════════════════════════════════════
#  工具
# ═══════════════════════════════════════════════════
def slugify(name):
    return re.sub(r"\.md$", "", name, flags=re.I)

def format_date(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").strftime("%Y年%-m月%-d日")
    except ValueError:
        return str(s)

# ═══════════════════════════════════════════════════
#  MathJax 注入脚本（前端渲染 LaTeX）
# ═══════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════
#  HTML 模板
# ═══════════════════════════════════════════════════
def build_post_html(post_html, meta, prev_post=None, next_post=None):
    title = meta["title"]
    date = meta["date"]
    tags = meta.get("tags", [])
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

    prev_href = f"../posts/{slugify(prev_post['filename'])}.html" if prev_post else "#"
    next_href = f"../posts/{slugify(next_post['filename'])}.html" if next_post else "#"
    prev_text = f"← {prev_post['title']}" if prev_post else "← 上一篇"
    next_text = f"{next_post['title']} →" if next_post else "下一篇 →"

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 我的博客</title>
    <meta name="description" content="{meta.get('excerpt', '')}">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{meta.get('excerpt', '')}">
    <meta property="og:type" content="article">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=ZCOOL+XiaoWei&display=swap">
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/vs.min.css">
    <link rel="icon" type="image/x-icon" href="../favicon.ico">
    {MATHJAX_SCRIPT}
</head>
<body>
    <header>
        <nav class="container">
            <div class="logo">
                <a href="../index.html" class="logo-link">
                    <img class="logo-avatar" src="../posts/images/test/头像.png" alt="avatar">
                    <span class="logo-text">彾九平</span>
                </a>
            </div>
            <ul class="nav-links">
                <li><a href="../index.html">首页</a></li>
                <li><a href="../index.html#about">关于</a></li>
                <li><a href="../links/index.html">友链</a></li>
                <li><a href="../index.html#contact">联系</a></li>
            </ul>
        </nav>
    </header>

    <main class="container">
        <article class="post-container">
            <div class="post-header">
                <h1 id="post-title">{title}</h1>
                <div class="post-meta">
                    <span>📅 {format_date(date)}</span>
                    <span>🏷️ {tags_str}</span>
                </div>
            </div>
            <div class="post-content" id="post-content">
{post_html}
            </div>
            <div class="post-navigation">
                <a href="{prev_href}">{prev_text}</a>
                <a href="../index.html">返回首页</a>
                <a href="{next_href}">{next_text}</a>
            </div>
        </article>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2026 我的个人博客 | <a href="../index.html">返回首页</a></p>
        </div>
    </footer>

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
</body>
</html>"""

def build_index_html(posts_sorted):
    items = []
    for p in posts_sorted:
        slug = slugify(p["filename"])
        href = f"posts/{slug}.html"
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

def build_sitemap(posts_sorted):
    if not SITE_URL:
        return None
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines.append(f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod></url>")
    # 友链页面也加入 sitemap
    lines.append(f"  <url><loc>{SITE_URL}/links/index.html</loc><lastmod>{today}</lastmod></url>")
    for p in posts_sorted:
        slug = slugify(p["filename"])
        url = f"{SITE_URL}/posts/{slug}.html"
        lastmod = p.get("date") or today
        lines.append(f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>")
    lines.append("</urlset>")
    return "\n".join(lines)

# ═══════════════════════════════════════════════════
#  首页更新
# ═══════════════════════════════════════════════════
def update_index_html(posts_sorted):
    index_path = ROOT / "index.html"
    if not index_path.exists():
        log.warn("找不到 index.html，跳过首页更新")
        return
    content = index_path.read_text(encoding="utf-8")
    new_list = build_index_html(posts_sorted)
    new_content = re.sub(
        r'(<div id="posts-container">).*?(</div>\s*</section>)',
        rf'\1{new_list}\2',
        content, flags=re.DOTALL
    )
    if "正在加载文章" in new_content and "post-item" not in new_content:
        new_content = new_content.replace(
            '<div class="loading">正在加载文章...</div>',
            new_list
        )
    index_path.write_text(new_content, encoding="utf-8")
    log.ok("首页 index.html 已更新")

# ═══════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════
def main():
    print(f"📂 项目根目录: {ROOT}")
    print(f"📂 文章目录:   {POSTS_DIR}")
    print(f"🌐 站点 URL:   {SITE_URL}")
    print()

    if not POSTS_DIR.is_dir():
        print(f"❌ 找不到 {POSTS_DIR}")
        sys.exit(1)

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

        meta["filename"] = filename
        posts.append(meta)
        log.ok(f"{filename} → \"{meta['title']}\" ({meta['date']}) tags={meta['tags']}")

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

        html_body = md_to_html(body)

        prev_p = posts_sorted[i + 1] if i + 1 < len(posts_sorted) else None
        next_p = posts_sorted[i - 1] if i - 1 >= 0 else None

        page = build_post_html(html_body, post, prev_p, next_p)

        slug = slugify(fname)
        out = POSTS_DIR / f"{slug}.html"
        out.write_text(page, encoding="utf-8")
        log.ok(f"{fname} → posts/{slug}.html")

    # ── 首页 ──
    update_index_html(posts_sorted)

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
