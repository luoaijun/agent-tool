# Agent CLI

**Windows 桌面 AI 多模型任务运行器 · 多模型并行 · 本地语音（实验性） · 跨设备联动**

[![Version](https://img.shields.io/badge/version-v0.8.19-blue)](https://github.com/luoaijun/agent-tool/releases)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11%20x64-lightgrey)](https://github.com/luoaijun/agent-tool)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Agent CLI 是一款 Windows 桌面 AI 工具，支持同时运行多个 AI 模型（DeepSeek、OpenAI、Claude、Gemini 等），完成任务的分解、并行执行和结果汇总。内置本地语音引擎（实验性）、微信小程序授权，让你以最自然的方式与 AI 协作。

🌐 **在线预览**：[luoaijun.github.io/agent-tool](https://luoaijun.github.io/agent-tool/)

---

## 👤 作者

**罗爱军（全网同名：我和猫猫）** — 摄影爱好者，活跃于抖音、小红书、视频号、微博、公众号，搜索「我和猫猫」即可找到。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🤖 **多模型并行** | 同时运行多个 AI 模型，任务分解后并行执行，自动汇总结果 |
| 🎯 **智能路由** | 根据任务类型自动选择最佳模型（推理/视觉/快速），无需手动切换 |
| 🎙️ **本地语音** ⚠️ | Windows 原生语音引擎，无需联网即可语音输入和语音播报 · 当前体验欠佳，持续优化中 |
| 🔧 **工具调用** | AI 可直接读写文件、执行命令、搜索网络、操作代码 |
| 📎 **文件拖拽** | 拖入图片和文件，AI 自动分析内容 |
| ⚡ **任务队列** | 多任务排队执行，随时暂停/取消，项目间互不干扰 |
| 🔌 **插件系统** | Skill 插件扩展，自定义 AI 能力边界 |
| 🕐 **定时调度** | 设置定时任务，AI 按时自动执行并通知结果 |
| 📱 **跨设备联动** | 微信小程序扫码授权，手机端发起任务 |
| 🎨 **Markdown 渲染** | 对话内容支持 Markdown 实时渲染和代码语法高亮 |

---

## 📥 下载安装

### 最新版本：v0.8.19

👉 **[GitHub Releases 下载](https://github.com/luoaijun/agent-tool/releases)**

1. 前往 Releases 页面下载最新安装包 `Agent-CLI-Setup.exe`
2. 双击运行，选择安装路径
3. 安装完成后桌面会出现 Agent CLI 快捷方式
4. 启动软件，在设置中配置你的 API Key 即可使用

### 系统要求

- Windows 10/11 x64
- 需要配置 AI 模型 API Key（支持 DeepSeek、OpenAI、Claude、Gemini 等兼容 OpenAI 接口的模型）

---

## 🚀 快速上手

1. **配置 API Key**：打开设置 → 选择模型提供商 → 填入 API Key
2. **新建项目**：点击左上角项目选择器 → 新建项目
3. **开始对话**：在输入框输入任务描述，AI 会自动执行
4. **拖入文件**：直接把图片或文件拖入输入区，AI 会分析内容
5. **语音对话**：点击麦克风按钮，直接语音交流（实验性功能，持续优化中）

---

## 🔑 支持的模型提供商

| 提供商 | API 地址 | 获取 API Key |
|--------|----------|-------------|
| DeepSeek | `https://api.deepseek.com` | [platform.deepseek.com](https://platform.deepseek.com) |
| 小米 MiMo | `https://api.xiaomimimo.com/v1` | [mimo.xiaomi.com](https://mimo.xiaomi.com) |
| OpenAI | `https://api.openai.com/v1` | [platform.openai.com](https://platform.openai.com) |
| Anthropic Claude | `https://api.anthropic.com` | [console.anthropic.com](https://console.anthropic.com) |

也支持任何兼容 OpenAI API 接口的自定义模型服务。

---

## 📝 更新日志

### v0.8.19
- 多模型并行协作：任务自动分解 → 分发 → 汇总
- 智能模型路由：根据任务类型自动选择推理/视觉/快速模型
- 本地语音引擎（实验性）：Windows 原生 STT/TTS，无需外部 API
- 微信小程序联动：扫码授权，手机端发起和管理任务
- 定时调度：预设时间自动执行任务
- Skill 插件面板优化
- 设置页面布局改进
- 搜索自动展示最近对话

---

## ⚠️ 注意事项

- 需自备 AI 模型 API Key，本软件不提供内置 Key
- AI 执行文件操作时请留意权限确认弹窗
- 建议在重要项目中使用前先备份

---

**Made with ❤️ by 罗爱军（我和猫猫）**
