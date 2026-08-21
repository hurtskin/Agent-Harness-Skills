# Agent Harness Skills

面向 Trae 与主流 Agent Harness 的可独立发布 Skills 集合。仓库的精髓是 **`bootstrap-agent-workspace`**：一套让 AI 和人、单人和团队都能在同一项目里稳定协作的工作区结构——AI 有宪法可依，决策有据可查，多人互不踩脚。另外两个 Skill 是它的配套工具。

## 核心：bootstrap-agent-workspace

初始化 AI Agent 工作区。它解决的问题：AI 每次会话都从零开始，项目规范靠人肉口述，做完的决策没人记得，多人同时用 AI 互相覆盖。

### 交互式初始化——先问诊，再开方

它不是"复制一套模板完事"的脚手架，而是一段 AI 主导的问诊流程：先了解你的项目，再按需组装，最后只生成你真正需要的东西。

```text
1. 问诊      AI 并行读取你的仓库结构、项目清单、README、测试配置，
             推断项目类型、目标、协作模式（单人/多人）；
             有证据就推断，没证据就问你，不瞎猜

2. 选套餐    AI 问你一个问题（不甩技术名词）：
             ┌─────────────────────────────────────────────┐
             │ 你希望这次先解决什么？                        │
             │  1. 快速开始（推荐）：建好协作说明、决策目录   │
             │     和待办排期，马上开始推进工作              │
             │  2. 完整工具链（适合大型协作）：再加 Spec ↔   │
             │     代码一致性检查                            │
             │  3. 自定义能力：我自己组合要装什么            │
             └─────────────────────────────────────────────┘

3. 确认      AI 汇报「将生成哪些产物」，你点头才动手；
             已有文件默认增量升级，绝不覆盖你的现有内容

4. 生成+验收 只读取选中模块的流程文档，未选的一概不装；
             完成后按验收清单逐项校验
```

这套"按需组装"也体现在文档架构上：SKILL.md 只管激活和路由，COMMON.md 管公共流程，各模块文档只在被选中时才加载——初始化一个小项目，AI 不会去读 drift-check 的实现细节。

### 初始化后的产物

```text
project/
├── AGENTS.md       # AI 宪法：协作原则、安全红线、踩坑教训、当前入口
│                   # 所有 Agent Harness 原生加载它——换工具零迁移
├── BACKLOG.md      # 待办排期：未完成项进，完成后出
└── decisions/      # 决策档案：每个重要决策一个文件，文件名自带关键词
    ├── _INDEX.md   #   索引表——AI 查"为什么用 jimp 不用 sharp"先扫这里
    └── 006-v1.1-phash-dedup-jimp-sharp-bmp.md
```

三件套之外的任何 Harness 差异都不需要你操心：Trae、Codex、OpenCode、Pi、Qoder 原生加载 `AGENTS.md` 开箱即用，Claude Code 自动生成 `CLAUDE.md` 薄入口。

详细文档：[`skills/bootstrap-agent-workspace/SKILL.md`](./skills/bootstrap-agent-workspace/SKILL.md)

### 单人模式

个人项目选「快速开始」套餐。初始化时 AI 会问诊你的项目（从仓库证据推断，问不到点子上的不多问），生成三件套；之后的日常工作流：

```text
新会话     AI 自动读 AGENTS.md → 拿到原则、红线、教训和当前入口，不用重复交代
做决策     结论验证通过后，AI 新建 decisions/NNN-vN-关键词.md 并登记 _INDEX.md
           （序号 = 当前最大 +1，文件名即搜索索引，ls 一眼看全史）
踩了坑     AI 在 AGENTS.md 踩坑教训章节追加一条「错误做法 → 正确做法」
待办闭环   BACKLOG.md 移除条目，闭环决策落进 decisions/
```

单人模式下你就是确认闸门：AI 起草一切文档变更，你点头才生效。项目长大了想加装 drift-check？重新触发 skill 选「完整工具链」，增量升级，不动已有内容。

### 多人模式（核心设计）

多人同时和各自的 AI 协作开发同一个项目时，最大的痛点是：AI 的工作记忆写在哪里？写进共享文件，每个人 pull 都是冲突地狱；各自为政，一周后团队会有三套互相看不懂的“项目规范”。

本仓库的答案：**共享宪法 Git 锁死，个人上下文 Git 无视，人做晋升闸门。**

#### 三层结构

```text
project/
├── AGENTS.md                 # 宪法层 ⭐ Git 跟踪：协作原则、红线、踩坑教训（全员共享，AI 只起草不生效）
├── BACKLOG.md                # 宪法层 ⭐ Git 跟踪：待办排期
├── decisions/
│   ├── _INDEX.md             # 决策层 ⭐ Git 跟踪：决策索引表
│   └── 006-v1.1-phash-...md  # 决策层 ⭐ Git 跟踪：已确认的团队决策
└── .agents/                  # 个人层 ⛔ Git 不跟踪：每人一个目录，互不干扰
    ├── huang/
    │   ├── context.md        # 个人 AI 的当前任务上下文
    │   └── scratchpad.md     # 草稿、探索期假设、待验证结论
    └── zhang/
        ├── context.md
        └── scratchpad.md
```

