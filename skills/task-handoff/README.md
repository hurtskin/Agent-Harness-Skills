# Task Handoff

一个用于复杂 coding 任务上下文交接的 Skill。它通过无状态接任子代理审计当前任务、追问旧任务主 Agent，并使用临时状态文件保存跨轮信息，最终生成可验证的交接文档、接管提示词或二者组合。

与普通对话摘要相比，`task-handoff` 更强调证据、冲突检查、未知项和可恢复状态，适合上下文较长、决策较多或准备新开任务继续工作的场景。

## 核心能力

- 从当前任务中提取目标、验收标准、进度、约束、决策和失败尝试
- 使用新的无状态接任子代理独立审计交接信息
- 最多进行 3 轮审问，每轮最多提出 5 个高价值问题
- 额外执行 1 次独立终审，子代理调用总数最多为 4 次
- 以带 v2 YAML Front Matter 的临时 Markdown 文件作为跨轮次唯一会话记忆
- YAML Front Matter 是机器状态唯一事实源，正式章节保存事实证据，`# TL;DR` 是不超过 1500 Unicode 字符的派生投影
- 每轮在当前证据下合并并穷举最多 5 个问题，由主 Agent 一次性批量回答
- 为关键结论记录文件、提交、diff 或测试证据
- 无法验证的信息统一标记为 `unverified`
- 支持 `READY`、`READY_WITH_RISKS` 和 `BLOCKED` 三种最终状态
- 根据内容长度生成交接文档、完整提示词、压缩提示词或文档加短启动提示词
- 使用安全 YAML 解析、确定性机器校验和候选/正式文件 SHA-256 字节摘要一致性保护写入，并提供异常恢复规则

## 适用场景

满足以下任一情况时可以使用：

- 当前对话上下文较长，准备新开任务继续开发
- 需要把 coding 工作交给另一个 Agent 或工程师
- 当前任务包含较多隐性决策、约束和失败尝试
- 普通摘要可能遗漏关键证据或风险
- 希望由独立子代理检查交接信息是否足够
- 用户要求生成接管提示词或交接文档

以下情况通常不需要使用：

- 任务已完成且没有后续接管需求
- 只需回答简单问题
- 旧任务上下文已经丢失，却要求恢复未记录的历史事实

## 触发方式

可以直接向 Agent 表达任务交接意图，例如：

```text
使用 task-handoff 交接当前任务。
```

```text
当前上下文太长，请生成一份可供新任务接管的交接文档。
```

```text
请让接任子代理检查当前任务信息是否足够，并生成文档加启动提示词。
```

## 工作原理

```text
接任子代理 ↔ Skill 编排器 ↔ 当前旧任务主 Agent
                         ↓
                    临时状态文件
                         ↓
                    最终交接包
```

各角色职责如下：

- **当前旧任务主 Agent**：旧对话上下文的唯一持有者，负责回答无法从仓库直接验证的问题。
- **接任子代理**：读取状态文件和仓库证据，检查缺失事实、冲突、风险与未知项。
- **Skill 编排器**：管理轮次、落盘、状态流转、回答归并和最终交付。
- **临时状态文件**：保存跨子代理调用的唯一会话记忆；后续调用不得依赖上一子代理的隐藏上下文。

## 执行流程

1. **初始化**：收集目标、验收标准、当前状态、用户约束和已有证据。
2. **创建状态文件**：使用严格的 v2 YAML Front Matter 写入机器状态，并在固定 `# TL;DR` 后保存任务事实、决策、风险、失败尝试和推荐下一步。
3. **接任预审**：调用无状态子代理读取状态文件并审计交接内容；每轮一次性穷举并合并当前证据下最多 5 个问题。
4. **批量归并**：`NEEDS_ANSWERS` 使用问题批次与回答归并批次两个稳定事务；满足停止条件的 `READY` / `READY_WITH_RISKS` 将完整预审批次与 `REVIEW_PENDING` 一次提交，禁止先写 `COLLECTING` 再转态。
5. **确定性写入校验**：安全解析 YAML、检查 Markdown 和状态不变量，再以候选/正式文件 SHA-256 字节摘要一致性确认替换成功。
6. **继续审问**：信息仍不足时调用新的无状态子代理，最多进行 3 轮。
7. **独立终审**：审问停止后额外调用一次子代理；终审六字段、接任摘要、TL;DR、终态及理由证据在内存归并后一次封存。
8. **选择交付方式**：根据长度和用户选择输出文档、提示词或组合交付。

