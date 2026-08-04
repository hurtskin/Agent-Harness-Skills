# Bootstrap Agent Workspace

面向主流 Hermes 编程工具的 AI Agent 工作区初始化 Skill。它将激活路由、跨工具公共规则、客户端适配和可选工具拆分为独立文档，只加载本次真正需要的部分。

支持 Trae、Claude Code、Codex、OpenCode、Pi、Qoder 和 ZCoder。Trae 是基线实现，所有客户端共享一套项目事实；changelog-rag 与 drift-check 共享项目 `tools/` 下的同一套 Python 环境。

## 核心特性

- `SKILL.md` 只负责激活、工具识别、模块询问和文档路由
- `COMMON.md` 维护跨工具公共流程、单一事实源和产物门禁
- 每个 Hermes 客户端使用独立适配器，避免把所有实现一次性加载
- 核心文档、排期、changelog-rag、drift-check 均可独立选择
- 未选模块不加载、不生成、不安装依赖，也不注入规则
- 已有文件默认增量升级，覆盖或重建必须得到明确授权
- 客户端入口只保存索引和必要差异，不复制完整公共事实
- 初始化完成后的日常上下文按 P0 / P1 / P2 分级加载，历史与教训默认按需读取
- 分级加载不改变初始化阶段的模块按需路由，也不改变现有公共事实源路径
- 两个 Python 工具共享唯一的 `tools/.venv` 和 `tools/uv.lock`

## 触发方式

在目标项目根目录表达以下意图即可：

- `初始化工作区`
- `生成灵魂文档`
- `配三件套`
- `bootstrap`
- `配 agent`
- `多工具兼容`
- `Hermes 兼容`

也可以直接说：

```text
使用 bootstrap-agent-workspace 初始化当前项目。
```

## 按需加载流程

```text
SKILL.md
├── COMMON.md
├── adapters/<当前客户端>.md
├── 首屏按目的选择场景套餐
│   ├── 快速开始（推荐）
│   ├── 规范治理（适合长期项目）
│   ├── 完整工具链（适合大型协作）
│   └── 自定义能力 → 再显示技术模块多选
├── workflows/core-documents.md      套餐映射或自定义选中核心文档时
├── modules/kanban.md                套餐映射或自定义选中排期时
├── modules/changelog-rag.md         套餐映射或自定义选中 changelog-rag 时
├── modules/drift-check.md           套餐映射或自定义选中 drift-check 时
├── modules/python-workspace.md      选中任一 Python 工具时
└── workflows/verification.md        最后按确认范围验收
```

首次引导先询问用户想达到什么效果，首屏不要求理解 changelog、RAG、drift 等术语：

1. **快速开始（推荐）**：建立项目协作说明和待办排期，马上开始推进工作。
2. **规范治理（适合长期项目）**：在快速开始基础上，让重要历史决定之后能快速查到。
3. **完整工具链（适合大型协作）**：在规范治理基础上，持续检查规范、任务和代码是否一致。此项仅适合已有 Spec / 文档驱动协作的项目，不是普通小项目的默认选择。
4. **自定义能力**：自行组合具体能力，此时才显示原有技术模块多选。

确认前会汇报所选套餐、对应技术模块、将加载的文档和将生成的产物；完整工具链会再次提示一致性检查的适用前提。未选择的模块不会参与执行。

## 套餐映射与模块产物

| 场景套餐 | 技术模块 |
|---|---|
| 快速开始（推荐） | 核心工作区文档 + 排期清单 |
| 规范治理（适合长期项目） | 核心工作区文档 + 排期清单 + changelog-rag |
| 完整工具链（适合大型协作） | 核心工作区文档 + 排期清单 + changelog-rag + drift-check |
| 自定义能力 | 进入核心工作区文档、排期清单、changelog-rag、drift-check 原有多选 |

技术模块名在确认清单或自定义入口中展示。`drift-check` 仅适用于已有 Spec / 文档驱动协作、需要持续检查文档与实现一致性的项目，避免将完整工具链误导为普通小项目的默认方案。

| 选择 | 加载文档 | 主要产物 |
|---|---|---|
| 核心工作区文档 | `workflows/core-documents.md` | soul、`AGENTS.md`、决策日志、lessons |
| 排期清单 | `modules/kanban.md` | `排期清单.md` |
| changelog-rag | `modules/changelog-rag.md` | `tools/changelog_rag/` 和当前客户端 MCP 配置 |
| drift-check | `modules/drift-check.md` | `tools/drift_check/` |
| 任一 Python 工具 | `modules/python-workspace.md` | `tools/pyproject.toml`、`tools/.venv`、`tools/uv.lock` |

