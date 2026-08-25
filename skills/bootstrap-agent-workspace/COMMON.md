# 公共初始化流程

> 本文件是 `bootstrap-agent-workspace` 的跨工具唯一公共流程。`SKILL.md` 负责激活与索引；所有原生加载 `AGENTS.md` 的工具无需适配，`adapters/claude-code.md` 仅处理 Claude Code 的 `CLAUDE.md` 入口差异。

## 1. 单一事实源

无论激活哪个工具，都只维护以下项目事实源：

| 文件 | 职责 |
|---|---|
| `AGENTS.md` | P0 唯一常驻事实源：短导航与当前入口、协作原则、安全红线、踩坑教训；所有 Agent Harness 原生加载，换工具零迁移 |
| `decisions/` | P2 决策目录：一决策一文件，文件名自带版本与关键词；`_INDEX.md` 是唯一索引表，追溯时按关键词定位后局部读取 |
| `BACKLOG.md` | 仅保存未完成事项；完成后清除，闭环写入 decisions/ |

协作原则与教训不建独立文件（如 `soul.md`、`lessons-learned.md`），直接作为 `AGENTS.md` 章节维护，顶部锚点目录提供跳转。多人协同模式的 `.agents/` 个人层（各成员的上下文与草稿）不属于公共事实源，Git 不跟踪。

工具入口文件不得复制完整项目事实，只能：

1. 声明当前工具和加载方式。
2. 指向上述事实源。
3. 写入该工具无法通过引用表达的最小关键规则。
4. 说明冲突优先级与验证方式。

## 2. 初始化后运行时分级加载契约

本节只约束初始化完成后的日常客户端上下文加载，不改变 `SKILL.md` 在初始化阶段“先确认模块、再按需读取流程文档”的路由。

| 级别 | 运行时职责 | 内容与长度边界 | 默认文件 |
|---|---|---|---|
| **P0 / Always** | 每次会话必须立即可见的安全边界、稳定协作原则、踩坑教训和当前入口 | 只保留跨多数任务都成立、遗漏会导致错误执行的内容；使用短段落或清单，不放历史、详细架构、完整流程或重复事实 | `AGENTS.md`（唯一常驻事实源） |
| **P1 / Indexed** | 可被入口定位、按任务相关性选择读取的工作上下文 | 保存路径索引、主题摘要、适用条件和读取提示；入口只指向事实源，不复制正文 | 活跃 Spec、架构文档、`BACKLOG.md` 及客户端条件规则 |
| **P2 / On-demand** | 仅在排障、追溯或特定主题命中时读取的历史与经验 | 可持续追加，但条目应可检索、可局部读取；不得由入口复制或主动导入 | `decisions/`（入口 `_INDEX.md`）、归档 Spec |

执行规则：

1. P0 必须精简；内容不再对多数会话必要时，下沉到 P1 或 P2，并在 `AGENTS.md` 保留入口。
2. P1 不等于自动加载全文。客户端支持原生引用或条件规则时，只按能力建立索引或触发；能力不明时使用薄入口列出路径和读取条件。
3. P2 默认不被入口直接导入；需要时通过索引关键词定位、锚点或局部范围读取。决策检索固定走 `decisions/_INDEX.md`，不依赖任何检索工具。
4. 同一事实源只允许一条默认自动加载路径。客户端已原生加载 `AGENTS.md` 时，不再通过配置或另一入口重复导入。
5. 冲突按“客户端不可绕过的安全与格式约束 > 项目安全红线 > 当前已确认 Spec / 任务约束 > 索引与历史记录”处理。同级冲突以更具体、更新且有证据的事实源为准；仍无法消解时停止并询问用户。
6. 分级描述的是加载优先级，不改变公共事实源路径，也不得以复制内容的方式制造第二事实源。

## 3. 启动自检

进入初始化前必须确认：

