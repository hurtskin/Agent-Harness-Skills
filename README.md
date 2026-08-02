# Bootstrap Agent Workspace

一个面向 Trae IDE 的 AI Agent 项目冷启动 Skill。它通过交互式问答识别项目上下文，并初始化项目规则、工作记忆、决策记录、待办看板和配套检查工具。

该 Skill 不绑定语言、框架或项目类型，适合新项目初始化，也支持对已有工作区进行增量升级。

## 核心能力

- 根据仓库结构、配置文件、README 和入口文件识别项目上下文
- 对无法可靠推断的信息进行结构化提问，不凭空猜测
- 建立“文档先于代码、Spec 是唯一真相源”的 Agent 工作规则
- 分离自动加载的项目上下文与按需检索的历史决策，降低上下文消耗
- 维护未完成事项看板，并将已闭环事实永久记录到决策日志
- 可选生成本地决策日志 RAG MCP Server
- 可选生成 Spec 与代码漂移检查 CLI
- 对已存在的工作区文件默认采用升级模式，避免覆盖用户内容

## 触发方式

在项目根目录中向 Trae Agent 表达以下意图即可触发：

- `初始化工作区`
- `生成灵魂文档`
- `配三件套`
- `三件套脚手架`
- `bootstrap`
- `配 agent`

也可以直接说：

```text
使用 bootstrap-agent-workspace 初始化当前项目。
```

## 初始化产物

默认流程会生成 5 份核心文档，并按用户选择生成 3 项配套工具或配置。

### 核心文档

| 产物 | 作用 |
|---|---|
| `.trae/rules/soul.md` | Agent 行为准则、工作流程、工具偏好和禁止触碰的红线 |
| `AGENTS.md` | Trae IDE 自动加载的项目上下文概要、当前任务、常用命令和 Spec ↔ Code 导航 |
| `决策日志.md` | 不自动加载的项目决策历史，采用追加式索引记录，由 RAG 工具按需检索 |
| `排期清单.md` | 未完成事项看板；完成项从看板清除，闭环事实写入决策日志 |
| `.trae/rules/lessons-learned.md` | 跨任务通用踩坑教训，按稳定编号追加 |

### 配套工具

| 产物 | 作用 | 默认行为 |
|---|---|---|
| `tools/changelog_rag/` | 本地 MCP Server，按关键词检索决策日志 | 询问后生成 |
| `.trae/mcp-config.json` | changelog-rag 的 Trae MCP 配置模板 | 随 RAG 工具生成 |
| `tools/drift_check/` | 检测 Spec、任务、测试与代码之间的漂移 | 询问后生成 |

## 文档职责边界

```text
soul.md
└─ Agent 应该如何工作，以及不能做什么

AGENTS.md
└─ 当前项目是什么、如何运行、当前在做什么、Spec 与代码如何对应

决策日志.md
└─ 项目历史上做过哪些决策；永久保留并按需检索

排期清单.md
└─ 现在还有哪些事情未完成；完成后从看板移除

lessons-learned.md
└─ 哪些教训需要跨任务长期遵守
```

其中：

- `AGENTS.md` 只保留适合自动加载的项目上下文，不承载项目决策流水。
- `决策日志.md` 保存所有决策变更，详细设计正文仍应位于对应 Spec 中。
- `排期清单.md` 只保存未完成事项，不作为历史档案。
- `lessons-learned.md` 采用 append-only 方式沉淀可复用教训。

## 工作流程

Skill 按以下顺序执行：

1. **启动自检**：确认当前目录、读写权限、已有工作区文件和内置模板。
2. **识别项目**：读取仓库结构、项目清单文件、README 和入口文件。
3. **确认上下文**：汇报推断结果，对不确定字段询问用户。
4. **生成 `soul.md`**：建立 Agent 行为准则、文档先行流程和项目红线。
5. **生成 `AGENTS.md`**：记录项目上下文、架构事实、命令和文档目录树。
6. **生成 `决策日志.md`**：建立项目决策历史的初始索引。
7. **生成 `排期清单.md`**：按用户选择创建待办看板空骨架。
8. **生成 `lessons-learned.md`**：建立跨任务教训沉淀骨架。
9. **生成配套工具**：按用户选择安装 changelog-rag 与 drift-check 模板。
10. **互链校对**：检查文档职责、链接、命令和配置是否一致。
11. **完成报告**：汇报产物、字段来源、风险残留和下一步操作。

每个关键阶段都会等待用户确认后再继续。无法可靠判断的信息会进入提问流程，而不是使用未经确认的默认值。

## 核心原则

### 文档先于代码

生成的 `soul.md` 会内置文档先行约束：

1. 定位本次修改对应的 Spec、历史决策和相关教训。
2. 阅读现行文档并确认现状。
3. 先修改文档并向用户展示差异。
4. 用户确认后，严格按文档修改代码。
5. 运行 drift-check 检查 Spec 与代码的一致性。
6. 将最终结果回写到决策日志、文档目录树和教训库。

### 不猜，多问

每个字段都应具备明确来源：

- 从仓库事实中推断
- 由用户自由输入
- 使用 Skill 内置默认规则

