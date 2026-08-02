---
title: Git快速使用
date: 2026-08-02
tags: [技术, 介绍]
excerpt: Git的使用与常用命令
---

# Git的使用与常用命令

对于软件开发人员而言 Git 是日常工作中很重要的工具，不仅提高了开发的质量和效率，并且使得软件开发变得更加灵活、开放与协作。Git 不仅对软件开发人员有用，它的核心功能 — 版本控制 ，对于任何需要管理文档、项目或者创意作品的非开发人员也同样受益。

## 下载

官网下载地址：<https://git-scm.com/downloads>

## 初始配置

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

Git 的底层逻辑是文件在三个区域之间流转。

```
工作区(Working Directory) → 暂存区(Staging Area) → 本地仓库(Repository)
        你编辑文件               git add                git commit
```

## 本地仓库的基本用法

在已有项目目录里初始化

```bash
mkdir my-project && cd my-project
git init
```

或者直接克隆远程仓库到本地

```bash
git clone https://github.com/user/repo.git
```

本地仓库

```bash
# 查看状态
git status

# 关联远程仓库（clone 下来的仓库会自动关联 origin）
git remote add origin https://github.com/username/repo.git

# 暂存改动
git add 文件名      # 添加单个文件
git add .          # 添加当前目录所有修改

# 提交
git commit -m "清晰描述这次做了什么"

# 首次推送，-u 会把本地分支和远程分支绑定，下次直接 git push 就行
git push -u origin main
```

分支管理

```bash
git branch                # 查看本地分支（*表示当前分支）
git branch -v             # 查看本地分支及最新提交
git branch -r             # 查看远程分支
git branch -a             # 查看所有分支（本地 + 远程）

git branch dev            # 创建 dev 分支
git checkout dev          # 切换到 dev 分支（传统方式）
git switch dev            # 切换到 dev 分支（推荐，Git 2.23+）

git checkout -b dev       # 创建并切换（旧）
git switch -c dev         # 创建并切换（新，推荐）

git merge dev             # 将 dev 分支合并到当前分支
git merge --no-ff dev     # 禁用快进合并（保留分支历史，推荐）

git branch -d dev         # 删除已合并的本地分支
git branch -D dev         # 强制删除本地分支（未合并）

git push origin --delete dev   # 删除远程分支
git branch -dr origin/dev      # 删除远程分支（简写）
```

## 结语

感谢你阅读这篇文章！如果你有任何问题或建议，欢迎通过 [GitHub Issues](https://github.com/Ling-Nine/Ling-nine.github.io/issues) 与我交流。

---

*本文使用 Markdown 编写，最后更新于 2026年8月2日*