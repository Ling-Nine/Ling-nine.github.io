// 博客配置
const config = {
    postsPerPage: 10,
    postsDirectory: 'posts/',
    defaultPost: 'hello-world.md'
};

// 文章索引数据
let postsIndex = [];
let currentPostIndex = 0;

// DOM元素
const postsContainer = document.getElementById('posts-container');
const postContentElement = document.getElementById('post-content');
const postTitleElement = document.getElementById('post-title');
const postDateElement = document.getElementById('post-date');
const postTagsElement = document.getElementById('post-tags');
const prevPostLink = document.getElementById('prev-post');
const nextPostLink = document.getElementById('next-post');

// 初始化函数
async function init() {
    // 检查当前页面
    const path = window.location.pathname;

    if (path.includes('post.html')) {
        // 文章页面
        await loadPostsIndex();
        const postFile = getPostFromURL() || config.defaultPost;
        await loadPost(postFile);
        setupPostNavigation();
    } else {
        // 首页
        await loadPostsIndex();
        renderPostsList();
    }
}

// 加载文章索引
async function loadPostsIndex() {
    try {
        // 尝试从posts/index.json加载索引
        const response = await fetch(`${config.postsDirectory}index.json`);

        if (response.ok) {
            postsIndex = await response.json();
        } else {
            // 如果index.json不存在，则扫描posts目录
            console.warn('index.json not found, scanning posts directory...');
            await scanPostsDirectory();
        }

        // 按日期排序（最新的在前）
        postsIndex.sort((a, b) => new Date(b.date) - new Date(a.date));

    } catch (error) {
        console.error('Error loading posts index:', error);
        postsContainer.innerHTML = '<p class="loading">无法加载文章列表，请稍后再试。</p>';
    }
}

// 扫描posts目录（备用方案）
async function scanPostsDirectory() {
    // 预定义的文章列表（实际使用时可以手动维护或通过构建工具生成）
    postsIndex = [
        {
            filename: 'hello-world.md',
            title: 'Hello World - 我的第一篇博客',
            date: '2024-01-15',
            tags: ['随笔', '介绍'],
            excerpt: '欢迎来到我的个人博客！这是我使用Markdown编写的第一篇文章...'
        },
        {
            filename: 'my-first-post.md',
            title: 'Markdown博客搭建指南',
            date: '2024-01-10',
            tags: ['教程', '技术'],
            excerpt: '本文将介绍如何使用Markdown和GitHub Pages搭建个人博客...'
        }
    ];

    // 在实际应用中，这里可以添加更多文章
}

// 渲染文章列表到首页
function renderPostsList() {
    if (!postsContainer) return;

    if (postsIndex.length === 0) {
        postsContainer.innerHTML = '<p class="loading">暂无文章，请添加Markdown文件到posts目录。</p>';
        return;
    }

    let html = '';

    postsIndex.forEach((post, index) => {
        const postUrl = `post.html?post=${encodeURIComponent(post.filename)}`;
        const dateFormatted = formatDate(post.date);
        const tagsHtml = post.tags ? post.tags.map(tag => `<span class="tag">${tag}</span>`).join(' ') : '';

        html += `
            <article class="post-item">
                <h3><a href="${postUrl}">${post.title}</a></h3>
                <div class="post-meta">
                    <span>📅 ${dateFormatted}</span>
                    <span>🏷️ ${tagsHtml}</span>
                </div>
                <div class="post-excerpt">${post.excerpt || '点击阅读全文...'}</div>
                <a href="${postUrl}" class="read-more">阅读全文 →</a>
            </article>
        `;
    });

    postsContainer.innerHTML = html;
}

// 从URL获取文章文件名
function getPostFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('post');
}