## 子代理输出契约

预审和终审统一使用以下字段：

```text
Status
Questions
Conflicts
Risks
Unknowns
Evidence
```

没有内容的字段写 `none`，不得使用同义字段替代。

预审状态只能是：

- `NEEDS_ANSWERS`
- `READY`
- `READY_WITH_RISKS`

终审状态只能是：

- `READY`
- `READY_WITH_RISKS`
- `BLOCKED`

## 状态机

```text
COLLECTING → NEEDS_ANSWERS → COLLECTING
COLLECTING → REVIEW_PENDING
NEEDS_ANSWERS → REVIEW_PENDING
REVIEW_PENDING → READY | READY_WITH_RISKS | BLOCKED
```

| 状态 | 含义 |
|---|---|
| `COLLECTING` | 正在初始化，或上一轮回答已落盘，可以继续审问 |
| `NEEDS_ANSWERS` | 存在必须由当前旧任务主 Agent 回答的问题 |
| `REVIEW_PENDING` | 审问已停止，等待独立终审 |
| `READY` | 接管信息完整，没有影响执行的未知项 |
| `READY_WITH_RISKS` | 可以接管，剩余未知项可在新任务中安全验证 |
| `BLOCKED` | 缺少接管前必须获得的信息，继续执行可能造成错误或不可逆影响 |

只有独立终审可以写入最终状态。预审返回 `READY` 或 `READY_WITH_RISKS` 时，只能先进入 `REVIEW_PENDING`。

## 状态文件 v2

生成的 handoff Markdown 使用 YAML Front Matter 作为机器状态唯一事实源（不同于 `SKILL.md` 自身的注册 Front Matter），字段固定为：

```text
schema_version, session_id, repository, branch, base_commit, working_tree,
handoff_status, interrogation_round, last_audit_status, status_reason,
status_evidence, created_at, updated_at
```

`schema_version` 固定为 `2`。所有字段均为 required，顶层及 `status_evidence` 元素均拒绝未知键：

- `session_id`、`repository`、`status_reason` 必须为非空字符串；`created_at`、`updated_at` 必须为 RFC 3339。
- `branch`、`base_commit` 为 `string|null`；detached、非 Git 或 unborn 时为 `null`，非空 `base_commit` 必须为 7–64 位十六进制字符。
- `working_tree` 只能为 `CLEAN`、`DIRTY`、`UNAVAILABLE`。
- `status_evidence` 是非空结构化数组；元素固定为 `kind/ref/claim/verification`。`kind` 只能为 `source|document|test|diff|commit|command|unverified`，`ref` 为 `string|null`，`claim` 为非空字符串，`verification` 为 `VERIFIED|UNVERIFIED`。完全无证据时只能有一个 `kind=unverified`、`ref=null`、`verification=UNVERIFIED` 的项。
- 初始化、更新、恢复时，`session_id` 分别与编排器持有的预期值、最后可验证正式文件、被选恢复版本比较。

不得增加 `content_hash`、`LOW_RISK` 或 `source_snapshots`。YAML 后第一个标题必须是 `# TL;DR`，且依次包含 `Objective`、`Current State`、`Next Action`、`Blockers and Risks`、`Critical Constraints`、`Evidence Anchors`；建议不超过 200 tokens，硬限制 1500 Unicode 字符。正式章节是事实证据源，TL;DR 仅为派生投影。

TL;DR 不是空标题骨架：`Objective` 至少一个非空目标；`Current State` 必须含与 `handoff_status` 一致的 `Status`，并分别列出已修改与已验证内容；`Next Action` 至少一个可执行动作，只有终态确无动作时可写 `none` 加理由；`Blockers and Risks`、`Critical Constraints` 至少一项或 `none`，但 `READY_WITH_RISKS` 的风险不得为 `none`；`Evidence Anchors` 至少一个可定位锚点或 `unverified`。这些规则全部由机器校验。

