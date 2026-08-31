---
name: "bootstrap-agent-workspace"
description: "跨 Agent Harness 初始化 AI Agent 工作区。SKILL.md 仅负责激活、识别和按需路由；所有原生加载 AGENTS.md 的 Agent Harness（Trae、Codex、OpenCode、Pi、Qoder 等）开箱即用，Claude Code 额外生成 CLAUDE.md 薄入口。协作原则、安全红线与踩坑教训并入 AGENTS.md 唯一 P0 事实源，决策记录采用 decisions/ 目录（一决策一文件 + _INDEX.md 索引），换工具零迁移；支持单人/多人协同（.agents/ 个人层 + 决策晋升流程），可选路径成对钩子、verify-matrix、drift-inventory（通用脚本模板，无分 Harness 适配长文）。Invoke when user says '初始化工作区 / 生成协作准则 / 配 AGENTS / bootstrap / 配 agent / 多工具兼容 / harness 兼容 / 多人协同 / 路径成对 / path-align'。"
---

# Bootstrap Agent Workspace — 激活与路由

> 本文件只负责激活、检测、询问和索引。verify-matrix / drift-inventory **用法**在 spec-writing；本 Skill 只装机与 AGENTS 登记。

## 1. 启动顺序

1. 读取 [`COMMON.md`](./COMMON.md)，确认单一事实源、升级原则与基础验收。
2. 检测当前 Agent Harness：默认入口是项目根 `AGENTS.md`，无需适配；仅 Claude Code 例外，读取 [`adapters/claude-code.md`](./adapters/claude-code.md) 生成 `CLAUDE.md` 薄入口。
3. 首次引导先通过**交互式项目问诊**搞清楚项目要做什么、当前处于什么阶段、已有何种规则/文档、主要协作风险和期望产出；不能用场景套餐选择替代需求澄清。
4. 根据问诊结果推荐场景套餐（含适合项目规模说明），并允许用户改选「自定义能力」。
5. 用户选择「自定义能力」时，再显示技术模块多选。
6. 汇报「问诊结论 / 推荐套餐 / 技术模块 / 将加载的文档 / 将生成的产物」，等待用户确认。
   - 若含路径成对钩子：必须把「宿主 hook 配置文件（如 `.cursor/hooks.json` / `.claude/settings.json` / 其他 Harness 惯例路径）」列在「将生成的产物」中，等待用户确认；未识别 Harness 时**必问用户**。
7. 只读取用户确认选中的流程或模块文档。
8. 执行完成后按 [`workflows/verification.md`](./workflows/verification.md) 校验选中范围。

## 2. 工具入口策略

| 工具 | 是否需要适配器 | 入口 |
|---|---|---|
| 原生加载 `AGENTS.md` 的工具 | 否 | `AGENTS.md` |
| Claude Code | 是：[`adapters/claude-code.md`](./adapters/claude-code.md) | `CLAUDE.md` / `.claude/CLAUDE.md`（`@AGENTS.md` 导入） |

## 3. 按需模块索引

### 3.1 场景套餐映射

| 首屏选择 | 适合项目规模 | 映射模块 |
|---|---|---|
| 快速开始（推荐） | **微型**：个人脚本、Demo、文档/Skill 仓 | 核心 + 排期 |
| 敏捷迭代 | **小型**：兼职、小程序、MVP、1–2 人 | 核心 + 排期 + 路径成对 |
| 规范交付 | **中型**：有 Spec、要提交前门控 | 核心 + 排期 + 路径成对 + verify-matrix + drift-inventory |
| 大型协作 | **大型**：多人、长周期 | 同规范交付（+ 多人协同文档） |
| 自定义能力 | 任意 | 技术模块多选 |

### 3.2 技术模块与产物

| 用户选择 | 读取文档 | 主要产物 |
|---|---|---|
| 核心工作区文档 | [`workflows/core-documents.md`](./workflows/core-documents.md) | `AGENTS.md`（含 Spec 工具表）、decisions/ |
| 排期清单 | [`modules/kanban.md`](./modules/kanban.md) | `BACKLOG.md` |
| 路径成对钩子 | [`modules/path-align-hooks.md`](./modules/path-align-hooks.md) | `tools/path_align_hooks/` |
| verify-matrix | [`modules/verify-matrix.md`](./modules/verify-matrix.md) | `specs/verification/` |
| drift-inventory | [`modules/drift-inventory.md`](./modules/drift-inventory.md) | `specs/drift/` |

路由规则：

- 未选 verify-matrix / drift-inventory：不复制 `specs/verification/`、`specs/drift/`，不在 AGENTS 登记。
- 未选路径成对钩子：不复制 `tools/path_align_hooks/`，不生成宿主 hook 配置。
- 选路径成对钩子：落地通用脚本（`tools/path_align_hooks/turn_align.{ps1,sh}`），**Agent 按所识别 Harness 的官方 hook 提示生成对应宿主配置文件**（如 `.cursor/hooks.json` / `.claude/settings.json` / 其他惯例路径），并把 `turn_align` 注册到「轮次结束」类事件，工作目录为仓库根。未识别 Harness 走「必问用户」，不得默认跳过接线，也不得默认套 Trae。

## 4. 启动询问

### 4.1 先做项目问诊，再选套餐

首次启动必须先用交互式提问建立项目画像，至少确认：

- **目标**：这个项目要做什么，最终交付给谁，怎样算完成
- **阶段**：新项目冷启动、已有项目整顿，还是正在处理具体需求
- **现状**：已有 `AGENTS.md`、Spec、决策记录、排期或验证工具吗
- **风险**：最担心规则丢失、Spec/代码脱节、结构漂移、多人协作冲突，还是长任务上下文耗尽
- **产出**：这次希望生成哪些文档、目录、检查或交接材料

问诊结果必须用用户能确认的自然语言复述一遍，再进入套餐推荐。若项目目标或边界仍不清楚，继续追问，不得直接套用默认套餐。

### 4.2 根据问诊结果推荐套餐

> 1. **快速开始** — 微型：个人脚本、Demo、文档仓。  
> 2. **敏捷迭代** — 小型：兼职、小程序、MVP；含路径成对。  
> 3. **规范交付** — 中型：Spec + verify + drift pre-commit 模板。  
> 4. **大型协作** — 大型：同规范交付 + 多人协同。  
> 5. **自定义能力** — 多选：核心 / 排期 / path-align / verify-matrix / drift-inventory。

## 5. 强制边界

- 公共项目事实只存在于 `AGENTS.md`、`decisions/`、`BACKLOG.md`。
- 未选模块不得把相关命令、依赖或强制规则写入目标项目。
- verify / drift 日常用法在 **spec-writing** `tools/`，不在本 Skill 重复。