// 加载并显示单篇文章
async function loadPost(filename) {
    try {
        // 查找文章索引
        const postIndex = postsIndex.findIndex(p => p.filename === filename);
        if (postIndex !== -1) {
            currentPostIndex = postIndex;
        }

        const response = await fetch(`${config.postsDirectory}${filename}`);

        if (!response.ok) {
            throw new Error(`Failed to load post: ${filename}`);
        }

        const markdown = await response.text();

        // 解析Markdown前部的元数据（YAML Front Matter）
        const { content, metadata } = parseFrontMatter(markdown);

        // 更新页面标题和元数据
        const title = metadata.title || postsIndex[currentPostIndex]?.title || '未命名文章';
        const date = metadata.date || postsIndex[currentPostIndex]?.date || '';
        const tags = metadata.tags || postsIndex[currentPostIndex]?.tags || [];

        document.title = `${title} - 我的博客`;

        if (postTitleElement) postTitleElement.textContent = title;
        if (postDateElement) postDateElement.textContent = `📅 ${formatDate(date)}`;
        if (postTagsElement) postTagsElement.textContent = `🏷️ ${tags.join(', ')}`;

        // 使用marked解析Markdown
        if (postContentElement) {
            postContentElement.innerHTML = marked.parse(content);

            // 为代码块添加复制按钮
            addCopyButtonsToCodeBlocks();
        }

    } catch (error) {
        console.error('Error loading post:', error);
        if (postContentElement) {
            postContentElement.innerHTML = `
                <div class="error">
                    <h2>文章加载失败</h2>
                    <p>无法加载文章 "${filename}"。请检查文件是否存在。</p>
                    <p>错误信息：${error.message}</p>
                    <a href="index.html">返回首页</a>
                </div>
            `;
        }
    }
}

// 解析Markdown前部的元数据
function parseFrontMatter(markdown) {
    const frontMatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n/;
    const match = markdown.match(frontMatterRegex);

    if (match) {
        const frontMatter = match[1];
        const content = markdown.slice(match[0].length);

        // 简单解析YAML格式的元数据
        const metadata = {};
        frontMatter.split('\n').forEach(line => {
            const colonIndex = line.indexOf(':');
            if (colonIndex > 0) {
                const key = line.slice(0, colonIndex).trim();
                let value = line.slice(colonIndex + 1).trim();

                // 移除引号
                if ((value.startsWith('"') && value.endsWith('"')) ||
                    (value.startsWith("'") && value.endsWith("'"))) {
                    value = value.slice(1, -1);
                }

                // 处理数组（简单情况）
                if (value.startsWith('[') && value.endsWith(']')) {
                    value = value.slice(1, -1).split(',').map(v => v.trim().replace(/['"]/g, ''));
                }

                metadata[key] = value;
            }
        });

        return { content, metadata };
    }

    return { content: markdown, metadata: {} };
}

// 设置文章导航
function setupPostNavigation() {
    if (!prevPostLink || !nextPostLink) return;

    // 上一篇
    if (currentPostIndex < postsIndex.length - 1) {
        const prevPost = postsIndex[currentPostIndex + 1];
        prevPostLink.href = `post.html?post=${encodeURIComponent(prevPost.filename)}`;
        prevPostLink.style.display = 'inline-block';
    } else {
        prevPostLink.style.display = 'none';
    }

    // 下一篇
    if (currentPostIndex > 0) {
        const nextPost = postsIndex[currentPostIndex - 1];
        nextPostLink.href = `post.html?post=${encodeURIComponent(nextPost.filename)}`;
        nextPostLink.style.display = 'inline-block';
    } else {
        nextPostLink.style.display = 'none';
    }
}

// 为代码块添加复制按钮
function addCopyButtonsToCodeBlocks() {
    const codeBlocks = document.querySelectorAll('pre code');

    codeBlocks.forEach(codeBlock => {
        const pre = codeBlock.parentElement;
        const button = document.createElement('button');

        button.className = 'copy-button';
        button.textContent = '复制';
        button.style.cssText = `
            position: absolute;
            top: 5px;
            right: 5px;
            background: #4a5568;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            opacity: 0.7;
            transition: opacity 0.3s;
        `;

        pre.style.position = 'relative';
        pre.appendChild(button);

        button.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(codeBlock.textContent);
                button.textContent = '已复制!';
                setTimeout(() => {
                    button.textContent = '复制';
                }, 2000);
            } catch (err) {
                console.error('复制失败:', err);
                button.textContent = '复制失败';
            }
        });

        button.addEventListener('mouseenter', () => {
            button.style.opacity = '1';
        });

        button.addEventListener('mouseleave', () => {
            button.style.opacity = '0.7';
        });
    });
}

// 格式化日期
function formatDate(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);

// 导出函数供其他脚本使用
window.BlogApp = {
    loadPost,
    formatDate,
    parseFrontMatter
};