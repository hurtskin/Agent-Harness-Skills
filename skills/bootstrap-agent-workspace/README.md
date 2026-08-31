# Bootstrap Agent Workspace

面向主流 Agent Harness 的 AI Agent 工作区初始化 Skill。它将激活路由、跨工具公共规则、客户端适配和可选工具拆分为独立文档，只加载本次真正需要的部分。

所有原生加载项目根 `AGENTS.md` 的 Agent Harness（Trae、Codex、OpenCode、Pi、Qoder 等）开箱即用；Claude Code 额外生成 `CLAUDE.md` 薄入口。协作原则、安全红线与踩坑教训并入 `AGENTS.md` 唯一 P0 事实源，决策记录采用 `decisions/` 目录（一决策一文件 + `_INDEX.md` 索引），换工具零迁移。套餐按项目规模划分；verify-matrix / drift-inventory 用法在 spec-writing，bootstrap 只装机与 AGENTS 登记。

## 核心特性

- `SKILL.md` 只负责激活、工具识别、模块询问和文档路由
- `COMMON.md` 维护跨工具公共流程、单一事实源和产物门禁
- 所有原生加载 `AGENTS.md` 的工具零适配；仅 Claude Code 有独立适配器（`CLAUDE.md` 入口差异）
- 支持单人 / 多人协同：多人时共享宪法 Git 跟踪 + `.agents/` 个人层不跟踪 + 决策晋升流程（草稿无号 → 晋升认领序号 → 人工 review 合并）
- 核心文档、排期、路径成对、verify-matrix、drift-inventory 可独立选择
- verify / drift 使用项目解释器，不绑 bootstrap 内 uv workspace

## 触发方式

在目标项目根目录表达以下意图即可：

- `初始化工作区`
- `生成协作准则`
- `配 AGENTS`
- `bootstrap`
- `配 agent`
- `多工具兼容`
- `harness 兼容`

也可以直接说：

```text
使用 bootstrap-agent-workspace 初始化当前项目。
```

## 按需加载流程

```text
SKILL.md
├── COMMON.md
├── adapters/claude-code.md           仅当前工具为 Claude Code 时
├── 首屏按目的选择场景套餐（含适合项目规模）
│   ├── 快速开始（微型）
│   ├── 敏捷迭代（小型）
│   ├── 规范交付（中型）
│   ├── 大型协作（大型）
│   └── 自定义能力 → 再显示技术模块多选
├── workflows/core-documents.md
├── modules/kanban.md
├── modules/path-align-hooks.md
├── modules/verify-matrix.md
├── modules/drift-inventory.md
├── modules/verify-matrix.md
├── modules/drift-inventory.md
├── modules/path-align-hooks.md
└── workflows/verification.md        最后按确认范围验收
```

首次引导先通过交互式问诊弄清项目目标、阶段、现状、风险和期望产出，再推荐套餐；套餐选择不能替代需求澄清，首屏也不要求用户理解 drift 等术语：

1. **快速开始** — 微型：个人脚本、Demo、文档仓。
2. **敏捷迭代** — 小型：兼职、小程序、MVP、1–2 人；含路径成对钩子。
3. **规范交付** — 中型：有 Spec、要 pre-commit 验证与 inventory 漂移检查。
4. **大型协作** — 大型：多人长周期；同规范交付 + 多人协同骨架。
5. **自定义能力** — 自行组合模块。

verify / drift 日常用法见 **spec-writing** `tools/`；bootstrap 只复制 `specs/verification/`、`specs/drift/` 模板。

## 套餐映射与模块产物

| 场景套餐 | 适合规模 | 技术模块 |
|---|---|---|
| 快速开始（推荐） | 微型 | 核心 + 排期 |
| 敏捷迭代 | 小型 | 核心 + 排期 + 路径成对 |
| 规范交付 | 中型 | 核心 + 排期 + 路径成对 + verify-matrix + drift-inventory |
| 大型协作 | 大型 | 同规范交付（+ 多人协同文档） |
| 自定义 | 任意 | 多选 |