| 层级 | 文件 | Git | AI 权限 | 内容 |
|---|---|---|---|---|
| 宪法层 | `AGENTS.md`、`BACKLOG.md` | 跟踪 | 起草-确认制 | 原则、红线、教训、排期 |
| 决策层 | `decisions/` | 跟踪 | 起草-确认制；已确认不改写 | 已验证的团队决策 |
| 个人层 | `.agents/<成员>/` | 忽略 | 自由读写 | 当前任务上下文、探索草稿 |

**起草-确认制**：AI 可以起草宪法层修改和决策文件，但不得单方面生效——经人工 review 合并后才进入 main。人做闸门，不是人做誊写员。

#### 使用流程（三人团队示例）

```text
1. 初始化      运行 bootstrap-agent-workspace，选择多人协同；
               确认成员名单（git user.name），自动建 .agents/<你>/ 骨架并忽略入库

2. 日常工作    AI 先读 AGENTS.md（宪法）→ 再读 .agents/<你>/context.md（当前任务）；
               探索期假设随手写 .agents/<你>/scratchpad.md，不编号，随便改

3. 决策晋升    一个结论验证通过后：
               a. AI 读 main 最新 _INDEX.md 取 max+1，起草正式决策文件（此刻才有序号）
               b. 同一 PR 内：_INDEX.md 追加一行；教训类结论起草 AGENTS.md 修改
               c. 代码 + 决策文件一起提 PR，commit message 引用决策文件名
               d. 队友 review → 合并 = 确认生效

4. 并发撞号    两人同时晋升会拿到同一个序号——没关系：
               _INDEX.md 尾部追加必然产生 Git 冲突，冲突即报警；
               后合并者把自己的序号整体 +N（文件重命名 + 索引行 + 文内 vN），纯机械操作
```

#### 为什么这样分

- **AGENTS.md 必须跟踪**：它是团队共识的锚点。不跟踪，三个人各聊三天 AI，会得到三套不同的“灵魂文档”
- **个人上下文必须忽略**：张的 AI 写“当前任务：BMP 支持”，李的 AI 写“当前任务：分页”，这俩文件一旦入库，每次 pull 都是冲突
- **序号在晋升时刻才分配**：草稿不编号，所以批量晋升时重命名零牵连；`_INDEX.md` 的尾部冲突不是故障，是系统唯一的报警器
- **归属进元数据**：决策文件带「作者」行、索引带作者列；文件名只留给全局顺序

完整规则见 [`workflows/core-documents.md`](./skills/bootstrap-agent-workspace/workflows/core-documents.md) §6。

### 真实案例：拼多多拉图工具

这套体系不是纸上谈兵——[《拼多多拉图工具 vibecoding 全过程复盘》](./docs/case-study-pdd.md)还原了一个真实项目从「拉个开源项目」到「交付单文件 exe」的全程：53 轮对话、25 条决策记录、36 个 Spec 文件、30 条单测，最后客户拿到的是一个双击即用的 exe，全程零命令。

几个最有说服力的瞬间：

- **需求挤牙膏式注入，架构接得住**：用户从没给过完整需求文档，中途还有「忘了，还有一个最重要的功能」——靠层级 Spec 体系，每个新需求都有明确落点
- **决策全程可溯**：「为什么用 jimp 不用 sharp」这种问题，翻决策日志 v1.1 就有答案（sharp 不支持 BMP，实测淘汰）
- **踩坑变资产**：Windows detached 进程无法 COM 交互这种环境深坑，沉淀为 lessons-learned，下次直接绕开
- **多 Agent 冲突实战**：两个 Agent 并行改同一批 Spec 文件发生覆盖——这正是多人协同模式（决策晋升 + 只追加不重写）要解决的问题

详见 [`docs/case-study-pdd.md`](./docs/case-study-pdd.md)。

## 配套 Skill

| Skill | 用途 | 入口 |
|---|---|---|
| `task-handoff` | 长任务交接：接任子代理审计上下文，生成可验证的交接文档或接管提示词 | [`skills/task-handoff/SKILL.md`](./skills/task-handoff/SKILL.md) |
| `spec-writing` | Spec 编写规范：10 段强制结构 + 零自由发挥约束 + 落地前 15 题自检 | [`skills/spec-writing/SKILL.md`](./skills/spec-writing/SKILL.md) |

## 安装

将需要的发布单元复制到宿主工具的 Skills 目录。例如 Trae：

```text
<skills-root>/bootstrap-agent-workspace/SKILL.md
<skills-root>/task-handoff/SKILL.md
<skills-root>/spec-writing/SKILL.md
```

## 发布约定

- 每个 `skills/<name>/` 的目录名必须与 `SKILL.md` frontmatter 中的 `name` 一致。
- 每个 Skill 必须自包含，不能依赖相邻 Skill 或仓库根目录中的运行时文件。
- 发布单个 Skill 时，只打包对应的 `skills/<name>/` 目录。
- 仓库根目录不放 `SKILL.md`，避免被识别为额外 Skill 或产生重复入口。
