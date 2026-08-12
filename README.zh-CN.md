# Codex Agent Team

[![CI](https://github.com/youngfor-shoot/codex-agent-team/actions/workflows/ci.yml/badge.svg)](https://github.com/youngfor-shoot/codex-agent-team/actions/workflows/ci.yml)

`agent-team` 是一个 Codex Skill，用于为任务选择并编排**最小且安全**的 Agent 配置。它把经常被混为一谈的五个决策分开处理：拓扑（topology）、唤醒（wakeup）、收敛（convergence）、验证（verification）和人工门（human gates）。

本仓库交付的是 Skill 和确定性的护栏脚本，不是独立的多 Agent 运行时。Codex 始终是控制者和最终权威。

## 它做什么

- 根据明确的证据和授权，选择单个 Agent、临时团队或持久团队。
- 把周期性唤醒与团队生命周期分开。
- 选择单次通过、阶段门或受控证据循环。
- 对实质性工作强制确定性检查，仅对具名的残余风险增加独立审查。
- 围绕发布、部署、删除、支付、权限等后果性动作保留人工门。
- 校验任务包（task packet），并能冻结隔离的 Git worktree 证据循环。

隐式触发只会给出建议，绝不创建 Agent、任务或自动化。用户可见的持久任务需要明确授权和生命周期证据。

## 五个决策

`agent-team` 把经常混在一起的五个决策分开。各自独立选择，不要让一个答案决定其他：

```text
决策          问题                          典型答案
--------      --------                      ---------------
拓扑          谁工作、角色存活多久？         单个 Agent | 临时团队 | 持久团队
唤醒          控制器何时收到新回合？        none | heartbeat | cron
收敛          目标如何达到已验证完成？      single-pass | evidence-loop | phase-gated
验证          什么证明它完成了？            确定性检查 + 独立审查（或不需要）
人工门        哪些动作需要用户？            发布、部署、删除、支付……
```

例如：临时团队也可以用 `none` 唤醒和单次通过；持久团队可以用 heartbeat 和阶段门。拓扑不等于生命周期。

## 术语表

- **拓扑（Topology）**——多少个 Agent 参与、角色是否跨目标存活（`single` / `temporary` / `persistent`）。
- **唤醒（Wakeup）**——控制器何时收到新回合（`none` / `heartbeat` / `cron`）。与拓扑分离。
- **收敛（Convergence）**——当前目标如何达到已验证完成（`single-pass` / `evidence-loop` / `phase-gated`）。
- **验证（Verification）**——确定性检查；仅对具名残余风险增加一次独立审查，并记录单一后端。
- **人工门（Human gates）**——后果性动作（发布、部署、删除、支付、权限变更）周围的用户授权边界。
- **任务包（Task packet）**——委派任务的规范控制文档；由 `scripts/validate_task_packet.py` 校验。
- **`<task_handoff>`**——每次交接末尾的固定块，携带 `finding_severity`、`goal_alignment`、`scope_delta`、`new_assumptions` 和 `next_authorized_step`。
- **证据循环（Evidence loop）**——在隔离的链接 Git worktree 中进行的有界、冻结检查迭代，由契约/状态哈希和必需审查把关。
- **原生验证器（Native verifier）**——默认独立审查后端：独立的只读 Codex 上下文，零外部依赖。
- **AgentParliament / Reasonix**——可选审查适配器，绝不要求 Agent Team 依赖它。
- **Luna / Terra 通道**——临时委派的可选实现配置：`luna_worker` 用于规格决定的工作，`terra_worker` 用于上下文密集或更高风险的实现。

## 要求

- 支持 Skills 的 Codex
- Python 3.10 或更高（内置校验器和跨平台安装器）
- Git（可选的证据循环工作流）
- Windows PowerShell 5.1 或更高（仅在使用 PowerShell 助手时）

Skill 和 Python 助手只使用标准库。

## 安装

克隆仓库，然后安装受管 Skill 面。任意平台（Python 3.10+，推荐的跨平台方式）：

```bash
git clone https://github.com/youngfor-shoot/codex-agent-team.git
cd codex-agent-team
python scripts/sync-agent-team.py --mode Install --yes
python scripts/sync-agent-team.py --mode Verify
```

Windows 上也可以使用 PowerShell 助手：

```powershell
git clone https://github.com/youngfor-shoot/codex-agent-team.git
Set-Location codex-agent-team
& .\scripts\sync-agent-team.ps1 -Mode Install -Confirm:$false
& .\scripts\sync-worker-agents.ps1 -Mode Install -Confirm:$false
```

助手默认安装到 `~/.codex/skills/agent-team`，备份当前受管文件、保留未知文件，并在复制后校验哈希。使用 `--destination <path>`（Python）或 `-Destination <path>`（PowerShell）指定其他位置。

## 使用

预览拓扑（无副作用）：

```text
Use $agent-team preview: review this authentication migration plan
```

授权一个临时团队完成单个目标：

```text
Use $agent-team with a temporary team to complete: add import validation and verify it
```

让 Skill 选择最小安全配置：

```text
Use $agent-team to complete: audit and repair this release workflow
```

完整契约见 [`skill/agent-team/SKILL.md`](skill/agent-team/SKILL.md)。证据循环、验证后端、圆桌会议和实现通道的细节在 [`skill/agent-team/references/`](skill/agent-team/references/) 下按需展开。场景示例——预览输出、临时团队记录、证据循环会话、持久团队搭建和拒绝场景——在 [`examples/`](examples/) 下。版本历史见 [`CHANGELOG.md`](CHANGELOG.md)。

## 安全模型

- 证据循环只在干净的链接 Git worktree 中运行，绝不在主检出中。
- 验收命令和资产冻结在 worker 所有权之外。
- Obsidian 仓库被自动拒绝；调用方必须用 `--protected-path` 声明其他敏感根。
- Shell 和网络启动器、内联解释器求值、无界输出和类秘密输出会被助手拦截或脱敏。
- 助手不提供操作系统沙箱，不创建 Agent，不合并、部署、发布或跨越人工门。

敏感报告请参见 [`SECURITY.md`](SECURITY.md)。

## 社区

- [Discussions](https://github.com/youngfor-shoot/codex-agent-team/discussions)——提问和策略提案。
- [`CONTRIBUTING.md`](CONTRIBUTING.md)——如何贡献。
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)——社区准则。

## 开发与验证

```powershell
python -m unittest discover -s skill/agent-team/scripts -p "test_*.py"
python -m unittest discover -s scripts -p "test_*.py"
python skill/agent-team/scripts/validate_task_packet.py skill/agent-team/templates/task-packet.md --template
python skill/agent-team/scripts/validate_task_packet.py examples/in-progress-task-packet.md
python skill/agent-team/scripts/validate_task_packet.py examples/completed-task-packet.md --require-complete
python "$env:USERPROFILE/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skill/agent-team
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-agent-team.ps1 -Mode Verify
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-worker-agents.ps1 -Mode Verify
```

前三条命令跨平台可用。结构校验器需要本地 Codex 安装；Windows 上的 PowerShell 同步检查会校验当前用户级运行时副本；其他平台用 `python scripts/sync-agent-team.py --mode Verify`。CI 在 Linux、macOS 和 Windows 上运行可移植测试，并在 Windows 上做全新安装/校验循环。

## 仓库布局

```text
skill/agent-team/          Canonical Codex Skill
agents/                    可选的规范 worker 配置
examples/                  场景示例
schemas/                   state/contract JSON Schema
scripts/                   仓库安装与验证助手
tests/scenarios/           路由合规场景 fixture
PRD.md                     产品需求与验收标准
Tech-Spec.md               当前技术契约
MEMORY.md                  持久项目决策
```

## 许可证

Apache-2.0。见 [`LICENSE`](LICENSE)。
