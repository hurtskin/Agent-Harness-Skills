# Agent Harness Skills

面向 Trae、Cursor 与主流 Agent Harness 的**三个自包含 Skill**。各自解决不同问题，组合起来形成一条 **Spec 驱动 + Hook 约束 + 可验证交接** 的 Agent 工作闭环。

> **一句话噱头（已自证边界）**  
> 用 **`bootstrap-agent-workspace` + `spec-writing` + `task-handoff`**，可以在**任意 Harness** 里拼出 **Kiro 式核心能力闭环**——不是 Kiro IDE 的复刻，而是把它的三条主线（**立规 / Hook 防漂 / 行为可证**）拆成可独立发布的 Skill；另加 **多人协同** 与 **长任务交接**，Kiro 本身并不强调后者。

---

## 三个 Skill，各管一段

| Skill | 一句话 | 独有特点 |
|---|---|---|
| [**bootstrap-agent-workspace**](./skills/bootstrap-agent-workspace/SKILL.md) | **先问诊，再装工作区** | 按项目规模选套餐（微型→大型）；生成 `AGENTS.md` + `decisions/` + 排期；可选 **path-align**、**verify-matrix**、**drift-inventory** 模板；**Harness 通用**，换工具零迁移 |
| [**spec-writing**](./skills/spec-writing/SKILL.md) | **Spec 写到能直接复刻代码** | 强制 **10 段** + **零自由发挥** + **15+2 自检**；Properties 行为不变量；`inventory.yaml` + Correctness **变更门**（写 P / 跑 PT 分轨） |
| [**task-handoff**](./skills/task-handoff/SKILL.md) | **换 Agent 不断档** | 接任子代理 **审问**旧 Agent；证据化 YAML 状态机；`READY` / `BLOCKED` 门禁；最多 3 轮追问 + 终审 |

没有「主 Skill + 两个附件」——三个都可以**单独安装、单独触发**；组合时才形成完整闭环。

---

## Kiro 式闭环：怎么对应、差在哪

Kiro 公开叙事里反复出现的三件事：**Spec 当事实源**、**Hook 在关键节点拉住 Agent**、**Correctness / Properties 证明行为**。下面是对照（非官方对标）：

| Kiro 主线 | 本仓库谁负责 | 覆盖程度 |
|---|---|---|
| Spec 驱动开发 | `spec-writing` | ✅ 10 段 + 三件套 + 零自由发挥；偏「写规」而非 IDE 内置 Spec 面板 |
| Agent Hooks | `bootstrap` 装机 + 接线 | ✅ **双层守门**：① **turn-end** `turn_align` — L0 路径成对 nudge；② **pre-commit 兜底** — verify-matrix（PBT / example / contract，staged 命中 `watch` 才跑）+ drift-inventory（L1/L2 inventory 比对）。三层互补，不是「只有轻量 L0」。⚠️ 接线 Harness 无关、项目自建，非 Kiro IDE 内置 hook 商店 |
| Correctness / Properties | `spec-writing` + verify-matrix | ✅ `P-*` / `PT-*` + **变更门**；PT 由 pre-commit hook 或手动 `run_verify` 执行；⚠️ 矩阵与解释器由项目维护，非 IDE 内置 PBT 流水线 |
| 长会话 / 换 Agent 不断档 | `task-handoff` | ➕ **本组合额外能力**，非 Kiro 宣传重点 |
| 多人各带 AI 不撕规范 | `bootstrap` 多人协同 | ➕ **本组合额外能力**（`.agents/` + 决策晋升） |

**结论**  
- ✅ 「**拼出 Kiro 式 Spec + Hook + Correctness 闭环**」——三条主线都有对应 Skill，且可在一个消费者项目里串起来。  
- ❌ 「**等于 Kiro** / 功能完全等价」—缺 IDE 一体化、缺 Kiro 原生工具链深度、Correctness 需自行装机与矩阵维护。  
- ✅ 「**在 Cursor/Trae 里用三个 Skill 获得同类纪律**」——且比绑死单一 IDE 更轻、可拆分。

### Hook 双层守门（bootstrap 装机）

Kiro 的 hook 叙事是「关键节点拉住 Agent」——本组合用 **两个触发点** 覆盖路径、结构与行为，互为兜底：

| 触发点 | 入口 | 守门内容 | 模板路径 |
|---|---|---|---|
| **Agent turn-end** | `turn_align`（Harness 轮次结束 hook） | **L0 路径成对**：契约侧 ↔ 实现侧 dirty 是否同现 | `tools/path_align_hooks/` |
| **`git commit` 前** | `pre_commit_entry` → `run_verify -PreCommit` | **Correctness**：matrix `watch` 命中才跑 PBT / example / contract | `specs/verification/hooks/` |
| **`git commit` 前** | `run_drift` / 合并 pre-commit 脚本 | **结构漂移**：inventory L1 计数 + L2 符号名 | `specs/drift/` + [`pre-commit-combined.example`](./skills/bootstrap-agent-workspace/templates/spec_hooks/pre-commit-combined.example) |

- turn-end 漏网 → pre-commit 在提交前再拦一层；无 Harness hook 时仍可只装 pre-commit 兜底。
- path-align **不替代** verify / drift；三者分层，用法见 spec-writing [`tools/`](./skills/spec-writing/tools/)。

### 组合闭环（示意）