如果推断缺少可靠依据，Skill 会通过选项加自由输入的方式询问用户。

### 最小化覆盖

当目标文件已存在时，默认读取现有内容并进入升级模式，只补充缺失项。仅在用户明确选择重建时才覆盖已有结构。

## changelog-rag

`templates/changelog_rag/` 是一个 Python 3.10+ 本地 MCP Server 模板，用于从 `决策日志.md` 中按量读取相关历史记录，避免 Agent 每次加载完整日志。

当前服务提供以下能力：

| MCP 工具 | 用途 |
|---|---|
| `list_recent_changelog` | 列出最近的决策记录 |
| `load_relevant_changelog` | 根据关键词进行语义检索 |
| `latest_changelog_version` | 获取当前最新决策版本 |
| `append_log_entry` | 追加新的决策记录 |
| `update_log_entry` | 更新指定版本和 occurrence 的记录 |
| `delete_log_entry` | 清空指定记录正文并保留版本标题锚点 |

初始化后可在项目中执行：

```powershell
Set-Location "tools/changelog_rag"
uv sync --extra dev
uv run pytest tests/
```

随后将 `.trae/mcp-config.json` 中的配置添加到 Trae IDE 的 MCP 面板。若修改了 MCP Server 源码，需要在 IDE 中禁用并重新启用该 Server。

> 首次安装语义模型依赖可能需要联网；生成的 MCP 配置默认以离线模式运行。

## drift-check

`templates/drift_check/` 是一个 Python 3.10+ CLI 模板，用于让 Spec 与代码之间的漂移可以被自动发现，并通过退出码接入 CI。

### 检查项

| ID | 检查内容 |
|---|---|
| D1 | `spec.md`、`tasks.md`、`checklist.md` 版本一致性 |
| D2 | Spec 字段或类声明与代码模型的一致性 |
| D3 | Gherkin 场景、测试用例标记与测试函数数量的一致性 |
| D4 | `tasks.md` 任务状态与代码目标实际状态的一致性 |
| D5 | lessons 段落引用是否存在 |
| D6 | Bug 子 Spec 是否已同步到父 Spec 的闭环记录 |

初始化后应在工具目录中执行：

```powershell
Set-Location "tools/drift_check"
uv sync --extra dev
uv run pytest tests/
uv run drift-check scan --project-root ../..
```

其他常用命令：

```powershell
uv run drift-check scan --project-root ../.. --format json
uv run drift-check scan --project-root ../.. --only D1 --only D4
uv run drift-check list-detectors
```

退出码约定：

- `0`：没有 ERROR
- `1`：存在至少一个 ERROR

工具通过 Adapter 模式适配项目。标准模板面向 `.trae/specs/` 布局；如果项目采用其他 Spec 目录或格式，需要实现自定义 `SpecAdapter`。

## 目录结构

```text
bootstrap-agent-workspace/
├── SKILL.md
├── README.md
└── templates/
    ├── changelog_rag/
    │   ├── src/changelog_rag/
    │   ├── tests/
    │   ├── pyproject.toml
    │   └── README.md
    ├── config/
    │   └── mcp-config.json.template
    ├── drift_check/
    │   ├── src/drift_check/
    │   ├── tests/
    │   ├── pyproject.toml
    │   └── README.md
    └── kanban/
        └── 排期清单.md.template
```

## 环境要求

Skill 的文档初始化本身不限制项目语言。启用配套 Python 工具时，需要：

- Trae IDE
- Python 3.10+
- `uv`
- changelog-rag 首次下载嵌入模型时可访问对应模型源

支持在 Windows PowerShell 环境下完成模板复制、依赖安装和验证。

## 已有项目升级

如果目标项目已经存在部分产物，Skill 应先读取现有内容并让用户选择：

- **升级**：保留已有内容，只补缺失字段、规则和工具配置
- **重建**：按当前模板重新生成，由用户明确授权覆盖

升级模式尤其适用于：

- 将旧版“工作区三件套”迁移为当前五份核心文档
- 将项目决策从 `AGENTS.md` 分离到 `决策日志.md`
- 增加 `排期清单.md`
- 接入 changelog-rag 或 drift-check
- 补齐文档先行、临时文件和 Git 操作红线

## 注意事项

- 应从目标项目根目录调用该 Skill。
- 不要手工将 `决策日志.md` 的全部正文复制回 `AGENTS.md`，否则会增加自动加载上下文。
- `排期清单.md` 只保留未完成事项；完成项的闭环信息应写入 `决策日志.md`。
- drift-check 必须在 `tools/drift_check/` 的 Python 环境中运行，并将项目根传为 `../..`。
- `.trae/mcp-config.json` 中的 `<PROJECT_ROOT>` 必须替换为目标项目的绝对路径。
- Skill 运行中若用户要求停止，应保留已经生成的文件，并询问是否回滚，不应擅自删除。

## 进一步说明

完整的交互决策树、文档模板、红线规则、异常处理和验收清单见 `SKILL.md`。两个配套工具的详细使用方式分别见：

- `templates/changelog_rag/README.md`
- `templates/drift_check/README.md`
