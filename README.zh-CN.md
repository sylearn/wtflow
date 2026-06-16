# wtflow

一个 [Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)，教 AI 编程助手把 [Worktrunk](https://worktrunk.dev)（`wt`）用明白：开隔离 worktree、配 hooks 和 dev server、并行跑多个 Agent，以及安全地合并、清理。

[English](README.md)

![wtflow 演示](assets/demo.gif)

## 这是什么

`wt` 已经把机械动作做好了：创建 worktree、切换进去、跑 hooks、合并回来、清理掉。它不替你决定的，是**在真实仓库里这些动作该怎么组合**——hook 放哪、依赖安装要不要阻塞 `wt switch`、worktree 什么时候能删、怎么让两个 Agent 不去改同一个 checkout。

`wtflow` 就是这一层判断。它是给 Agent 看的操作知识，不是新的命令行工具，也不是对 `wt` 的封装。Agent 读完它，就能正确地用 Worktrunk，而不是瞎猜命令。

具体来说，它帮 Agent：

- 把配置放对位置——项目级 `.config/wt.toml` 还是个人级 `~/.config/worktrunk/config.toml`
- 为 setup、dev server、检查、合并、清理选对 hook
- 让多个 Agent（Claude Code、Codex、OpenCode）在隔离分支里并行干活，互不覆盖
- 配置 LLM 自动生成提交信息，且不把个人命令写进共享配置
- 任何破坏性操作先预览或 dry-run 再执行
- 排查 shell 集成、hook 失败、`wt list` 变慢等问题

## 前置条件

1. **Worktrunk（`wt`）**——这个 skill 操作的就是 `wt`，所以先装它并启用 shell 集成：

   ```bash
   # macOS / Linux
   cargo install worktrunk && wt config shell install
   # macOS（Homebrew）
   brew install worktrunk && wt config shell install
   # Windows（winget 会装成 git-wt）
   winget install max-sixty.worktrunk && git-wt config shell install
   ```

   其他安装方式见 [Worktrunk 安装文档](https://worktrunk.dev)。

2. **一个支持 skill 的 AI Agent**——Claude Code、Cursor、Codex 或 OpenCode。
3. **Git**——Worktrunk 跑在 Git worktree 之上。
4. **Python 3.8+**——仅探测脚本需要（通常由 Agent 自动运行）。

## 安装

把仓库克隆到你的 Agent 加载 skill 的目录：

```bash
# Claude Code（个人，所有项目）
git clone https://github.com/sylearn/wtflow.git ~/.claude/skills/worktrunk-workflows

# Claude Code（单个项目）
git clone https://github.com/sylearn/wtflow.git .claude/skills/worktrunk-workflows
```

Cursor、Codex、OpenCode 同理：放到对应 Agent 发现 skill 的位置，引用名 `worktrunk-workflows`。用 `git pull` 升级。

## 使用

直接用大白话说目标即可，不需要知道 `wt` 命令长什么样。示例：

**为仓库配置 Worktrunk**

```text
为这个仓库配置 Worktrunk，并创建保守的 .config/wt.toml。
把依赖安装、快速检查、合并前验证放到合适的阶段。
改文件前先说明方案。
```

**并行启动多个 Agent**

```text
启动两个隔离分支：
- feature-code-review：让 Claude 做 Code Review
- feature-docs：让 OpenCode 改进文档
直接启动这些 Agent，并告诉我每个分支在哪里运行。
```

**每个分支一个 dev server**

```text
为每个分支添加独立 dev server。
端口不要冲突，删除分支工作区时服务也要自动停止。
```

**安全清理**

```text
检查哪些工作区可以清理。
有未提交改动或状态不明确的内容不要删除。
```

## 工作原理

skill 激活后，Agent 走一个固定循环：

1. **探测**：用 `scripts/probe_worktrunk_project.py` 扫一遍仓库，识别包管理器、可用工具和已有配置。
2. **分类**：判断任务类型，只加载 `references/` 里对应的那一个文档。
3. **设计**：给出配置或命令，有风险的先预览再动手。
4. **验证**：用 `wt hook show --expanded`、`wt config alias dry-run` 或 `--dry-run` 校验。

## 项目结构

```text
wtflow/
├── SKILL.md                          # 入口：操作模型、安全规则、决策表
├── references/
│   ├── command-reference.md          # wt switch / list / merge / remove / step / hook / config
│   ├── config-hooks.md               # 配置文件、hooks、模板、过滤器、审批、状态
│   ├── recipes.md                    # dev server、数据库、缓存、tmux、Caddy、bare repo
│   ├── llm-agents.md                 # LLM 提交生成 + Claude / Codex / OpenCode
│   └── troubleshooting.md            # shell 集成、hook、LLM、list 变慢、Windows
├── scripts/
│   └── probe_worktrunk_project.py    # 零依赖仓库探测脚本 → JSON + 建议 hooks
├── agents/
│   └── openai.yaml                   # OpenAI / Codex skill 清单
├── README.md
├── README.zh-CN.md
└── LICENSE
```

`SKILL.md` 保持精简，只负责路由到 `references/`，让 Agent 按需加载。

## 开发

可以直接运行探测脚本；提 PR 前检查一下脚本：

```bash
python3 scripts/probe_worktrunk_project.py            # 探测当前仓库
python3 scripts/probe_worktrunk_project.py /path/repo # 探测其他仓库
python3 -m py_compile scripts/probe_worktrunk_project.py
uvx ruff check scripts/
```

## 许可证

MIT © 2026 Sylearn

## 致谢

本项目在 [LINUX DO](https://linux.do) 社区分享，感谢社区的支持与反馈。