1. 当前目录是项目根目录且可读写。
2. 识别现有事实源、工具入口和配置文件。
3. 已有文件默认升级，不覆盖；重建必须用户明确授权。
4. `AGENTS.md` 的协作原则与红线章节必须包含文档先行、Git/依赖/删除红线和临时文件红线。
5. `templates/kanban/BACKLOG.md.template` 存在。
6. 当前工具为 Claude Code 时，`adapters/claude-code.md` 存在且声明了检测信号、自动加载入口、生成策略和校验方式；其他原生加载 `AGENTS.md` 的工具无需适配器。

## 4. Agent Harness 识别

按下列顺序识别，可同时命中多个工具：

1. **运行时证据**：当前客户端或系统上下文明确声明工具名称。
2. **项目配置**：扫描已知目录与文件，例如 `.trae/`、`.claude/`、`.codex/`、`opencode.json`、`.pi/`、`.qoder/`。
3. **项目入口**：扫描 `CLAUDE.md`、`AGENTS.md` 及工具专属入口。
4. **用户确认**：若存在多个候选、证据冲突或无法识别，使用结构化问题询问。

无法确定时依次问：

- 当前使用哪个 Agent Harness？
- 该工具会自动加载项目中的哪个目录或文件？
- 是生成新入口、升级现有入口，还是只保留公共 `AGENTS.md`？

确认结果仅在 `AGENTS.md` 已存在或本次选择核心工作区文档时写入其“Agent 工具适配”表，至少记录：工具、自动加载入口、来源和最后确认日期。否则只在本次执行结果中报告，不得为记录适配状态而创建 `AGENTS.md`。已有适配表后优先复用；只有入口丢失或配置冲突时才再次询问。

## 5. 项目上下文识别

并行读取：

- 仓库根目录结构
- `pyproject.toml`、`package.json`、`Cargo.toml`、`go.mod` 等项目清单
- README 项目简介
- 入口文件和测试配置
- 已有 Agent 规则与历史记录

需要确认的核心字段：

- `project_name`
- `project_type`
- `project_goal`
- `scope` 与 `non_goals`
- 用户角色与工作语言
- `collaboration_mode`：单人 / 多人协同
- `team_members`：多人协同时的成员名单（git user.name 标识；当前用户优先从 `git config user.name` 推断）
- 部署形态
- 项目级红线

有证据则推断；无证据则询问，不猜多问。

## 6. 按需初始化

启动时由 `SKILL.md` 一次询问用户需要的模块，并只加载对应文档：

| 模块 | 流程文档 |
|---|---|
| 核心工作区文档 | `workflows/core-documents.md` |
| 排期清单 | `modules/kanban.md` |
| 路径成对钩子 | `modules/path-align-hooks.md` |
| verify-matrix | `modules/verify-matrix.md` |
| drift-inventory | `modules/drift-inventory.md` |

未选择的模块不得生成产物、安装依赖或注入强制规则。套餐「敏捷迭代」及以上默认含路径成对钩子；「规范交付 / 大型协作」含 verify-matrix + drift-inventory。

生成或升级工具入口（如 `CLAUDE.md`）前必须形成产物清单：

1. `existing_artifacts`：项目中实际存在的公共文档和工具入口。
2. `selected_artifacts`：用户所选模块将生成或升级的产物。
3. `available_artifacts`：上述两者的并集。

工具入口生成只能消费 `available_artifacts`：只能生成客户端原生入口或配置，只能引用其中实际存在或确定将生成的文件；不得自行创建 `AGENTS.md`、decisions/ 或 `BACKLOG.md`。客户端原生入口依赖的公共文件不可用时，应跳过入口、保留已有入口不动，或只写不产生失效引用的最小配置。

## 7. 文档先行硬流程

以下流程适用于目标项目的业务代码、架构、接口、数据模型和行为规则变更，不适用于按本 Skill 已确认模块流程复制或安装工具模板。

项目代码修改必须：