## 强制落盘规则

每轮必须遵循“先完整构造、后确定性提交”：

1. 在状态文件同目录写入完整候选临时文件。
2. 使用禁用任意对象构造、自定义标签和外部引用的安全 YAML 解析器，并拒绝重复键、未知键、锚点/别名和多文档输入。
3. 机器检查 UTF-8、严格字段、状态与轮次、RFC 3339 时间、固定 TL;DR、必需章节、本轮批次和状态交叉不变量。
4. 校验成功后安全替换正式文件，并保留最后可验证副本。
5. 比较候选与正式文件的 SHA-256 字节摘要；一致后才允许回答、停止审问、调用下一子代理或流转状态。

正常路径不使用 LLM 全文双回读。仅在机器校验无法解释异常或恢复需要人工判断时，才允许 LLM 按需回读；它不能替代安全解析、机器校验或摘要比对。发生写入失败、部分写入、校验失败、摘要不一致或文件损坏时，不得增加轮次或改变状态，应从通过同一机器校验的正式文件或最后可验证副本恢复；无可验证副本时停止原会话并创建新的 `session_id`。

`NEEDS_ANSWERS` 必须有非空问题批次；只有整批问题均已回答或明确归档为未知、且影响已归档后，才可转为 `COLLECTING` 或 `REVIEW_PENDING`。该路径继续保留问题批次和回答归并批次两个独立稳定事务。

预审 `READY`，或风险已归档且满足停止条件的 `READY_WITH_RISKS`，必须把本轮六字段、正式章节归并、TL;DR、`last_audit_status`、`status_reason`、结构化 `status_evidence`、`updated_at` 与 `handoff_status=REVIEW_PENDING` 放入同一候选并一次正式替换；禁止先以 `COLLECTING` 提交再单独转态。机器校验会拒绝“完整 READY 批次且停止条件满足但状态仍为 COLLECTING”。`REVIEW_PENDING` 不得留有未归档问题或影响。终态必须在终审六字段、`Final Successor Summary`、TL;DR、终态及理由证据一次封存成功后成立。

## 最终交付方式

| 方式 | 适用情况 |
|---|---|
| 文档 + 短启动提示词 | 默认推荐；引用成功封存的正式 handoff 文档，同时减少新任务启动上下文 |
| 仅交接文档 | 交付成功封存的正式 handoff 文件或其字节一致副本 |
| 完整提示词 | 内容较短且不存在截断风险 |
| 压缩提示词 | 输入上限较小或交接内容较长 |

文档模式不得另行生成丢失机器状态的普通 Markdown。最终交接文档必须是成功封存的正式 handoff 文件或 SHA-256 一致的字节级副本，以 v2 YAML Front Matter 和紧随其后的 `# TL;DR` 开始，并完整通过 `SKILL.md` 4.1 的校验。

当交接正文可能超过宿主输入上限时，Skill 必须询问用户，不能直接输出可能被截断的完整提示词。

## 关键约束

- 最多 3 轮审问，每轮基于当前证据一次性穷举、合并最多 5 个问题
- 主 Agent 一次性批量回答；问题批次和回答归并批次各只做一次正式替换，禁止逐题落盘
- 终审额外调用一次，不计入审问轮次
- 每次子代理调用都必须重新读取完整状态文件
- 可以从代码或文档验证的问题不得询问旧任务主 Agent
- 每个关键结论必须有可读取证据或标记为 `unverified`
- 状态文件不得包含密钥、令牌、个人隐私或未经脱敏的敏感日志
- 未经用户确认，不覆盖 `AGENTS.md`、长期记忆或已有交接文档
- 终态写入后不得继续审问；发现新事实时应创建新的交接会话

## 目录结构

```text
task-handoff/
├── README.md
└── SKILL.md
```

- `SKILL.md`：Skill 的触发条件、执行规范、状态机和完整约束
- `README.md`：面向使用者的能力说明和快速使用指南

## 当前验证范围

本文档定义协议约束；安全 YAML 解析器、确定性校验、原子替换、SHA-256 摘要比对及故障恢复能力需由具体宿主环境提供并验证。
