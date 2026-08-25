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
- **Non-goals**：不在根目录发布 Skill；不让一个 Skill 依赖相邻 Skill 或根目录运行时文件；不把本仓库扩展为业务应用或共享运行时框架；**本发布仓不以 Spec 三件套驱动日常开发**（`specs/` 仅可作本地沙箱，不跟踪入库）。
- **协作语言**：中文；代码、命令和路径保持原文。
- **协作模式**：单人。

## 当前入口

| 入口 | 用途 |
|---|---|
| [`README.md`](README.md) | 仓库索引、发布边界和三个现有 Skill 入口 |
| [`skills/bootstrap-agent-workspace/SKILL.md`](skills/bootstrap-agent-workspace/SKILL.md) | 工作区初始化激活与模块路由 |
| [`skills/task-handoff/SKILL.md`](skills/task-handoff/SKILL.md) | 可验证任务交接协议 |
| [`skills/spec-writing/SKILL.md`](skills/spec-writing/SKILL.md) | Spec 文档编写规范（10 段结构 + Properties 推荐 + 零自由发挥 + 15+2 题自检） |
| [`BACKLOG.md`](BACKLOG.md) | 排期清单：当前未完成工程项；任务开始时按相关性读取 |
| [`decisions/_INDEX.md`](decisions/_INDEX.md) | 决策索引表；追溯决策时的检索入口 |

当前无单独活跃 Spec；实施以用户已确认任务和对应 Skill 内流程文档为准。

## 真实验证命令

在仓库根目录执行：

```powershell
uv run --no-project python scripts/check_links.py
uv run --no-project python skills/bootstrap-agent-workspace/scripts/self_check.py
uv run --no-project python -m unittest discover -s skills/bootstrap-agent-workspace/tests -v
# Windows:    powershell -NoProfile -ExecutionPolicy Bypass -File skills/task-handoff/scripts/validate_handoff.ps1 <handoff.md>
# Linux/macOS: bash skills/task-handoff/scripts/validate_handoff.sh <handoff.md>
uv run --no-project python -m unittest discover -s skills/task-handoff/tests -v
```

`task-handoff` 校验器为 PowerShell / bash+gawk 双语言等价实现（`skills/task-handoff/scripts/validate_handoff.{ps1,sh}`），同构、同失败语义。本仓不把 Hypothesis / `specs/**/pilot` 列入发布验证；Correctness 思想写在 `spec-writing` Skill 内，供消费者项目按变更门选用。

## 协作原则

- 不猜测；证据不足时先询问。只做满足已确认任务所需的最小改动，不顺手重构。
- 业务行为、架构、接口或数据模型变更必须文档先行：定位现行 Spec/决策，先展示文档差异并获确认，再严格落代码。
- **路径成对（L0，stop / drift-lite）**：不看文件内容是否正确，只看本轮 git dirty 是否同时触及「契约侧」与「实现侧」。只改一侧会记 `CODE_WITHOUT_SPEC` 或 `SPEC_WITHOUT_CODE`，默认可能 followup 催补；`PATH_ALIGN_NUDGE=0` / `STOP_ALIGN_FOLLOWUP=0` 可关闭催改。这不是 Correctness/行为证明，只防明显单边漂移。**本发布仓**不跟踪 `specs/`、也不以 Spec 驱动开发——改 `skills/` 文档时不必强行补 `specs/`（可 A2 说明故意单边）；该约定主要服务装了路径成对钩子的**消费者项目**。**本仓本地不启用** Cursor path-align hook（`.cursor/hooks.json` 无 `stop` 接线）；模板仅随 bootstrap 发给消费者。
  - **契约侧**（消费者）：`specs/`、路径含 `openapi`、`*.schema.json`
  - **实现侧**：`skills/` / `src/` / 常见源码后缀（以脚本为准）
  - **不参与配对**：`.cursor/`、已 gitignore 的沙箱等工具目录；仅改导航文档不触发成对告警
- **Correctness 变更门**（写给 Skill 消费者）：写 `P-*` 与跑 `PT-*` 分轨；命中相关实现或性质正文才跑对应 PT。本仓不强制、不嵌入全仓 PBT。细则见 `skills/spec-writing/SKILL.md`。
- **drift-inventory**：结构漂移 L1/L2（inventory + regex profile）；**verify-matrix**：Correctness 验证；bootstrap 完整工具链默认 = 核心 + 排期 + 路径成对；规范交付套餐加 verify + drift。
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
- L-002：新写的 Python 脚本直接 `print` 中文，本机 UTF-8 控制台全绿，CI Windows runner（默认 cp1252）`UnicodeEncodeError` 崩溃 → 脚本入口加 `configure_output_encoding()` 把 stdout/stderr reconfigure 为 UTF-8（模式见 `skills/bootstrap-agent-workspace/scripts/self_check.py`），并可在本地用强制 cp1252 复现验证。