核心文档不是其他模块的强制前置条件。例如仅选择 changelog-rag 时，不会为了登记适配状态而创建 `AGENTS.md`。如果默认数据源 `决策日志.md` 不存在，Skill 会要求补选核心文档、提供其他已有日志路径或取消该模块。

## 单一事实源

所有客户端只维护以下公共事实源：

| 文件 | 职责 |
|---|---|
| `AGENTS.md` | 短导航与当前工作入口：最小项目定位、当前任务、命令和 Spec ↔ Code / 事实源索引 |
| `.trae/rules/soul.md` | 必须常驻的稳定原则与安全红线；路径为历史兼容名称，不代表仅供 Trae 使用 |
| `决策日志.md` | 追加式项目决策历史，由 RAG 或关键词局部读取按需检索 |
| `排期清单.md` | 仅保存未完成事项，完成后移除并将闭环写入决策日志 |
| `.trae/rules/lessons-learned.md` | 跨任务通用教训，append-only，默认按需读取 |

执行适配器前会形成：

- `existing_artifacts`：项目中已经存在的产物
- `selected_artifacts`：本次所选模块将生成或升级的产物
- `available_artifacts`：两者并集

适配器只能引用 `available_artifacts`，不得自行创建缺失的公共核心文档，也不得留下失效引用。

## 运行时分级加载

初始化完成后，各客户端按同一契约组织日常上下文；这与前述 Skill 初始化阶段的模块路由是两套边界，不能混用。

| 级别 | 用途 | 默认内容 |
|---|---|---|
| P0 / Always | 每次会话立即可见的稳定原则和当前入口 | 精简 soul、短 `AGENTS.md` |
| P1 / Indexed | 按任务相关性定位的工作上下文 | 活跃 Spec、架构/数据流文档、排期和条件规则 |
| P2 / On-demand | 排障、追溯或主题命中时局部读取 | `决策日志.md`、lessons、归档 Spec |

支持原生引用或条件规则的客户端可据实映射；能力不明时使用薄入口 + 路径索引，不宣称客户端具备未确认能力。同一事实源只保留一条默认自动加载路径，例如客户端原生加载 `AGENTS.md` 后，不再通过配置重复导入。冲突依次服从客户端不可绕过约束、项目安全红线、当前已确认 Spec/任务约束、索引与历史；无法消解时询问用户。

## Hermes 工具适配

| 工具 | 适配器 | 默认入口 |
|---|---|---|
| Trae | `adapters/trae.md` | `.trae/rules/*.md` 和 `AGENTS.md` |
| Claude Code | `adapters/claude-code.md` | `CLAUDE.md` / `.claude/CLAUDE.md` |
| Codex | `adapters/codex.md` | `AGENTS.md` |
| OpenCode | `adapters/opencode.md` | `AGENTS.md` / `opencode.json` |
| Pi | `adapters/pi.md` | `AGENTS.md`，可选 `.pi/SYSTEM.md` / `.pi/APPEND_SYSTEM.md` |
| Qoder | `adapters/qoder.md` | 解析 `context.fileName`，默认 `AGENTS.md` |
| ZCoder | `adapters/zcoder.md` | 实现不统一，必须检测或询问 |

同一项目可以同时启用多个适配器，但仍共享上述公共事实源。只有 `AGENTS.md` 已存在或本次将生成时，才向其中写入“Agent 工具适配”表；否则只在执行结果中报告适配状态。

## 共享 Python Workspace

changelog-rag 和 drift-check 使用同一个 uv workspace：

```text
tools/
├── pyproject.toml
├── uv.lock
├── .venv/
├── changelog_rag/
└── drift_check/
```

统一从项目 `tools/` 运行：

```powershell
Set-Location "tools"
uv sync --all-packages --all-extras
uv run pytest changelog_rag/tests
uv run pytest drift_check/tests
uv run drift-check scan --project-root ..
```

只选择一个工具时，workspace 只包含该成员。后续增加第二个工具时更新 members 并同步现有环境，不创建成员级 `.venv` 或第二个锁文件。

## changelog-rag MCP

changelog-rag 以 stdio MCP Server 运行，数据源默认是项目根 `决策日志.md`，也可以使用用户确认的其他决策日志绝对路径。

### Trae

