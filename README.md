# YT-Street-Echoes 🎙️

> 捕捉 YouTube 街头回音，打造专属的英语语料日历档案馆。

**YT-Street-Echoes** 是一个基于 Python 和 GitHub Actions 构建的静态 WebApp 自动化工具。它不仅能定期自动抓取全美 YouTube 各大版块的热门视频和高价值评论，还提供了一个强大的纯前端控制台：支持直接粘贴链接生成“单集精读”，并利用 GitHub API 实现页面的无缝更新与云端文件的彻底删除。

---

## ✨ 核心亮点

* 🤖 **自动化“打工人”**: 配置 GitHub Actions 定时触发（默认每周一早 8:00），全自动执行抓取、生成静态 HTML 并提交推送。
* 📅 **纯静态日历枢纽**: 页面存放在 `docs/` 目录下，完美适配 GitHub Pages。按年月归档，双击日历区域可一键唤出“删除模式”。
* 💬 **原生级 UI 体验**: 生成的视频页面内置仿 iOS 原生聊天气泡的评论区 UI，带双重折叠设计，阅读体验极佳。
* ⚡ **无服务器前端直写**: 网页前端输入链接，通过浏览器的 JS 搭配 GitHub Personal Access Token (PAT)，直接将生成的静态页面推送到 GitHub 仓库，页面不刷新即可看到新日历项。
* 🗑️ **云端彻底清理**: 面板上删除某一天的数据时，不仅抹除 JSON 索引，还会直接向仓库发送 `DELETE` 请求，物理销毁无用 HTML，绝不堆积垃圾。

---

## 🚀 部署与使用指南

### 1. 准备工作
* Fork 本仓库到你的个人账号下。
* 前往 [Google Cloud Console](https://console.cloud.google.com/) 申请一个 **YouTube Data API v3** 的密钥（API Key）。
* 前往 GitHub 的 Developer settings 生成一个 **Personal Access Token (classic)**，勾选 `repo` 权限（用于前端写入和删除文件）。

### 2. 投喂打工人 (配置 Secrets & 权限)
为了让 GitHub Actions 有权限抓取数据并提交代码：
1.  进入仓库的 `Settings` -> `Secrets and variables` -> `Actions`。
2.  新建一个 Repository secret，名称必须为 `YOUTUBE_API_KEY`，填入你申请的 YouTube API 密钥。
3.  进入 `Settings` -> `Actions` -> `General`，拉到最下方找到 **Workflow permissions**，确保勾选了 **`Read and write permissions`**。

### 3. 开启 GitHub Pages
* 进入 `Settings` -> `Pages`。
* 在 Build and deployment 中，Source 选择 `Deploy from a branch`。
* Branch 选择 `main`，文件夹选择 **`docs/`**，点击 Save。

### 4. 前端本地配置中心 ⚙️
部署完成后，打开你的 GitHub Pages 链接：
1.  点击页面右上角的齿轮 ⚙️ 图标。
2.  依次填入你的：
    * **YouTube API Key** * **GitHub Personal Access Token**
    * **GitHub 用户名**
    * **GitHub 仓库名** (例如 `YT-Street-Echoes`)
3.  点击“保存配置”。（⚠️ *放心，配置仅保存在你当前浏览器的 LocalStorage 中，绝不上传第三方服务器*）。

---

## 🛠️ 工作流说明 (Workflow)

本项目内置了 GitHub Actions 工作流，触发逻辑如下：

```yaml
on:
  schedule:
    - cron: '0 0 * * 1'  # 自动：每周一北京时间早上 8:00 (UTC 00:00) 运行，生成“📌 每周热播”
  workflow_dispatch:     # 手动：允许在 GitHub Actions 网页端手动点击运行