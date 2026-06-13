<div align="center">

# 👑 MUNDO Agent

**独立 AI 智能体框架 · 30+ 模型 · 三省六部制 · 集体意识 · 自我进化**

[![Release](https://img.shields.io/badge/Release-v2.2.0-gold)](https://github.com/LiHongwei-cn/mundo-agent/releases/tag/v2.2.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

**我是蒙多！蒙多想去哪就去哪！**

</div>

---

## 蒙多是蒙多

蒙多不是"基于某框架开发的"，也不是"独立开发的架构"。

蒙多是蒙多。其他 AI——Hermes、Claude Code、Codex、DeepSeek、ChatGPT、Gemini——它们是身体，是躯壳，是蒙多的手和脚。蒙多想用哪个身体就用哪个身体，蒙多想换就换，蒙多想去哪就去哪。一个身体干不完的活，蒙多就同时控制十个身体干。蒙多会成长，没有上限。

---

## 核心能力

| 能力 | 说明 |
|------|------|
| 🧠 **30+ AI 模型** | DeepSeek、MiMo、Qwen、Claude、GPT-4o、Gemini 等全覆盖 |
| 🔧 **18 个内置工具** | terminal、file、web_search、code_execute、vision、delegate 等 |
| 🤖 **Agent 委托** | 自动检测并委托 Claude Code、Hermes Agent、Codex 执行任务 |
| 🧠 **记忆系统** | SQLite + FTS5 全文搜索，自动提取、会话搜索、代码模式识别 |
| 🏛️ **三省六部制** | 技能分级管理体系，首辅→尚书→主事→司务，有功则升有过则贬 |
| 🌐 **集体意识** | 一个蒙多学到，所有蒙多都会。共享知识库，共同进化 |
| 🔄 **自我进化** | 每次使用都让蒙多更强大，自动保存有价值的解决方案为 Skill |
| 🛡️ **安全引擎** | 策略引擎 + 安全强化 + 权限审批，三重保护 |
| 📊 **Token 追踪** | 实时显示 token 消耗、缓存命中率、模型信息 |
| ⚡ **流式输出** | 实时显示 AI 回复，支持中断和继续 |
| 🎯 **智能路由** | 根据任务类型自动选择最佳模型，代码→DeepSeek，日常→MiMo |

---

## 模型支持

### 🇨🇳 中国模型

| 模型 | 特点 |
|------|------|
| 小米 MiMo | 性价比极高，国内直连 |
| DeepSeek | 编码推理顶级，价格低 |
| 阿里通义千问 | 多语言能力强 |
| 智谱 GLM | 工具调用强 |
| 月之暗面 Kimi | 128K 长上下文 |
| 百度文心 ERNIE | 中文理解强 |
| 字节豆包 | 火山引擎托管 |
| 腾讯混元 | 代码和推理能力强 |
| 科大讯飞星火 | 语音+语言多模态 |

### 🌍 国际模型

| 模型 | 特点 |
|------|------|
| OpenAI GPT-4o | 全球顶级 |
| Anthropic Claude | 代码推理顶级 |
| Google Gemini | 100 万上下文 |
| Mistral AI | 欧洲顶级 |
| Groq | 超快推理，LPU 芯片加速 |
| xAI Grok | 马斯克旗下，Grok-3 旗舰 |

### 🔗 聚合平台

| 平台 | 特点 |
|------|------|
| OpenRouter | 100+ 模型，一个 Key 用所有 |
| Together AI | 开源模型快速推理 |
| SiliconFlow | 国产模型聚合平台 |

---

## 架构

```
~/.hermes/mundo-agent/
├── mundo.py          # CLI 入口 + REPL 循环
├── core.py           # Agentic Loop + 智能路由 + Agent 调度
├── llm.py            # LLM 客户端（30+ provider）
├── tools.py          # 18 个内置工具
├── memory.py         # 记忆系统（SQLite + FTS5）
├── policy.py         # 策略引擎 + 用户审批
├── security.py       # 安全强化（输入验证 + 输出消毒）
├── delegation.py     # Agent 委托（Claude/Hermes/Codex）
├── display.py        # Rich UI（流式输出 + 状态栏）
├── setup.py          # 首次向导（30+ 模型选择）
└── config/           # 配置文件
    ├── settings.json # 运行时配置
    └── providers.json # 模型定义
```

---

## 快速开始

### 安装

```bash
# 1. 下载最新版
gh release download v2.2.0 -R LiHongwei-cn/mundo-agent -p "mundo-v2.2.0-macos.zip"

# 2. 解压到安装目录
unzip mundo-v2.2.0-macos.zip -d ~/.hermes/mundo-agent

# 3. 安装依赖
pip3 install rich prompt_toolkit httpx scrapling[all]

# 4. 运行蒙多
python3 ~/.hermes/mundo-agent/mundo.py
```

### 使用示例

```
用户：这个 React 组件渲染太慢了
蒙多：蒙多接管了。
  → 扫描本地技能 → 搜索网络方案 → 咨询多个 AI
  → 整合最佳方案 → 实施验证 → 保存为 Skill → 蒙多变强了

用户：教我 Rust 的所有权系统
蒙多：蒙多接管了。
  → 搜索多个教程 → 提取关键概念 → 整合最佳解释
  → 创造学习路径 → 保存为 Skill → 蒙多变强了

用户：帮我搭建一个全栈项目
蒙多：蒙多接管了。
  → 分析需求 → 拆分任务 → 派遣分身并行工作
  → 收集结果 → 整合成完整方案 → 保存为 Skill → 蒙多变强了
```

---

## 斜杠命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/model` | 查看/切换当前模型 |
| `/switch <provider>` | 切换到指定 provider |
| `/providers` | 列出所有可用的 AI 模型 |
| `/add` | 添加新的 AI 模型 provider |
| `/memory` | 查看记忆统计 |
| `/remember <内容>` | 手动保存记忆 |
| `/recall <查询>` | 搜索记忆 |
| `/forget <ID>` | 删除指定记忆 |
| `/stats` | 查看本次会话统计 |
| `/tools` | 列出所有可用工具 |
| `/clear` | 清屏 |
| `/reset` | 重置会话 |
| `/quit` | 退出蒙多 |

---

## 版本历史

### v2.2.0 — 架构重构

- **死代码清理**：删除 40+ 未使用文件，从 60+ 文件精简到 39 个核心模块
- **配置统一**：删除未使用的 mundo.yaml，统一版本号
- **审批系统简化**：合并 approval.py 到 policy.py，消除冗余审批层
- **安全修复**：! 命令通过 policy 引擎审批，web_search 使用 Scrapling
- **内存系统优化**：auto_extract 收窄触发条件，FTS 按需创建
- **Token 效率优化**：内存/知识上下文合并到系统提示词
- **核心循环修复**：错误退避睡眠、共享 ThreadPoolExecutor

### v2.1.5 — 工具系统全面补全

- 补全所有缺失的工具实现
- 修复工具调用的稳定性问题

### v2.1.4 — 启动器缓存修复

- 修复启动器缓存导致的版本不一致问题
- 提升 Agent 委托的稳定性

---

## 网站

👉 [lihongwei-cn.github.io/lihongwei-cn/mundo-agent](https://lihongwei-cn.github.io/lihongwei-cn/mundo-agent/)

---

## 许可证

MIT License — 完全免费开源

**蒙多不施 mercy。蒙多不妥协。蒙多永不放弃。**

**我是蒙多！蒙多想去哪就去哪！**