使用 `templates/config/mcp-config.json.template` 生成项目 `.trae/mcp-config.json`。

### OpenCode

使用 `templates/config/opencode-changelog-rag.json.template`，将 `mcp.changelog-rag` 增量合并到项目根已有的 `opencode.json` 或 `opencode.jsonc`；两者都不存在时创建 `opencode.json`。

OpenCode 配置采用原生格式：

- `mcp.changelog-rag.type` 为 `local`
- `command` 是包含可执行文件和参数的单一数组
- `environment.CHANGELOG_RAG_AGENTS_MD` 指向实际数据源
- 已有配置字段、注释和 JSON/JSONC 格式必须保留

可直接参考 `templates/config/opencode.json.example`。应用前将示例中的 `C:/path/to/your-project` 替换为项目绝对路径。如果项目已有 OpenCode 配置，只合并 `mcp.changelog-rag` 节点，不要覆盖整个文件。

修改 MCP Server 源码或配置后，需要重启对应客户端的 MCP Server。

## 文档先行边界

文档先行流程适用于目标项目的业务代码、架构、接口、数据模型和行为规则变更：

1. 定位相关 Spec、决策和教训。
2. 阅读现行文档并列出计划变化。
3. 先修改文档并等待确认。
4. 严格按已确认文档修改代码。
5. 运行所选范围的验证。
6. 只回写 `available_artifacts` 中与本次变更相关的文档。

按已确认模块流程复制或安装 changelog-rag、drift-check 工具模板时，不要求补建未选核心文档。如果工具初始化同时改变项目接口、架构或运行行为，相关项目变更部分仍执行文档先行流程。

## 验收规则

最终读取 `workflows/verification.md`，仅校验本次选择范围：

- 未选模块没有残留配置、依赖或强制规则
- `AGENTS.md` 可用时检查工具适配表，否则检查执行结果中的适配报告
- 所有入口和相对路径有效，P0 保持精简，P1/P2 读取条件清楚
- 决策日志、lessons 和归档内容未进入无条件自动加载链
- 同一公共事实源没有通过原生入口、引用或配置重复自动加载
- Python 工具共享唯一 workspace、虚拟环境和锁文件
- changelog-rag 使用当前客户端原生 MCP 格式，数据源实际存在
- OpenCode 的 `mcp.changelog-rag` 使用 `local` 类型和单一 `command` 数组

因缺少未选公共产物而主动跳过客户端入口，不判为失败。

## 目录结构

```text
bootstrap-agent-workspace/
├── SKILL.md
├── COMMON.md
├── README.md
├── adapters/
│   ├── trae.md
│   ├── claude-code.md
│   ├── codex.md
│   ├── opencode.md
│   ├── pi.md
│   ├── qoder.md
│   └── zcoder.md
├── workflows/
│   ├── core-documents.md
│   └── verification.md
├── modules/
│   ├── kanban.md
│   ├── changelog-rag.md
│   ├── drift-check.md
│   └── python-workspace.md
└── templates/
    ├── tools/pyproject.toml.template
    ├── changelog_rag/
    ├── drift_check/
    ├── kanban/排期清单.md.template
    └── config/
        ├── mcp-config.json.template
        ├── opencode-changelog-rag.json.template
        └── opencode.json.example
```

## 环境要求

文档初始化本身不限制项目语言。启用 Python 工具时需要：

- Python 3.10+
- `uv`
- 首次准备 changelog-rag 语义模型时可访问模型源，或本地已经缓存模型

支持在 Windows PowerShell 环境执行模板复制、依赖同步和验证。

## 已有项目升级

已有文件默认升级，只补缺失内容。适合以下场景：

- 将旧版工作区文档迁移到单一事实源结构
- 将项目决策从自动加载入口分离到 `决策日志.md`
- 为现有项目增加客户端薄入口
- 接入 changelog-rag、drift-check 或共享 Python workspace
- 为现有 OpenCode 配置增量加入 changelog-rag MCP

重建或覆盖任何已有文件前必须获得用户明确授权。

## 进一步阅读

- `SKILL.md`：激活、检测和模块路由
- `COMMON.md`：公共流程、事实源和产物门禁
- `workflows/core-documents.md`：核心工作区文档生成流程
- `workflows/verification.md`：按选择范围验收
- `modules/*.md`：可选模块实现
- `adapters/*.md`：Hermes 客户端差异
- `templates/changelog_rag/README.md`：changelog-rag 实现说明
- `templates/drift_check/README.md`：drift-check 实现说明
