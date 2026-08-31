# Agent Harness Skills

让 AI Agent 项目不再靠聊天记录和运气推进。

这是一组可复制到 Trae、Cursor、upstream、OpenCode、Pi、Qoder 等 Agent Harness 的自包含 Skill，用来解决三件最容易失控的事：项目秩序难以冷启动、Spec 与代码容易脱节、超长任务难以安全续接。

## 你可能正遇到这个问题

比如你刚完成一个项目，已经为它建立了规则文档、决策记录和任务排期；下一个项目开始时，这套秩序却只能靠手工重新搭一遍。开发过程中，Spec 改了但代码没跟着改，或者代码改了却忘了回写 Spec；再往后，一个超长任务耗尽当前会话上下文，你既不想把已经确认的决策和验证证据丢掉，也不想让下一个 Agent 从头猜一遍。项目未必马上报错，但维护成本和失控风险会持续累积。

这套 Skill 把这条链路固定下来：

```text
冷启动项目秩序 → 保持 Spec 与代码同步 → 带着证据交接任务
```

| 失控点 | 对应 Skill | 你得到的结果 |
|---|---|---|
| 每个新项目都要重新搭秩序 | [`bootstrap-agent-workspace`](./skills/bootstrap-agent-workspace/SKILL.md) | 冷启动统一的 `AGENTS.md`、`decisions/` 和 `BACKLOG.md` |
| Spec 与代码互相脱节 | [`spec-writing`](./skills/spec-writing/SKILL.md) | 把规则写成可实施、可验证，并要求变更保持同步的契约 |
| 超长任务无法安全续接 | [`task-handoff`](./skills/task-handoff/SKILL.md) | 用文件、diff、测试等证据生成 `READY` / `BLOCKED` 交接包 |

## 什么时候用哪个

- 刚开始一个 Agent 项目，想先把工作区和协作规则立住：用 `bootstrap-agent-workspace`
- 需求容易变、实现不能自由发挥：用 `spec-writing`
- 上下文快满了、要换 Agent 或多人接力：用 `task-handoff`
- 希望从“能写出来”升级到“可持续交付”：三个一起用

## 30 秒开始

每个 Skill 都是自包含目录。复制到目标 Harness 的 `skills` 目录，然后触发对应 Skill：

```text
<skills-root>/bootstrap-agent-workspace/
<skills-root>/spec-writing/
<skills-root>/task-handoff/
```

推荐第一次只安装 `bootstrap-agent-workspace`，按项目规模选择套餐：

| 套餐 | 适合 | 首次产出 |
|---|---|---|
| 快速开始 | 个人脚本、Demo、文档仓 | 核心规则、决策目录、排期 |
| 敏捷迭代 | MVP、兼职项目、1–2 人 | 快速开始 + 路径成对检查 |
| 规范交付 | 有 Spec、需要提交前门控 | 敏捷迭代 + 验证矩阵 + 漂移检查 |
| 大型协作 | 多人、长周期项目 | 规范交付 + 多人协同骨架 |

## 三个 Skill 分别解决什么

### `bootstrap-agent-workspace`：先把工作区立住

按项目规模问诊式初始化，而不是一次性堆满工具。它负责建立共享宪法、决策记录和排期，并可按需安装路径成对、验证矩阵、结构漂移等守门模板。

### `spec-writing`：让需求成为实施许可证

用固定结构、字段级约束和 `P-*` / `PT-*` Properties，把“希望它这样工作”写成 Agent 可以照着实现、测试可以照着验证的契约。需求变更时，先更新契约，再进入实现。

### `task-handoff`：让任务带着证据继续

交接不是“帮我总结一下”，而是由接任 Agent 审问当前状态，并要求结论引用文件、diff 或测试证据。最终明确输出 `READY`、`READY_WITH_RISKS` 或 `BLOCKED`，避免把未验证内容伪装成完成。

## 一个真实结果

在[拼多多拉图工具案例](./docs/case-study-pdd.md)中，需求从“拉取开源项目”逐步变成可交付的单文件 exe：中途经历需求追加、多个会话、Spec 重构、真实环境验证和多 Agent 并行。共享规则、决策记录和交接纪律让项目最终做到：双击启动、订单扫描、精确下载、去重、搜索、清理和状态管理，全程零命令。

## 这套方案的边界

- 它是跨 Harness 的 Skill 组合，不是某个 IDE 的内置功能替代品。
- Hook、验证矩阵和漂移检查由消费者项目按需启用；小项目可以只安装核心文档。
- 本仓库只发布 Skill，不把消费者项目的业务代码或运行时框架带进来。

## 发布验证

在仓库根目录执行：

```powershell
uv run --no-project python scripts/check_links.py
uv run --no-project python skills/bootstrap-agent-workspace/scripts/self_check.py
uv run --no-project python -m unittest discover -s skills/bootstrap-agent-workspace/tests -v
uv run --no-project python -m unittest discover -s skills/task-handoff/tests -v
```

根目录导航见 [`AGENTS.md`](./AGENTS.md)。

## License

[MIT](./LICENSE)