1. 定位相关 Spec、决策和教训。
2. 读现行文档并列出“文档现状 / 计划变化”。
3. 先改文档，展示差异并等待用户确认。
4. 严格按文档改代码，不二次发挥。
5. 运行项目实际安装的验证工具（verify-matrix / drift-inventory 按 AGENTS 表与 spec-writing 启用检测）。
6. 只回写 `available_artifacts` 中已生成且与本次变更相关的 decisions/（新建决策文件 + `_INDEX.md` 追加行）、文档目录树、排期与 AGENTS.md 踩坑教训章节。

工具模板初始化严格按用户已确认的模块文档执行，不得因此补建未选核心文档；若初始化同时改变项目架构、接口或运行行为，则相关项目变更部分仍须执行上述文档先行流程。

工具适配入口只负责让当前工具加载该流程，不得另建相互冲突的流程副本。

### 6.1 v17/v18 自动接线 dogfood 步骤（消费者项目首次初始化必跑）

> 本节是决策 v17（path-align 宿主 hook 自动接线）+ v18（pre-commit 自动注册）的最小落地证据。执行 Agent 在消费者项目首次 bootstrap（自定义能力含 path-align 或 verify-matrix / drift-inventory）后必须按本节跑一次最小试跳并把证据贴回执行结果；未跑 = 该模块初始化未闭环。决策闭环参考：发布仓 `decisions/019-v19-v17-v18-dogfood-closure.md`（消费者项目按自身事实源定位本仓对应决策）。

#### 6.1.1 路径成对（path-align，含 turn-end 自动接线）

> 决策 v17：模板脚本必须物理落地到目标项目 `tools/path_align_hooks/`；宿主 hook 配置按当前 Harness 提示生成并注册。

```powershell
# 1) 复制模板（如已复制则跳过）
Copy-Item -Recurse -Force skills/bootstrap-agent-workspace/templates/path_align_hooks/* tools/path_align_hooks/

# 2) 最小事件试跳（不解 stdin 时给空 payload）
echo '' | powershell -NoProfile -ExecutionPolicy Bypass -File tools/path_align_hooks/turn_align.ps1

# 期望：stderr 含 [turn_align] status=... parse_ok=...；exit 0；stdout 为 `{}` 或 nudge JSON。
```

宿主 hook 接线（示例：Cursor `stop` 事件）：

```json
{
  "version": 1,
  "hooks": {
    "stop": [
      {
        "command": "powershell -NoProfile -ExecutionPolicy Bypass -File tools/path_align_hooks/turn_align.ps1",
        "cwd": "<repo-root>",
        "env": { "PATH_ALIGN_NUDGE": "1" }
      }
    ]
  }
}
```

未识别 Harness → **必问用户**（不得默认套 Trae / 不得默认跳过）。详见 [`modules/path-align-hooks.md`](./modules/path-align-hooks.md)。

#### 6.1.2 验证矩阵 + 结构漂移（pre-commit 自动注册）

> 决策 v18：模板复制到 `specs/verification/`（含 `hooks/pre_commit_entry.{ps1,sh}`、`run_verify.{ps1,sh}`、`.pre-commit-config.yaml.example`）；Agent 按当前 Harness pre-commit 机制（pre-commit 框架 / Git 原生 hook / 必问）选一套自动生成宿主配置并安装。

```powershell
# 1) 复制模板
Copy-Item -Recurse -Force skills/bootstrap-agent-workspace/templates/spec_verification specs/verification

# 2) 最小试跳（无 staged watch 时应 nothing to run）
powershell -NoProfile -ExecutionPolicy Bypass -File specs/verification/hooks/pre_commit_entry.ps1 -Python python

# 期望：stderr 含 `[verify] pre-commit: nothing to run (ok)`；exit 0。
```

宿主 pre-commit 接线二选一：

