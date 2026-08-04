---
name: "bootstrap-agent-workspace"
description: "跨 Hermes 工具初始化 AI Agent 工作区。SKILL.md 仅负责激活、识别和按需路由；支持 Trae、Claude Code、Codex、OpenCode、Pi、Qoder、ZCoder。公共事实只维护一份，可选 changelog-rag 与 drift-check 共享 tools/.venv。Invoke when user says '初始化工作区 / 生成灵魂文档 / 配三件套 / bootstrap / 配 agent / 多工具兼容 / Hermes 兼容'。"
---

# Bootstrap Agent Workspace — 激活与路由

> 本文件只负责激活、检测、询问和索引。禁止在这里展开文档模板、工具安装步骤或某个客户端的完整实现。

## 1. 启动顺序

1. 读取 [`COMMON.md`](./COMMON.md)，确认单一事实源、升级原则与基础验收。
2. 检测当前 Hermes 工具，只读取命中的 [`adapters/`](./adapters/) 文档。
3. 首次引导先按用户目的询问一个场景套餐；首屏只描述用途和效果，不要求用户理解技术模块名。
4. 用户选择“自定义能力”时，再显示原有模块多选；其他套餐直接按映射得到所选模块。
5. 汇报“套餐 / 技术模块 / 将加载的文档 / 将生成的产物”，等待用户确认。
6. 只读取用户确认选中的流程或模块文档，不读取未选模块。
7. 执行完成后按 [`workflows/verification.md`](./workflows/verification.md) 校验选中范围。

## 2. 工具适配器索引

| 工具 | 适配器 | 默认入口 |
|---|---|---|
| Trae | [`adapters/trae.md`](./adapters/trae.md) | `.trae/rules/*.md` + `AGENTS.md` |
| Claude Code | [`adapters/claude-code.md`](./adapters/claude-code.md) | `CLAUDE.md` / `.claude/CLAUDE.md` |
| Codex | [`adapters/codex.md`](./adapters/codex.md) | `AGENTS.md` |
| OpenCode | [`adapters/opencode.md`](./adapters/opencode.md) | `AGENTS.md` / `opencode.json` |
| Pi | [`adapters/pi.md`](./adapters/pi.md) | `AGENTS.md` |
| Qoder | [`adapters/qoder.md`](./adapters/qoder.md) | 解析 `context.fileName`，默认 `AGENTS.md` |
| ZCoder | [`adapters/zcoder.md`](./adapters/zcoder.md) | 未统一，必须确认 |

无法确定工具或入口时，询问“当前工具名称 + 自动加载目录/文件”。仅当目标项目 `AGENTS.md` 已存在或本次选择核心工作区文档时，才将结果写入其中的“Agent 工具适配”表；否则只在本次执行结果中报告，不得为记录适配状态而创建核心文档。只有通用 `AGENTS.md` 时不得反推具体工具。

## 3. 按需模块索引

### 3.1 场景套餐映射

| 首屏选择 | 面向用户的效果 | 映射模块 |
|---|---|---|
| 快速开始（推荐） | 建好项目协作说明和待办排期，适合先把工作区用起来 | 核心工作区文档 + 排期清单 |
| 规范治理（适合长期项目） | 在快速开始基础上，让历史决策可按需查找，减少重复讨论 | 核心工作区文档 + 排期清单 + changelog-rag |
| 完整工具链（适合大型协作） | 在规范治理基础上，检查规范、任务与代码是否逐渐不一致 | 核心工作区文档 + 排期清单 + changelog-rag + drift-check |
| 自定义能力 | 按需组合具体能力 | 进入原有模块多选 |

`drift-check` 仅适用于已经采用 Spec / 文档驱动协作、且需要持续检查文档与实现一致性的项目。不得把它描述为普通小项目的默认必需能力；用户选择“完整工具链”时，也要在确认清单中明确此前提。

### 3.2 技术模块与产物

| 用户选择 | 读取文档 | 主要产物 |
|---|---|---|
| 核心工作区文档 | [`workflows/core-documents.md`](./workflows/core-documents.md) | soul、AGENTS、决策日志、lessons |
| 排期清单 | [`modules/kanban.md`](./modules/kanban.md) | `排期清单.md` |
| changelog-rag | [`modules/changelog-rag.md`](./modules/changelog-rag.md) | `tools/changelog_rag/` + MCP 配置 |
| drift-check | [`modules/drift-check.md`](./modules/drift-check.md) | `tools/drift_check/` |
| 任一 Python 工具 | [`modules/python-workspace.md`](./modules/python-workspace.md) | `tools/pyproject.toml` + 单一 `tools/.venv` |

路由规则：

- 未选择 changelog-rag：不读取其模块文档，不复制源码，不配置 MCP。
- 未选择 drift-check：不读取其模块文档，不复制源码，不注入强制扫描规则。
- 选择任一 Python 工具：必须额外读取 Python workspace 模块。
- 两个工具都选择：只创建一套 `tools/.venv` 和一个 `tools/uv.lock`。
- 后续增加第二个工具：更新 workspace members，并按 Python workspace 模块同步共享环境；不得创建第二个环境。

## 4. 启动询问

首次引导使用一次单选问题，首屏不展示技术模块名：

> 你希望这次先解决什么？
>
> 1. 快速开始（推荐）：建立项目协作说明和待办排期，马上开始推进工作。
> 2. 规范治理（适合长期项目）：在快速开始基础上，让重要历史决定之后能快速查到。
> 3. 完整工具链（适合大型协作）：在规范治理基础上，持续检查规范、任务和代码是否一致；仅适合已有 Spec / 文档驱动协作的项目。
> 4. 自定义能力：我想自己组合要安装的能力。

仅当用户选择“自定义能力”时，继续使用一次原有模块多选问题：

> 本次要初始化哪些能力？
>
> - 核心工作区文档
> - 排期清单
> - changelog-rag 决策检索
> - drift-check 漂移检查（仅适用于已有 Spec / 文档驱动协作的项目）

随后按套餐映射或自定义结果，汇报“所选套餐 / 技术模块 / 将加载哪些文档 / 将生成哪些产物”。“完整工具链”的确认清单必须再次注明 `drift-check` 的适用前提。等待确认后再执行。

## 5. 强制边界

- 执行前形成“已有产物 + 用户所选模块将生成的产物”清单；适配器只能引用该清单中的文件。
- 已有文件默认升级，只补缺失内容；覆盖必须明确授权。
- 公共项目事实只存在于 `AGENTS.md`、`.trae/rules/soul.md`、`决策日志.md`、`排期清单.md`、`.trae/rules/lessons-learned.md`。
- 适配器只能处理客户端原生入口和配置，不得自行决定生成任何公共核心文档。
- 原生入口依赖不存在的公共文件时，跳过该入口或只引用实际存在的文件，不得留下失效引用。
- 工具入口只保存索引和差异，不复制完整公共事实。
- 未选模块不得把相关命令、依赖或强制规则写入目标项目。
- 不确定时询问，不猜测工具路径、版本或配置。
