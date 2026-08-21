# Agent Harness Skills — Agent 导航（P0）

## 目录

- [项目定位](#项目定位)
- [当前入口](#当前入口)
- [真实验证命令](#真实验证命令)
- [协作原则](#协作原则)
- [红线](#红线)
- [踩坑教训](#踩坑教训)
- [P1 / P2 索引](#p1--p2-索引)
- [文档职责](#文档职责)
- [Agent 工具适配](#agent-工具适配)
- [AGENTS.md 变更日志](#agentsmd-变更日志)

## 项目定位

Agent Harness Skills 是面向 Trae 与主流 Agent Harness 的多 Skill 自包含发布仓库。根目录只负责索引；`skills/<name>/` 各自独立发布，不跨 Skill 引入运行时依赖，也不在根目录新增 `SKILL.md`。目标是以按需路由、单一事实源、客户端适配、模板工具和自动校验降低上下文漂移。

- **Scope**：Skill 激活与按需路由、公共事实源治理、客户端适配、模板工具及其自动校验。
- **Non-goals**：不在根目录发布 Skill；不让一个 Skill 依赖相邻 Skill 或根目录运行时文件；不把本仓库扩展为业务应用或共享运行时框架。
- **协作语言**：中文；代码、命令和路径保持原文。
- **协作模式**：单人。

## 当前入口

| 入口 | 用途 |
|---|---|
| [`README.md`](README.md) | 仓库索引、发布边界和三个现有 Skill 入口 |
| [`skills/bootstrap-agent-workspace/SKILL.md`](skills/bootstrap-agent-workspace/SKILL.md) | 工作区初始化激活与模块路由 |
| [`skills/task-handoff/SKILL.md`](skills/task-handoff/SKILL.md) | 可验证任务交接协议 |
| [`skills/spec-writing/SKILL.md`](skills/spec-writing/SKILL.md) | Spec 文档编写规范（10 段结构 + 零自由发挥 + 15 题自检） |
| [`BACKLOG.md`](BACKLOG.md) | 排期清单：当前未完成工程项；任务开始时按相关性读取 |
| [`decisions/_INDEX.md`](decisions/_INDEX.md) | 决策索引表；追溯决策时的检索入口 |

当前无单独活跃 Spec；实施以用户已确认任务和对应 Skill 内流程文档为准。

## 真实验证命令

在仓库根目录执行：

```powershell
uv run --no-project python skills/bootstrap-agent-workspace/scripts/self_check.py
uv run --no-project python -m unittest discover -s skills/bootstrap-agent-workspace/tests -v
```

## 协作原则

- 不猜测；证据不足时先询问。只做满足已确认任务所需的最小改动，不顺手重构。
- 业务行为、架构、接口或数据模型变更必须文档先行：定位现行 Spec/决策，先展示文档差异并获确认，再严格落代码。
- 优先使用 IDE 的读取、搜索、编辑、删除等专用工具；终端仅用于 Git、依赖、构建和测试。
- Bug 先报告现象、证据、影响与拟修复范围，得到确认后再修复。
- 每次会话从本文件获取当前入口；P1 仅在任务命中时读取，P2（`decisions/`）先读 `decisions/_INDEX.md` 按关键词定位，再读对应决策文件，不复制全文。

## 红线

- Git：不改 Git 配置；未经明确要求不 commit/push；禁止擅自 force push、硬重置、清理或覆盖已有改动。
- 依赖：先核对项目清单；未经确认不新增、升级或全局安装依赖，Python 工具只使用 `tools/` 共享 workspace。
- 删除：删除文件、迁移脚本或破坏性数据操作必须先确认并说明影响；不得改写已执行迁移。
- 临时文件：统一 `temp_*` 前缀命名，使用后立即删除；不得提交缓存、日志、密钥、成员级 `.venv` 或 `uv.lock`。

## 踩坑教训

每条一句话：错误做法 → 正确做法。`L-NNN` 编号从 `L-001` 递增；条目仅追加，不重排、不改既有编号；无项目证据不得预填。

- L-001：全局残留检查用 `*.md` glob 过滤，漏掉 `排期清单.md.template` 里的旧体系引用 → 一致性检查不按文件后缀过滤，模板、配置、代码注释一并扫描。

## P1 / P2 索引

| 级别 | 路径 | 读取条件 |
|---|---|---|
| P1 | `README.md` | 确认仓库定位、发布约定或 Skill 入口时 |
| P1 | `skills/<name>/SKILL.md` 及其按需路由文档 | 修改对应 Skill 或执行其流程时；不得预读未选模块 |
| P1 | `.github/workflows/bootstrap-agent-workspace.yml` | 修改或核对现有 CI 验证范围时 |
| P1 | `BACKLOG.md` | 规划任务、判断是否闭环待办时 |
| P1 | `specs/`（当前无） | 若创建 Spec：`specs/<模块>/<功能>/` 每节点三件套（spec/tasks/checklist），按项目大小裁剪层级；任务命中时读对应节点 |
| P2 | `decisions/` | 追溯决策时先读 `decisions/_INDEX.md` 按关键词定位，再读对应决策文件；`ls decisions/` 可浏览全史 |
| P2 | 归档 Spec（当前无） | 仅在追溯对应历史主题时读取 |

## 文档职责

- `AGENTS.md`：P0 唯一常驻事实源——短导航、当前入口、协作原则、安全红线、踩坑教训。
- `BACKLOG.md`（排期清单）：只保留未完成项；完成即移除，闭环在 decisions/ 新建决策文件并追加 `_INDEX.md` 索引行。
- `decisions/`：P2 决策目录，一决策一文件（`序号-版本-关键词.md`）；`_INDEX.md` 是唯一索引表。

## Agent 工具适配

| 工具 | 自动加载入口 | 状态 | 来源 | 最后确认日期 |
|---|---|---|---|---|
| Trae | `AGENTS.md` | active | 运行时证据 | 2026-08-21 |

## AGENTS.md 变更日志

- 2026-08-05：初始化规范治理短导航，登记 Trae 入口，建立 P1/P2 索引和共享工具命令。
- 2026-08-21：术语全局更名 Hermes → Agent Harness（含仓库名义和 Skill 触发词），文档体系与流程不变。
- 2026-08-21：确认 Trae 整目录加载 `.trae/rules/`，lessons 实际常驻；按用户决策接受该权衡，相关文档改为如实描述。
- 2026-08-21：迁移到三事实源体系（决策 v4）：soul 与 lessons-learned 正文并入本文件，删除 `.trae/rules/` 旧文件，闭环排期 #005。
- 2026-08-21：适配器收窄为仅 Claude Code（决策 v8）；临时文件红线改为 `temp_*` 命名 + 使用后立即删除；P1 索引新增 Spec 层级约定。
- 2026-08-21：废弃 MCP 与 changelog-rag，决策日志迁移为 `decisions/` 目录（决策 v9）；`_INDEX.md` 成为决策检索入口，删除 `tools/` 与 `.trae/`。
- 2026-08-21：补齐 v9 执行遗漏（决策 v10）：排期清单模板闭环规则改 decisions/ 工作流，drift-check D5 适配说明补新体系扫描源；登记教训 L-001。
- 2026-08-21：排期清单更名 `BACKLOG.md`（决策 v11）；中文"排期清单"保留为模块标签。
- 2026-08-21：收编 `spec-writing` 为第三个发布 Skill（决策 v12）；删除 crawl 项目专属适配声明，规范本体未改。
- 2026-08-21：初始化新增协作模式询问，AGENTS.md 项目定位标记协作模式（决策 v13）；本仓库为单人。
- 2026-08-21：删除「Agent 工具适配」小节及目录锚点（决策 v8/v9 后的残留自指记录）；Trae 入口事实由本文件被加载即证。
- 2026-08-21：上一条所述删除系误操作，「Agent 工具适配」小节与目录锚点已恢复；结构回归单人模式 11 章节，与 skill core-documents.md §4 一致。
- 2026-08-21：落地多人协同模式（决策 v14）：三层结构（共享宪法 + decisions/ + .agents/ 个人层）、起草-确认制、决策序号晋升认领与撞号规则；本仓库为单人模式，不建 .agents/。
