# Agent Harness Skills

面向 Trae 与主流 Agent Harness 的可独立发布 Skills 集合。

精髓是 **`bootstrap-agent-workspace`**：问诊式初始化工作区。两条并列的核心能力：

1. **多人协同**——共享宪法 Git 锁死，个人上下文 Git 无视，人做晋升闸门；多人各带 AI 也不把项目规范撕成三份。
2. **路径成对钩子（本轮增量）**——轮次结束轻量盯住契约侧 ↔ 实现侧是否同现，单边改当轮提醒，而不是事后人肉对账。

另外两个 Skill（`spec-writing` / `task-handoff`）是配套。

---

## 核心一：多人协同

多人同时和各自的 AI 协作时，最大痛点是：工作记忆写哪里？写进共享文件 → pull 冲突地狱；各自为政 → 一周后三套互相看不懂的「项目灵魂」。

答案：**共享宪法 Git 跟踪，个人上下文 Git 忽略，人做晋升闸门。**

### 三层结构

```text
project/
├── AGENTS.md                 # 宪法层 ⭐ 跟踪：原则、红线、踩坑教训
├── BACKLOG.md                # 宪法层 ⭐ 跟踪：待办排期
├── decisions/
│   ├── _INDEX.md             # 决策层 ⭐ 跟踪：索引表
│   └── 006-v1.1-….md         # 决策层 ⭐ 跟踪：已确认决策
└── .agents/                  # 个人层 ⛔ 不跟踪：每人一目录
    ├── huang/
    │   ├── context.md        # 当前任务上下文
    │   └── scratchpad.md     # 探索草稿（不编号、随便改）
    └── zhang/
        ├── context.md
        └── scratchpad.md
```

| 层级 | 文件 | Git | AI 权限 |
|---|---|---|---|
| 宪法层 | `AGENTS.md`、`BACKLOG.md` | 跟踪 | 起草-确认制（可起草，人工 review 合并后生效） |
| 决策层 | `decisions/` | 跟踪 | 起草-确认制；已确认决策不改写 |
| 个人层 | `.agents/<成员>/` | 忽略 | 自由读写，成员间互不干扰 |

**起草-确认制**：AI 不是誊写员，也不是擅自改宪法的人——起草共享层变更，人点头合并才进 main。

### 使用流程（示意）

```text
1. 初始化   bootstrap 选多人协同 → 确认成员名单 → 建 .agents/<你>/ 并 gitignore
2. 日常     先读 AGENTS.md，再读 .agents/<你>/context.md；草稿写 scratchpad
3. 决策晋升 结论验证通过后：
            a. 读 main 最新 _INDEX.md 取 max+1，此刻才有序号，起草决策文件
            b. 同 PR：追加索引行；教训类改动起草 AGENTS.md
            c. 代码 + 决策一起提 PR；队友 review → 合并 = 确认生效
4. 并发撞号 两人拿到同一序号也没关系：
            _INDEX.md 尾部追加必然冲突 = 系统报警；
            后合并者整体 +N（文件名 + 索引行 + 文内版本），纯机械操作
```

### 为什么这样分

- **AGENTS.md 必须跟踪**：团队共识锚点；不跟踪会裂成多套灵魂文档  
- **个人上下文必须忽略**：各人「当前任务」一旦入库，每次 pull 都是冲突  
- **序号在晋升时刻才分配**：草稿不编号，批量晋升零牵连；索引尾部冲突是报警器不是故障  
- **归属进元数据**：作者行 / 作者列；文件名只留给全局顺序  

完整规则：[`workflows/core-documents.md`](./skills/bootstrap-agent-workspace/workflows/core-documents.md) §6。

---

## 核心二（本轮）：路径成对钩子

Agent 最常出的漂移往往不是字段对错，而是**单边改**：动了实现没动契约（或反过来）。路径成对是 **L0**：只看本轮 git dirty 两侧路径是否同现——不做函数级扫描，也不做行为证明。

| | 说明 |
|---|---|
| **何时跑** | 宿主「轮次 / 会话结束」类 hook（执行 Agent 按当前 Harness 注册） |
| **装什么** | `tools/path_align_hooks/`（`drift_lite` + `turn_align`，ps1/sh） |
| **产出** | JSON；有风险可 nudge（A1 补另一侧 / A2 说明故意单边） |
| **套餐** | 「完整工具链」默认带；快速开始不带；自定义可单选 |
| **Harness** | 模板无某工具专属 hooks 配置；Skill 不写分工具适配长文 |
| **关掉催改** | `PATH_ALIGN_NUDGE=0` |

```powershell
powershell -NoProfile -File tools/path_align_hooks/drift_lite.ps1
```

[`modules/path-align-hooks.md`](./skills/bootstrap-agent-workspace/modules/path-align-hooks.md) · [`templates/path_align_hooks/`](./skills/bootstrap-agent-workspace/templates/path_align_hooks/)

> `drift-check`（D1–D6）偏 Python、需 Adapter，**不在默认套餐**；与路径成对分层，互不替代。

---

## 初始化：先问诊，再开方

```text
1. 问诊   读仓库证据，推断项目与协作模式（单人 / 多人）
2. 选套餐
          1. 快速开始：协作说明 + 决策目录 + 待办排期
          2. 完整工具链：再加路径成对钩子
          3. 自定义：自选模块（含可选 drift-check）
3. 确认   汇报产物，点头才生成；已有文件默认增量升级
4. 生成   只装选中模块
```

单人模式：不建 `.agents/`；你仍是确认闸门。多人模式：见上文「核心一」。

原生加载 `AGENTS.md` 的 Harness 开箱即用；Claude Code 额外 `CLAUDE.md` 薄入口。  
入口：[`skills/bootstrap-agent-workspace/SKILL.md`](./skills/bootstrap-agent-workspace/SKILL.md)

---

## 配套 Skill

| Skill | 用途 | 入口 |
|---|---|---|
| `spec-writing` | Spec 10 段 + 零自由发挥 + 落地前自检（可选 Properties 写法；本仓不强制 PBT） | [`SKILL.md`](./skills/spec-writing/SKILL.md) |
| `task-handoff` | 长任务可验证交接 | [`SKILL.md`](./skills/task-handoff/SKILL.md) |

---

## 真实案例

[《拼多多拉图工具 vibecoding 全过程复盘》](./docs/case-study-pdd.md)：决策可溯、Spec 层级接需求、多 Agent 并行覆盖文件——正是多人协同（晋升 / 只追加）与契约纪律要防的问题。

---

## 安装与发布

```text
<skills-root>/bootstrap-agent-workspace/
<skills-root>/task-handoff/
<skills-root>/spec-writing/
```

目录名 = frontmatter `name`；Skill 自包含；根目录不放 `SKILL.md`。

## License

[MIT](./LICENSE)
