---
name: "bootstrap-agent-workspace"
description: "跨 Hermes 工具初始化 AI Agent 工作区。SKILL.md 仅负责激活、识别和按需路由；支持 Trae、Claude Code、Codex、OpenCode、Pi、Qoder、ZCoder。公共事实只维护一份，可选 changelog-rag 与 drift-check 共享 tools/.venv。Invoke when user says '初始化工作区 / 生成灵魂文档 / 配三件套 / bootstrap / 配 agent / 多工具兼容 / Hermes 兼容'。"
---

# Bootstrap Agent Workspace — 激活与路由

> 本文件只负责激活、检测、询问和索引。禁止在这里展开文档模板、工具安装步骤或某个客户端的完整实现。

## 1. 启动顺序

1. 读取 [`COMMON.md`](./COMMON.md)，确认单一事实源、升级原则与基础验收。
2. 检测当前 Hermes 工具，只读取命中的 [`adapters/`](./adapters/) 文档。
3. 启动时一次询问用户需要哪些模块，可多选：
   - 核心工作区文档（默认推荐）
   - 排期清单
   - changelog-rag
   - drift-check
4. 只读取用户选中的流程或模块文档，不读取未选模块。
5. 执行完成后按 [`workflows/verification.md`](./workflows/verification.md) 校验选中范围。

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

使用一次多选问题：

> 本次要初始化哪些能力？
>
> - 核心工作区文档（推荐）
> - 排期清单
> - changelog-rag 决策检索
> - drift-check 漂移检查

随后汇报“将加载哪些文档 / 将生成哪些产物”，等待确认再执行。

## 5. 强制边界

- 执行前形成“已有产物 + 用户所选模块将生成的产物”清单；适配器只能引用该清单中的文件。
- 已有文件默认升级，只补缺失内容；覆盖必须明确授权。
- 公共项目事实只存在于 `AGENTS.md`、`.trae/rules/soul.md`、`决策日志.md`、`排期清单.md`、`.trae/rules/lessons-learned.md`。
- 适配器只能处理客户端原生入口和配置，不得自行决定生成任何公共核心文档。
- 原生入口依赖不存在的公共文件时，跳过该入口或只引用实际存在的文件，不得留下失效引用。
- 工具入口只保存索引和差异，不复制完整公共事实。
- 未选模块不得把相关命令、依赖或强制规则写入目标项目。
- 不确定时询问，不猜测工具路径、版本或配置。