```text
  ┌─────────────────────────────────────────────────────────┐
  │  bootstrap-agent-workspace                              │
  │  AGENTS 宪法 · 套餐装机 · path-align · verify/drift 模板 │
  └──────────────────────────┬──────────────────────────────┘
                             │ 消费者项目就绪
                             ▼
  ┌─────────────────────────────────────────────────────────┐
  │  spec-writing                                           │
  │  立 Spec / inventory · Properties · 变更门 · 跑 matrix   │
  └──────────────────────────┬──────────────────────────────┘
                             │ 实施 + hook / pre-commit 守门
                             ▼
                    （你的业务代码）
                             │
         上下文满 / 换 Agent  ▼
  ┌─────────────────────────────────────────────────────────┐
  │  task-handoff                                           │
  │  子代理审问 · 证据化交接包 · READY/BLOCKED               │
  └──────────────────────────┬──────────────────────────────┘
                             └──► 新会话接着干，约束不丢
```

---

## Skill 1：`bootstrap-agent-workspace` — 工作区与守门基础设施

**特点：问诊式初始化，按规模开方，不一次性堆工具。**

| 套餐 | 适合 | 装什么 |
|---|---|---|
| 快速开始 | 微型：脚本、Demo、文档仓 | 核心文档 + 排期 |
| 敏捷迭代 | 小型：兼职、小程序、MVP | + **path-align**（L0 路径成对） |
| 规范交付 | 中型：有 Spec、要提交前门控 | + **verify-matrix** + **drift-inventory**（含 **pre-commit 兜底** hook） |
| 大型协作 | 大型：多人长周期 | 同规范交付 + **多人协同**骨架 |

**多人协同**（大型协作独有卖点）：共享宪法 Git 跟踪（`AGENTS.md`、`decisions/`），个人上下文进 `.agents/<成员>/` 且 **Git 忽略**；决策 **起草-确认-晋升**，序号冲突靠 `_INDEX.md` 尾部撞号报警。

**path-align（L0，turn-end）**：轮次结束只看 dirty 路径——契约侧（`specs/` / openapi / schema）与实现侧（`skills/` / `src/`）是否同现；不做行为证明。模板在 [`templates/path_align_hooks/`](./skills/bootstrap-agent-workspace/templates/path_align_hooks/)。

**verify / drift（pre-commit 兜底）**：`git commit` 前跑 matrix 命中模块（PBT 等）与 inventory 漂移检查；可与 path-align 合并接线，见 [`templates/spec_hooks/`](./skills/bootstrap-agent-workspace/templates/spec_hooks/)。

> 本 **Skill 发布仓**不以 Spec 驱动日常开发，本地 **不启用** path-align Cursor hook；模板给消费者项目 bootstrap 安装。

入口：[`skills/bootstrap-agent-workspace/SKILL.md`](./skills/bootstrap-agent-workspace/SKILL.md)

---

## Skill 2：`spec-writing` — 契约写到机器可读

**特点：把「需求文档」写成「实施许可证」——字段级钉死，AI 不能自由发挥。**

- **10 段强制结构** + **11 维零自由发挥** + 落地前 **15+2 题自检**（不过自检不准实施）
- **Properties**（`P-*` / `PT-*`）：关键行为写成 ∀ oracle；与 path-align 分层，与 **Correctness 变更门**绑定（命中才跑 PT）
- **`inventory.yaml`**：与 spec 三件套同目录；供 drift-inventory 做 L1 计数 + L2 符号名（跨语言 baseline）
- **工具用法在本 Skill**：bootstrap 只装机；[`tools/enablement.md`](./skills/spec-writing/tools/enablement.md) 先检测项目是否启用 verify / drift

入口：[`skills/spec-writing/SKILL.md`](./skills/spec-writing/SKILL.md)

---

## Skill 3：`task-handoff` — 可验证的任务交接

**特点：不靠「帮我总结一下」——靠子代理审问 + 证据链 + 状态机。**

- 接任子代理 **无状态**，临时 handoff 文件是跨轮唯一记忆
- 关键结论必须 **VERIFIED**（文件 / diff / 测试引用）或明确 **unverified**
- 输出 **READY** / **READY_WITH_RISKS** / **BLOCKED**；BLOCKED 不假装能无缝接管
- 适合：上下文将满、换 Agent、多人接力、决策多且怕摘要丢约束

入口：[`skills/task-handoff/SKILL.md`](./skills/task-handoff/SKILL.md)

---

## 验证分层（消费者项目）

| 层 | 工具 | 典型触发 | 谁安装 | 谁写用法 |
|---|---|---|---|---|
| L0 路径成对 | path-align | turn-end `turn_align` | bootstrap | bootstrap 模板 |
| L1/L2 结构漂移 | drift-inventory | pre-commit `run_drift` | bootstrap | spec-writing |
| Correctness | verify-matrix | pre-commit `pre_commit_entry` | bootstrap | spec-writing |
| 交接门禁 | task-handoff | 流程触发（换 Agent） | —（纯流程 Skill） | task-handoff |

---

## 真实案例

[《拼多多拉图工具 vibecoding 全过程复盘》](./docs/case-study-pdd.md)：决策可溯、Spec 层级、多 Agent 并行——对应 **bootstrap 多人协同 + spec-writing 契约纪律 + task-handoff 不断档** 要解决的问题。

---

## 安装

每个 Skill 自包含，复制到 Harness 的 skills 目录即可（目录名 = frontmatter `name`）：

```text
<skills-root>/bootstrap-agent-workspace/
<skills-root>/spec-writing/
<skills-root>/task-handoff/
```

根目录索引见 [`AGENTS.md`](./AGENTS.md)；本仓发布验证：

```powershell
uv run --no-project python skills/bootstrap-agent-workspace/scripts/self_check.py
uv run --no-project python -m unittest discover -s skills/bootstrap-agent-workspace/tests -v
```

## License

[MIT](./LICENSE)
