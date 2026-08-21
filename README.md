# Agent Harness Skills

面向 Trae 与主流 Agent Harness 的可独立发布 Skills 集合。

本仓库要解决的不只是「把规则文件拷进项目」，而是让 Agent 协作**靠契约推进**：什么能改、改了要同步什么、关键行为如何写清——尽量少靠口述记忆。工作区初始化、Spec 写法、任务交接，是同一条线上的三块积木。

## 这次更靠近什么

相对早期「建好 AGENTS / decisions 就能干活」，当前重心多了一层**规范化契约**：

| 层级 | 做什么 | 重不重 |
|---|---|---|
| **工作区宪法** | `AGENTS.md` + `decisions/` + 排期；换 Harness 仍读同一套事实 | 默认就要 |
| **路径成对（L0）** | 轮次结束看 dirty：契约侧与实现侧是否同现，防单边改 | 轻；完整工具链默认带 |
| **Spec 契约** | 10 段钉死 + 零自由发挥；关键行为可写 Properties（∀ 思路） | 按需；写法进 `spec-writing` |
| **行为 Correctness** | 改到相关实现再跑对应性质测试 | **思想可借鉴，本仓库不强制、不重型嵌入** |

本发布仓库本身**不是** Spec 驱动业务仓：不以全仓 PBT / Hypothesis 为门禁；轻量约定写进 Skill，重型靶标留给消费者项目自己选。

## 三块积木

| Skill | 角色 | 入口 |
|---|---|---|
| **`bootstrap-agent-workspace`** | 问诊式初始化工作区：宪法、决策档案、套餐化可选能力（含路径成对钩子） | [`skills/bootstrap-agent-workspace/SKILL.md`](./skills/bootstrap-agent-workspace/SKILL.md) |
| **`spec-writing`** | 把需求写成可复刻契约：10 段结构、零自由发挥、15+2 自检；推荐 Properties + Correctness **变更门**（写 P / 跑 PT 分轨，命中才测） | [`skills/spec-writing/SKILL.md`](./skills/spec-writing/SKILL.md) |
| **`task-handoff`** | 长任务可验证交接，降低换会话丢上下文 | [`skills/task-handoff/SKILL.md`](./skills/task-handoff/SKILL.md) |

三者可单独发布；`bootstrap` 负责「项目里怎么协作」，`spec-writing` 负责「单份契约怎么写到实施不自由发挥」，`task-handoff` 负责「会话之间怎么交接」。

---

## bootstrap-agent-workspace：先问诊，再开方

解决：AI 每次从零开始、规范靠口述、决策没人记得、多人互相覆盖。

它不是「复制一套模板完事」，而是 AI 主导的按需组装：

```text
1. 问诊   读仓库证据，推断项目与协作模式；没证据就问，不瞎猜
2. 选套餐 只问效果，不甩模块名：
          1. 快速开始（推荐）：协作说明 + 决策目录 + 待办排期
          2. 完整工具链：再加轮次结束「路径成对」提醒（契约侧 ↔ 实现侧）
          3. 自定义：自己勾选（含可选高级 drift-check；偏 Python，非默认）
3. 确认   汇报将生成的产物，你点头才动手；已有文件默认增量升级
4. 生成   只加载选中模块；未选不装、不注入规则
```

### 初始化后的核心产物

```text
project/
├── AGENTS.md       # AI 宪法：原则、红线、教训、当前入口（换工具仍加载）
├── BACKLOG.md      # 未完成排期
└── decisions/      # 一决策一文件 + _INDEX.md 关键词索引
```

Trae / Codex / OpenCode / Pi / Qoder 等原生加载 `AGENTS.md`；Claude Code 额外生成 `CLAUDE.md` 薄入口。

### 单人日常

```text
新会话   读 AGENTS.md → 原则与入口齐了
做决策   验证通过后落 decisions/，登记 _INDEX.md
踩了坑   在 AGENTS.md 教训区追加「错误 → 正确」
待办     BACKLOG 进出；闭环进 decisions/
契约改动 若装了路径成对钩子：只改实现或只改契约时会被提醒补另一侧
```

单人模式下你是确认闸门：AI 起草，你点头再生效。

### 多人模式（核心设计）

痛点：共享文件人人冲突，各写各的又会裂成三套「项目灵魂」。

答案：**共享宪法 Git 跟踪，个人上下文 Git 忽略，人做晋升闸门。**

```text
project/
├── AGENTS.md / BACKLOG.md / decisions/   # 宪法 + 决策 ⭐ 跟踪；AI 起草-确认
└── .agents/<成员>/context.md + scratchpad.md   # 个人层 ⛔ 不跟踪
```

决策序号在**晋升时刻**才认领；`_INDEX.md` 尾部冲突即报警，后合并者整体 +N。完整规则见 [`workflows/core-documents.md`](./skills/bootstrap-agent-workspace/workflows/core-documents.md) §6。

详细入口：[`skills/bootstrap-agent-workspace/SKILL.md`](./skills/bootstrap-agent-workspace/SKILL.md)

---

## spec-writing：契约怎么写到「拿去就能复刻」

当项目需要文档先行、字段/接口/状态机必须钉死时启用。重点不是堆文档，而是：

- **10 段强制结构** + **零自由发挥**（11 维钉死）
- **落地前 15+2 自检**（含 Properties 两题）
- **Properties（推荐）**：关键行为写成可判定的 ∀；覆盖矩阵可挂 `P-*` / `PT-*`
- **Correctness 变更门**：写性质 ≠ 每次都跑测试；仅 dirty/diff 命中相关实现或性质正文时才跑对应 PT——适合借鉴到业务仓，**不必**做成 Skill 仓全仓强制 PBT

入口：[`skills/spec-writing/SKILL.md`](./skills/spec-writing/SKILL.md)

---

## 真实案例：拼多多拉图工具

[《拼多多拉图工具 vibecoding 全过程复盘》](./docs/case-study-pdd.md)：53 轮对话、25 条决策、层级 Spec、客户交付双击 exe。

- 需求挤牙膏注入，靠 Spec 层级仍有落点  
- 「为何 jimp 不 sharp」可在决策里溯源  
- 多 Agent 并行覆盖文件——正是多人晋升 / 只追加要防的问题  

---

## 安装与发布

复制到宿主 Skills 目录即可，例如：

```text
<skills-root>/bootstrap-agent-workspace/
<skills-root>/task-handoff/
<skills-root>/spec-writing/
```

- 目录名 = `SKILL.md` frontmatter `name`
- 每个 Skill 自包含，不依赖相邻 Skill 或根目录运行时
- 根目录不放 `SKILL.md`

## License

[MIT](./LICENSE)
