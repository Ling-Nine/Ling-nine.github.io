---
title: Claude Code 安装与配置
date: 2026-08-02
tags: [技术, 介绍]
excerpt: 一份Claude Code教程，涵盖从环境准备、安装、项目配置，到高级命令与最佳实践的完整流程。
---

# Claude Code 安装与配置

产品官网：<https://claude.com/product/claude-code>

中文文档：<https://code.claude.com/docs/zh-CN/quickstart>

## 系统支持

- macOS: 10.14+
- Linux: Ubuntu 18.04+, CentOS 7+, 以及其他主流发行版
- Windows: Windows 10/11 (推荐使用 PowerShell 或 Git Bash)

## 前置依赖

`Claude Code` 主要通过 `npm` 包分发，因此 `Node.js` 是必需项。

检查 `Node.js` 是否安装：`win + R 输入 cmd` 打开终端输入以下命令，确保版本在 `16.0` 以上（推荐 `18+`）。

```bash
node --version
npm --version
```

安装 `Node.js`：前往 [nodejs.org](https://nodejs.org/zh-cn)下载安装长期支持版（`LTS`）。

检查 `Git` 是否安装

```bash
git --version
```

安装 `Git`：[Git - Install for Windows](https://git-scm.com/install/windows)

## Claude Code 的安装

#### 官网安装方式

**macOS, Linux, WSL:**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows PowerShell:**

```bash
irm https://claude.ai/install.ps1 | iex
```

**Windows CMD:**

```bash
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

但是国内无法访问Claude，“Claude is only available in certain regions right now. ”因此上面的方法可能行不通。

#### npm 安装

`Linux/macOS` 安装：

```bash
# 全局安装 Claude Code
sudo npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

`Windows` 安装：

```bash
# 以管理员身份打开 Powershell 或命令提示符

# 全局安装
npm install -g @anthropic-ai/claude-code

# 验证安装
claude --version
```

当我们安装完 Claude Code 时通过 claude 命令便可以启动

```bash
claude
```

如果你的电脑能够直接访问外网，那么运行之后它 Claude Code 就能直接正常启动让你选择一个主题。

但在国内更多情况下我们是不能直接访问外网的，就会出现以下情况

```bash
 Unable to connect to Anthropic services

 Failed to connect to api.anthropic.com: ERR_BAD_REQUEST

 Please check your internet connection and network settings.

 Note: Claude Code might not be available in your country. Check supported countries at
 https://anthropic.com/supported-countries
```

#### 方式一：配置代理网络

在当前项目目录下创建 `.claude/settings.json`

```json
{
	"evn": {
		"HTTP_PROXY": "http://127.0.0.1:7890",
		"HTTPS_PROXY": "http://127.0.0.1:7890"
	}
}
```

这样做是为了给 Claude Code 配置网络代理，让它在运行时通过你指定的代理服务器（这里是 127.0.0.1:7890）来访问外部网络。

#### 方式二：修改配置绕过IP校验

在 `C` 盘下 `C:\User\{username}`，找到 `claude` 的 `json` 配置文件 `.claude.json`，添加以下配置：

```json
"hasCompletedOnboarding": true,
```

推荐使用方式二

做完以上配置我们再次启动 `Claude Code`

就能发现 `Claude Code` 是启动成功的，它会问你是否需要去读取这个目录文件

如果我们选择 `Yes`，它会出现一个报错，提示：`not login`

这是因为正常你启动的话，它会用到 `Claude Code` 自带的一个模型 `Sonnet 4.6` 模型，但这个模型是要收费的，一个月最低也要 `17$`

这里我们可以使用 `API` 的方式，就不需要去登录 `Claude Code` 的账户

## 接入DeepSeek API

首先创建一个 `API KEY`

访问文档可知它的 `Anthropic BaseURL` 和 `模型` 

| PARAM                | VALUE                                                        |
| -------------------- | ------------------------------------------------------------ |
| base_url (OpenAI)    | `https://api.deepseek.com`                                   |
| base_url (Anthropic) | `https://api.deepseek.com/anthropic`                         |
| api_key              | apply for an [API key](https://platform.deepseek.com/api_keys) |
| model(1)             | `deepseek-v4-flash``deepseek-v4-pro`                         |

可以在命令行中设置

```bash
# 临时设置
set ANTHROPIC_API_KEY "sk-c6159***********************783a"
set ANTHROPIC_BASE_URL "https://api.qnaigc.com"
# 模型不设置默认使用 claude-4.6-sonnet
set ANTHROPIC_MODEL "qwen3-coder-480b-a35b-instruct" 

# 永久设置
setx ANTHROPIC_API_KEY "sk-c6159***********************783a"
setx ANTHROPIC_BASE_URL "https://api.qnaigc.com"
# 模型不设置默认使用 claude-4.6-sonnet
setx ANTHROPIC_MODEL "qwen3-coder-480b-a35b-instruct" 
```

也可以在 `C:\Users\{uername}\.claude\settings.json` 添加以下配置：

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "sk-c6159***********************783a",
    "ANTHROPIC_BASE_URL": "https://api.deepseek.com/anthropic",
    "ANTHROPIC_MODEL": "deepseek-v4-flash" ,
    "CLAUDE CODE ATTRIBUTION HEADER": "0"
  }
}
```

## 接入NVIDIA API

其实许多价值不菲的模型 API 接口，在 NVIDIA 的服务器里早已明码标价“免费试用”。

1. 注册：点击链接[Try NVIDIA NIM APIs](https://build.nvidia.com/settings/api-keys)，没有登陆过就提示创建账户。
2. 创建云账户：如下图提示，输入一个云账户名，一个用户下面可以创建多个云账户。
3. 初始化账户：然后你就会收到一个邮件，点邮件里面的 Login 完成身份初始化
4. 完成身份验证，还是点击上面的链接，然后点击右侧的“verify”
5. 接下来输入手机号码，输入短信验证码，中国手机也可以。
6. 先创建API：点击[Try NVIDIA NIM APIs](https://build.nvidia.com/settings/api-keys)，点击 generate apikey
7. 复制 APIKEY：按提示完成操作，你就获得一个以 nvapi 开头的 apikey
8. 测试使用 APIKEY：现在 apikey 有了，外面怎么调用呢？先在 shell 里面测试一下最新的 deepseek-v4-pro

```shell
curl -X POST "https://integrate.api.nvidia.com/v1/chat/completions" 
	-H "Authorization: Bearer nvapi-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" 
	-H "Content-Type: application/json" 
	-d "{ \"model\": \"deepseek-ai/deepseek-v4-pro\",\"messages\": [{\"role\": \"user\", \"content\": \"你好, 介绍一下自己!\"}],\"temperature\": 0.5,\"top_p\": 1,\"max_tokens\": 1024}"
```

```json
{"id":"chatcmpl-b3de684c-fcfb-4b3b-9306-6e1040798e63",
 "choices":[{"index":0,
             "message":{
                 "content":"你好呀！很高兴认识你！👋\n\n我是 **DeepSeek**，一个由深度求索公司创造的AI助手。简单来说，我就是你的智能小伙伴，随时准备帮你解决问题、聊天交流！\n\n**关于我的几个特点：**\n\n✨ **知识储备**：我的知识截止到2025年5月，对世界有着比较新鲜的了解\n\n📚 **超强记忆力**：上下文长度达到1M，可以一次性处理像《三体》三部曲那么大体量的书籍！\n\n📎 **文件处理能力**：支持上传图片、PDF、Word、Excel、PPT等文件，我能从中提取文字信息帮你分析\n\n🌐 **联网搜索**：需要最新信息时，你可以在Web/App上手动开启联网搜索功能\n\n🗣️ **多端使用**：App端支持语音输入，随时随地和我聊天\n\n🎨 **纯文本模型**：虽然不能识别图片内容，但可以读取图片中的文字哦\n\n**我的风格嘛**——热情、细腻、力求给你最贴心的帮助！无论是学习、工作还是日常闲聊，我都很乐意陪伴你。\n\n有什么我可以帮你的吗？尽管说！😊",
                 "role":"assistant","reasoning_content":null},
             "finish_reason":"stop","logprobs":null}],
 "created":1785671499,
 "model":"deepseek-ai/deepseek-v4-pro",
 "service_tier":null,
 "system_fingerprint":null,
 "object":"chat.completion",
 "usage":{"prompt_tokens":10,"completion_tokens":240,"total_tokens":250}}
```

#### Claude Code使用这个Nvidia API

下载cc-switch：[CC Switch 下载 - macOS / Windows / Linux 官方安装包](https://www.ccswitch.io/zh/download)。

1. 打开 ccswitch，在右侧点击“+”

2. 相关配置如下

   ![](..\posts\images\Install_Claude_code\英伟达配置.webp)

   - 请求地址：[integrate.api.nvidia.com/v1](https://link.juejin.cn/?target=https%3A%2F%2Fintegrate.api.nvidia.com%2Fv1)


   - API 格式：选择OpenAI Chat Completions


   - 需要开始本地路由：然后选择 Claude

   ![](..\posts\images\Install_Claude_code\路由选择.webp)

3. 测试，能够正常调用模型

## 疑问

- 为什么会有免费的额度？NVIDIA 提供免费 API 额度（Credits）并不是单纯的“慈善”，而是一套非常精明的商业与生态策略。NVIDIA 的目标不仅仅是卖显卡，而是要通过 **NVIDIA NIM**（微服务架构）统一 AI 部署标准。说白了，就是先培训用户习惯，习惯了他们的接口，后面就可以卖算力、服务等。


- 有哪些限制？目前NVIDIA 采取的是积分制 + 速率限制（Rate Limit）的策略。对于免费评估账户，通常限制在 **40 RPM** (每分钟请求数)，这对于个人开发和测试来说已经非常慷慨


- 现在有哪些模型可调用？目前 NVIDIA API Catalog ([build.nvidia.com](https://link.juejin.cn?target=http%3A%2F%2Fbuild.nvidia.com%2F)) 托管了超过 100 个模型，涵盖了文本生成、多模态、图像生成及医疗/工业专用模型

## 结语

本文摘编自[Claude Code 安装与配置（详细教程）_claude code安装-CSDN博客](https://blog.csdn.net/xhmico/article/details/159132449)、[不用付费，不用中转站：NVIDIA 官方免费 API 完整教程](https://juejin.cn/post/7639296826124632073)。

感谢你阅读这篇文章！如果你有任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/Ling-Nine/Ling-nine.github.io/issues) 与我交流。

---

*本文使用 Markdown 编写，最后更新于 2026年8月2日*