| 选择 | 加载文档 | 主要产物 |
|---|---|---|
| 核心工作区文档 | `workflows/core-documents.md` | `AGENTS.md`（含 Spec 工具表）、`decisions/` |
| 排期清单 | `modules/kanban.md` | `BACKLOG.md` |
| 路径成对钩子 | `modules/path-align-hooks.md` | `tools/path_align_hooks/` |
| verify-matrix | `modules/verify-matrix.md` | `specs/verification/` |
| drift-inventory | `modules/drift-inventory.md` | `specs/drift/` |
| verify-matrix | `modules/verify-matrix.md` | `specs/verification/` |
| drift-inventory | `modules/drift-inventory.md` | `specs/drift/` |

核心文档不是 path-align 或 Spec 工具的强制前置条件。

## 单一事实源

所有客户端只维护以下公共事实源：

| 文件 | 职责 |
|---|---|
| `AGENTS.md` | P0 唯一常驻事实源：短导航与当前入口、协作原则、安全红线、踩坑教训；顶部锚点目录跳转，所有 Agent Harness 原生加载 |
| `decisions/` | P2 决策目录：一决策一文件（`序号-版本-关键词.md`），`_INDEX.md` 是唯一索引表；文件系统即索引，追溯时按关键词定位后局部读取 |
| `BACKLOG.md` | 仅保存未完成事项，完成后移除；闭环在 `decisions/` 新建决策文件并追加索引行 |

协作原则与教训不建独立文件（旧体系的 `soul.md`、`lessons-learned.md` 按核心文档流程迁移并入 `AGENTS.md`）。

生成或升级工具入口（如 `CLAUDE.md`）前会形成：

- `existing_artifacts`：项目中已经存在的产物
- `selected_artifacts`：本次所选模块将生成或升级的产物
- `available_artifacts`：两者并集

工具入口只能引用 `available_artifacts`，不得自行创建缺失的公共核心文档，也不得留下失效引用。

## 多人协同

初始化时确认协作模式（单人 / 多人协同）并写入 `AGENTS.md` 项目定位。多人协同采用「共享宪法 + 个人上下文」三层结构：

| 层级 | 文件 | Git | AI 权限 |
|---|---|---|---|
| 宪法层 | `AGENTS.md`、`BACKLOG.md` | 跟踪 | 起草-确认制：AI 可起草修改，经人工 review 合并后生效 |
| 决策层 | `decisions/` | 跟踪 | 起草-确认制；已确认决策不改写 |
| 个人层 | `.agents/<成员>/`（context.md + scratchpad.md） | 忽略 | 自由读写，成员间互不干扰 |

决策序号在晋升时刻分配（读 `_INDEX.md` 取 max+1，序号 ↔ vN 一一对应）；草稿阶段不编号。并发晋升时 `_INDEX.md` 尾部追加必然冲突——冲突即报警，后合并者整体 +N 改号，纯机械操作。完整规则见 `workflows/core-documents.md` §6。

## 运行时分级加载

初始化完成后，各客户端按同一契约组织日常上下文；这与前述 Skill 初始化阶段的模块路由是两套边界，不能混用。

| 级别 | 用途 | 默认内容 |
|---|---|---|
| P0 / Always | 每次会话立即可见的稳定原则、踩坑教训和当前入口 | `AGENTS.md`（唯一常驻事实源） |
| P1 / Indexed | 按任务相关性定位的工作上下文 | 活跃 Spec、架构/数据流文档、排期和条件规则 |
| P2 / On-demand | 排障、追溯或主题命中时局部读取 | `decisions/`（入口 `_INDEX.md`）、归档 Spec |