- **pre-commit 框架**：`Copy-Item specs/verification/.pre-commit-config.yaml.example .pre-commit-config.yaml` + `pre-commit install`。
- **Git 原生 hook**：`Copy-Item specs/verification/hooks/pre-commit.example .git/hooks/pre-commit`（Windows 用 `.ps1.example`）。

未识别 Harness → **必问用户**。详见 [`modules/verify-matrix.md`](./modules/verify-matrix.md) §3 与 [`templates/spec_verification/hooks/README.md`](./templates/spec_verification/hooks/README.md)。

#### 6.1.3 失败兜底（必问 / 跳过 / 留模板）

任一自动接线步骤遇到下列情况即停止推进，在执行结果中汇报「**未识别 Harness / 宿主不支持 / 物理布局冲突**」并保留模板，等待用户决策：

- 未识别 Harness（无法从 SKILL §1.2 推断）。
- 宿主不支持 turn-end / pre-commit 任一事件。
- **模板物理布局与目标项目布局冲突（兜底，已被决策 v20 大幅收敛）**：
  - v20 已用 `__file__` / `$PSScriptRoot` / `git rev-parse --show-toplevel` 三层回退替代 `..\..` / `inventory_path.parent.parent` 等硬假设；`drift_inventory.py` / `pre_commit_entry.{ps1,sh}` 跨 `specs/`、`tools/`、项目约定目录均可工作，**无需改脚本**。
  - 仍保留本兜底分类的原因：(a) 消费者项目历史副本未同步刷新到 v20+ 模板；(b) 消费者自定义路径走偏（如 `run_verify.ps1` 找不到 `matrix.yaml`，因 `matrix.yaml` 不在脚本同目录）；(c) 模板外脚本（如旧版 `drift_inventory.py`）未升级。
  - 处置：发现冲突 → 拉取最新 `templates/`（`Copy-Item -Recurse -Force skills/bootstrap-agent-workspace/templates/spec_verification specs/verification` 等）+ 重跑 §6.1.1 / §6.1.2 试跳；仍冲突则在执行结果中标记「物理布局冲突」并保留模板，等用户决策。

发布仓自身（`Agent Harness Skills`）按 AGENTS.md 变更日志 2026-08-22 决定**故意不接** `.cursor/hooks.json` 的 stop 与 `.git/hooks/pre-commit`；dogfood 步骤仍按 §6.1.1 / §6.1.2 跑通脚本试跳，作为决策 v19 闭环证据；v20 路径硬假设收敛已在决策 `020-v20-script-path-anchor-hardcoded-layout.md` 闭环。

## 8. 验收

完成后读取 `workflows/verification.md`，只校验用户选择的模块。通用检查：

1. 公共事实源职责不重叠。
2. 实际生成或复用工具入口时，该入口有效；`AGENTS.md` 可用时存在适配记录，否则执行结果已报告适配状态。
3. 工具入口不复制决策历史或 AGENTS.md 正文。
4. P0 只包含稳定原则、踩坑教训与当前入口；P1/P2 有明确路径和读取条件，decisions/ 未进入无条件自动加载链。
5. 同一事实源没有通过客户端原生入口、引用或配置重复自动加载。
6. 未选模块没有残留配置、依赖或失效命令。
7. 未确认入口标记为 `pending-confirmation`；因缺少未选公共产物而主动跳过入口时，不判为失败。

## 9. 异常处理

| 场景 | 处理 |
|---|---|
| 用户中途停止 | 保留已生成文件，询问是否回滚 |
| 文件已存在 | 默认升级，只补缺失内容 |
| 工具入口未知 | 询问自动加载目录或文件并记录 |
| 多工具同时使用 | 共享 `AGENTS.md` 事实源；Claude Code 额外生成薄入口 |
| 工具规则冲突 | 工具专属安全/格式约束优先；项目事实以公共事实源为准；无法消解时询问用户 |
| 工具版本变化 | 重新核实官方文档或用户本地配置，不沿用过期假设 |