## P1 / P2 索引

| 级别 | 路径 | 读取条件 |
|---|---|---|
| P1 | `README.md` | 确认仓库定位、发布约定或 Skill 入口时 |
| P1 | `skills/<name>/SKILL.md` 及其按需路由文档 | 修改对应 Skill 或执行其流程时；不得预读未选模块 |
| P1 | `.github/workflows/bootstrap-agent-workspace.yml` | 修改或核对现有 CI 验证范围时 |
| P1 | `BACKLOG.md` | 规划任务、判断是否闭环待办时 |
| P1 | `specs/`（本仓不跟踪） | 消费者项目 Spec 布局约定仍为 `specs/<模块>/<功能>/` 三件套；本发布仓 `specs/` 已 gitignore，仅本地沙箱可选 |
| P1 | `.cursor/hooks/`（可选） | 维护宿主本地 hook 接线时；默认不预读。通用脚本模板在 `skills/bootstrap-agent-workspace/templates/path_align_hooks/` |
| P2 | `decisions/` | 追溯决策时先读 `decisions/_INDEX.md` 按关键词定位，再读对应决策文件；`ls decisions/` 可浏览全史 |
| P2 | 归档 Spec（当前无） | 仅在追溯对应历史主题时读取 |

## 文档职责

- `AGENTS.md`：P0 唯一常驻事实源——短导航、当前入口、协作原则（含路径成对约定）、安全红线、踩坑教训。
- `BACKLOG.md`（排期清单）：只保留未完成项；完成即移除，闭环在 decisions/ 新建决策文件并追加 `_INDEX.md` 索引行。
- `decisions/`：P2 决策目录，一决策一文件（`序号-版本-关键词.md`）；`_INDEX.md` 是唯一索引表。
- `specs/`：本发布仓**不跟踪**；消费者项目中的契约侧布局仍推荐 `specs/<模块>/<功能>/`。本地可留 `specs/**/pilot` 作 Correctness 沙箱，不入库。
- `.cursor/hooks/` + `tools/path_align_hooks/`：宿主本地接线（若有）与通用 L0 路径成对脚本；行为以脚本为准，约定以本文件「路径成对」为准。bootstrap 模板在 `skills/bootstrap-agent-workspace/templates/path_align_hooks/`。

## Agent 工具适配

| 工具 | 自动加载入口 | 状态 | 来源 | 最后确认日期 |
|---|---|---|---|---|
| Trae | `AGENTS.md` | active | 运行时证据 | 2026-08-21 |

## AGENTS.md 变更日志（可选，决策 v21）

> 本节为可选人类时间线展示（决策 v21）；只挂结构级变化（章节增删 / 协作原则改写 / 模板验收清单改写 / v* 决策落地）。过程性条目（修脚本 / 加注释 / 删错别字）走 `decisions/_INDEX.md` 而非变更日志。追溯唯一入口：决策关键词检索 `decisions/_INDEX.md`。

- 2026-08-05：初始化规范治理短导航，登记 Trae 入口，建立 P1/P2 索引和共享工具命令。
- 2026-08-21：术语全局更名 Hermes → Agent Harness（决策 v2）。
- 2026-08-21：迁移到三事实源体系（决策 v4）：soul 与 lessons-learned 并入本文件。
- 2026-08-21：适配器收窄为仅 Claude Code（决策 v8）；临时文件红线改为 `temp_*` 命名。
- 2026-08-21：废弃 MCP 与 changelog-rag，决策日志迁移到 `decisions/` 目录（决策 v9）。
- 2026-08-21：落地多人协同模式（决策 v14）：三层结构 + 起草-确认制；本仓库单人，不建 `.agents/`。
- 2026-08-22：协作原则增补路径成对（L0 / stop·drift-lite）（决策 v15）。
- 2026-08-22：`bootstrap-agent-workspace` 增加「路径成对钩子」模块 + 移除遗留 `drift-check` 模板（决策 v15）。
- 2026-08-22：新增 `scripts/check_links.py` 仓库级链接校验（目标缺失 + 被 gitignore 两类死链）。
- 2026-08-25：v17/v18/v19/v20 决策序列落地（path-align + verify-matrix + drift-inventory 自动接线与路径硬假设收敛）。
- 2026-08-25：变更日志章节本身从必填改为可选（决策 v21）；未来过程性条目不再默认追加。