支持原生引用或条件规则的客户端可据实映射；能力不明时使用薄入口 + 路径索引，不宣称客户端具备未确认能力。同一事实源只保留一条默认自动加载路径，例如客户端原生加载 `AGENTS.md` 后，不再通过配置重复导入。冲突依次服从客户端不可绕过约束、项目安全红线、当前已确认 Spec/任务约束、索引与历史；无法消解时询问用户。

## Agent Harness 适配

所有原生加载项目根 `AGENTS.md` 的工具共用同一入口，零适配：

| 工具 | 是否需要适配器 | 入口 |
|---|---|---|
| Trae、Codex、OpenCode、Pi、Qoder 等原生加载 `AGENTS.md` 的工具 | 否 | `AGENTS.md` |
| Claude Code | 是：[`adapters/claude-code.md`](adapters/claude-code.md) | `CLAUDE.md` / `.claude/CLAUDE.md`（`@AGENTS.md` 导入） |

无法确定工具或自动加载入口时，询问用户；只有 `AGENTS.md` 已存在或本次将生成时，才向其中写入“Agent 工具适配”表，否则只在执行结果中报告适配状态。同一项目多工具使用时共享 `AGENTS.md` 事实源，Claude Code 额外生成薄入口。

## 文档先行边界

文档先行流程适用于目标项目的业务代码、架构、接口、数据模型和行为规则变更：

1. 定位相关 Spec、决策和教训。
2. 阅读现行文档并列出计划变化。
3. 先修改文档并等待确认。
4. 严格按已确认文档修改代码。
5. 运行所选范围的验证。
6. 只回写 `available_artifacts` 中与本次变更相关的文档。

按已确认模块流程复制工具模板时，不要求补建未选核心文档。

## 验收规则

最终读取 `workflows/verification.md`，仅校验本次选择范围：

- 未选模块没有残留配置、依赖或强制规则
- `AGENTS.md` 可用时检查工具适配表，否则检查执行结果中的适配报告
- 所有入口和相对路径有效，P0 保持精简，P1/P2 读取条件清楚
- decisions/ 和归档内容未进入无条件自动加载链；协作原则、红线与教训都在 `AGENTS.md` 内，无独立副本
- 同一公共事实源没有通过原生入口、引用或配置重复自动加载
- Python 工具（verify/drift runner）使用项目解释器，不在 bootstrap 内维护共享 uv workspace

因缺少未选公共产物而主动跳过客户端入口，不判为失败。

## 目录结构

```text
bootstrap-agent-workspace/
├── SKILL.md
├── COMMON.md
├── README.md
├── adapters/
│   └── claude-code.md
├── workflows/
│   ├── core-documents.md
│   └── verification.md
├── modules/
│   ├── kanban.md
│   ├── verify-matrix.md
│   ├── drift-inventory.md
│   └── path-align-hooks.md
└── templates/
    ├── spec_verification/
    ├── drift_inventory/
    ├── path_align_hooks/
    └── kanban/BACKLOG.md.template
```

## 环境要求

文档初始化本身不限制项目语言。运行 verify / drift 模板时需项目可用的 Python 解释器（由 Agent 指定）。

## 已有项目升级

已有文件默认升级，只补缺失内容。适合以下场景：

- 将旧版工作区文档迁移到单一事实源结构（含旧体系 `soul.md` / `lessons-learned.md` 并入 `AGENTS.md`，单文件 `决策日志.md` 拆分为 `decisions/` 目录）
- 为现有项目增加客户端薄入口
- 接入 path-align、verify-matrix、drift-inventory 模板

重建或覆盖任何已有文件前必须获得用户明确授权。

## 进一步阅读

- `SKILL.md`：激活、检测和模块路由
- `COMMON.md`：公共流程、事实源和产物门禁
- `workflows/core-documents.md`：核心工作区文档生成流程
- `workflows/verification.md`：按选择范围验收
- `modules/*.md`：可选模块实现
- `adapters/claude-code.md`：Claude Code 的 `CLAUDE.md` 入口差异
- `templates/spec_verification/README.md`、`templates/drift_inventory/README.md`：Spec 工具模板说明
