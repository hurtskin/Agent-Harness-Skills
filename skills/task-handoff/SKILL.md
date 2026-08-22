---
name: "task-handoff"
description: "通过接任子代理审问当前 Agent，提炼可验证的任务交接包。Invoke when 上下文过长、准备新开任务、需要交接当前 coding 工作或用户要求生成接管提示词/文档。"
---

# Task Handoff — 任务上下文交接

## 1. 目标

在当前任务上下文仍可用时，让“接任子代理”审阅代码和临时状态、向当前主 Agent 提问，并将隐性决策转化为可验证的交接信息。最终按用户选择输出提示词、交接文档，或“文档 + 短启动提示词”。

本 Skill 模拟以下协作关系：

```text
接任子代理 ↔ Skill 编排器 ↔ 当前旧任务主 Agent
                         ↓
                    临时状态文件
                         ↓
                    最终交接包
```

子代理每次调用均视为无状态实例。临时状态文件是跨轮次唯一会话记忆；不得假设后续调用记得上一轮内容。

## 2. 触发条件

满足任一条件时调用：

- 当前任务上下文过长，用户准备新开任务继续工作。
- 用户要求任务交接、上下文移交、接管提示词或交接文档。
- 当前 Agent 已做出较多决策，普通摘要可能遗漏关键约束。
- 用户希望由子代理检查交接信息是否足够。

以下情况不调用：

- 任务已经完成且没有后续接管需求。
- 只需回答一个简单问题。
- 旧任务上下文已经丢失，且用户要求恢复未记录的历史事实；此时只能基于现存代码和文档重建，不得声称已恢复原上下文。

## 3. 强制边界

1. 当前主 Agent 是旧任务上下文的唯一持有者；不得让一个新子代理冒充旧 Agent。
2. 接任子代理必须读取临时状态文件，并按需检查代码、Git diff、测试结果和已有文档。
3. 任何关键结论必须附证据位置，或明确标记为 `unverified`。
4. 最多进行 3 轮审问，每轮最多提出 5 个高价值问题。
5. 已能从代码或仓库证据回答的问题，不得询问当前主 Agent。
6. 不记录冗长思考过程，只记录事实、决策、理由、风险、问题和回答。
7. 临时文件不得写入密钥、令牌、个人隐私或未经脱敏的敏感日志。
8. 未经用户确认，不得覆盖项目长期记忆、AGENTS.md 或既有交接文档。
9. 子代理只负责审计和提问；Skill 编排器负责更新临时状态文件及最终输出。

## 4. 临时状态文件

开始前确定临时文件路径：

- 优先使用项目已有临时目录。
- 若没有，询问用户或使用用户明确允许的临时目录。
- 不得默认把临时交接文件放在项目根目录。
- 文件名建议为 `handoff-<session-id>.md`。

临时文件采用 YAML Front Matter + Markdown 正文。这里的 Front Matter 属于**生成的 handoff 状态文件**，不得与本 `SKILL.md` 顶部用于 Skill 注册的 Front Matter 混淆。YAML Front Matter 是机器状态唯一事实源；正式章节是事实与证据源；`# TL;DR` 是由二者派生的阅读投影，不得反向覆盖机器状态或正式章节。

YAML 必须严格使用以下 Schema，不得增加 `content_hash` 自引用字段、`LOW_RISK` 或 `source_snapshots`：

```yaml
---
schema_version: 2
session_id: "<非空唯一会话 ID>"
repository: "<非空仓库绝对路径或可验证标识>"
branch: null
base_commit: null
working_tree: UNAVAILABLE
handoff_status: COLLECTING
interrogation_round: 0
last_audit_status: null
status_reason: "<非空当前状态理由>"
status_evidence:
  - kind: unverified
    ref: null
    claim: "<非空、尚无可验证证据的状态说明>"
    verification: UNVERIFIED
created_at: "<RFC 3339 时间>"
updated_at: "<RFC 3339 时间>"
---
```

所有上述字段均为 `required`，字段集合必须完全相等并拒绝任何未知键；`status_evidence` 元素也只允许固定的 `kind`、`ref`、`claim`、`verification` 四个必需键并拒绝未知键。`schema_version`、`interrogation_round` 为整数；`session_id`、`repository`、`status_reason` 为非空字符串；`branch`、`base_commit` 为 `string|null`，detached、非 Git 或 unborn 仓库均写 `null`，且非空 `base_commit` 必须匹配 7–64 位十六进制字符；`working_tree` 只能为 `CLEAN`、`DIRTY` 或 `UNAVAILABLE`。`handoff_status` 只能取第 5 节六种状态；`last_audit_status` 为 `string|null`，非空时在预审只能为 `READY`、`READY_WITH_RISKS`、`NEEDS_ANSWERS`，终审封存时只能为 `READY`、`READY_WITH_RISKS`、`BLOCKED`。`created_at`、`updated_at` 必须是有效 RFC 3339 字符串。

`status_evidence` 必须是非空结构化数组。每个元素中，`kind` 只能为 `source`、`document`、`test`、`diff`、`commit`、`command` 或 `unverified`；`ref` 为 `string|null`；`claim` 为非空字符串；`verification` 只能为 `VERIFIED` 或 `UNVERIFIED`。有证据时逐项记录可定位引用及结论；完全无证据时只允许一个元素，且必须同时满足 `kind: unverified`、`ref: null`、`verification: UNVERIFIED`，其 `claim` 说明未验证状态。

YAML 结束后第一个标题必须是 `# TL;DR`，固定模板如下：

```markdown
# TL;DR

## Objective
- <非空目标；至少一项>

## Current State
- Status: <COLLECTING|NEEDS_ANSWERS|REVIEW_PENDING|READY|READY_WITH_RISKS|BLOCKED；必须与 handoff_status 一致>
- Modified: <已修改内容，或 none + 理由>
- Verified: <已验证内容及证据锚点，或 unverified>

## Next Action
- <可直接执行的动作；至少一项。终态确无后续动作时写 none: <理由>>

## Blockers and Risks
- <阻塞或风险；至少一项；确无内容写 none。READY_WITH_RISKS 不得写 none>

## Critical Constraints
- <关键约束；至少一项；确无内容写 none>

## Evidence Anchors
- <可定位的文件:行号、提交、diff、测试或命令记录；至少一项；无证据写 unverified>

# Handoff Details

## Objective
## Acceptance Criteria
## Completed Work
## Pending Work

## Decisions
| Decision | Reason | Evidence | Confidence |
|---|---|---|---|

## Constraints and User Preferences
## Changed Files
## Failed Attempts
## Known Risks
## Unverified Assumptions

## Interrogation
### Round 1
#### Status
#### Questions
#### Conflicts
#### Risks
#### Unknowns
#### Evidence
#### Current Agent Answers

## Evidence
## Recommended Next Actions
## Final Successor Summary
```

`# TL;DR` 的六个二级标题及顺序固定，建议不超过 200 tokens，硬限制为 1500 个 Unicode 字符（从 `# TL;DR` 起至下一个一级标题或文档结束）。上述占位规则均为强制内容约束：`Objective` 至少一个非空目标；`Current State` 必须包含且只使用一个 `Status:` 行并与 YAML `handoff_status` 一致，同时分别说明已修改与已验证内容；`Next Action` 至少一个可执行动作，仅当终态确无动作时允许 `none: <非空理由>`；`Blockers and Risks` 至少一项或精确写 `none`，且 `READY_WITH_RISKS` 时不得为 `none`；`Critical Constraints` 至少一项或精确写 `none`；`Evidence Anchors` 至少一个可定位锚点，完全无证据时精确写 `unverified`。TL;DR 必须与 YAML 状态及正式章节一致，以上结构、基数、终态例外及交叉一致性全部纳入 4.1 的确定性机器校验。只追加新的审问轮次；其他正式章节持续归并和去重，不得将同一事实重复复制到多个章节。

### 4.1 持久化与恢复

正常写入不依赖 LLM 全文双回读，必须执行确定性事务：

> 参考实现：`scripts/validate_handoff.{py,ps1,sh}` 提供下述步骤 2、3、5 的「安全 YAML 解析 + 确定性机器校验 + SHA-256 字节摘要」原语，三语言等价、同失败语义；步骤 1、4 的候选写入与原子替换属宿主事务编排，不在脚本职责内。

1. 在状态文件同目录写入完整候选文件，不直接覆盖最后可验证版本；关闭并刷新写入。
2. 用安全 YAML 解析器和确定性 Markdown 校验器验证候选文件。YAML 解析必须禁用任意对象构造、自定义标签和外部引用，拒绝重复键、未知键、锚点/别名及多文档输入；不得用不安全加载模式。
3. 机器校验的最小不变量：UTF-8 可解码；Front Matter 可安全解析；顶层字段与 `status_evidence` 元素字段均为 required、集合严格相等且无未知键；类型、非空约束、枚举、`base_commit` 格式与 RFC 3339 时间符合上述 Schema；`schema_version` 为整数 `2`；`interrogation_round` 为 `0..3` 的整数且不倒退；初始化候选的 `session_id` 必须等于编排器持有的预期值，更新候选必须等于最后可验证正式文件的值，恢复候选必须等于被选恢复版本的值；`created_at` 不变且 `updated_at` 不早于它；YAML 后第一个标题为 `# TL;DR`；TL;DR 六节的标题、顺序、非空内容、基数、`Status` 一致性、已修改/已验证区分、`none` 例外、证据锚点和 1500 Unicode 字符限制全部满足；必需正式章节与本次应写的六字段审计批次、回答批次或终审内容齐全；并满足第 5 节状态交叉不变量。
4. 候选校验成功后计算其 SHA-256 **字节摘要**，以原子替换或宿主等价安全操作更新正式文件；替换前保留最后可验证副本，例如 `<handoff>.bak`。
5. 对正式文件直接计算 SHA-256 字节摘要并与候选摘要比较。摘要一致才算写入成功，才允许回答、停止判断、调用下一子代理或状态流转；正常路径无需 LLM 再次阅读全文。

失败恢复规则：

- **写入、机器校验、替换或摘要比对失败**：保留正式文件和最后可验证副本；不得增加轮次、回答问题、改变状态或调用下一子代理。候选文件仅供诊断，不得作为事实源。
- **部分写入或替换中断**：不得基于残缺内容继续。依次对正式文件与 `.bak` 执行同一套安全 YAML 解析和确定性机器校验，优先采用通过校验且 `session_id` 相同的正式文件，否则从副本恢复并再次校验与核对 SHA-256。
- **状态文件损坏**：在通过完整机器校验的同会话版本中选择 `updated_at` 最新者；时间相同或无法确定新旧时，使用轮次较低的最后可验证版本，不猜测合并。
- **异常诊断和恢复**：只有机器校验无法说明失败原因或需要人工判断可恢复证据时，才允许 LLM 按需回读相关片段或全文；LLM 回读不能替代安全 YAML 解析、机器不变量校验或摘要比对。
- **无可验证副本**：停止原会话，不得在损坏文件上重建并继续；向用户报告可恢复证据，创建新 `session_id` 后重新初始化，原会话保持损坏且不得伪造终态。
- 恢复动作本身不消耗审问轮次；恢复完成后仍受最多 3 轮审问和额外 1 次终审约束。

## 5. 状态机

`handoff_status` 只允许使用以下状态：

| 状态 | 类型 | 含义 |
|---|---|---|
| `COLLECTING` | 中间态 | 正在初始化交接包，或上一轮回答已经落盘、可以开始下一轮审问 |
| `NEEDS_ANSWERS` | 中间态 | 接任子代理提出了必须由当前主 Agent 回答的问题 |
| `REVIEW_PENDING` | 中间态 | 审问已经停止，所有本轮结果均已落盘，等待终审 |
| `READY` | 终态 | 接管所需信息完整，没有影响下一步执行的未知项 |
| `READY_WITH_RISKS` | 终态 | 可以立即接管；剩余未知项可由新任务自行验证，且验证失败不会导致不可逆操作 |
| `BLOCKED` | 终态 | 缺少接管前必须获得的信息；新任务无法从代码、文档或运行证据自行恢复，继续执行可能造成错误或不可逆影响 |

合法状态转移：

```text
COLLECTING → NEEDS_ANSWERS → COLLECTING
COLLECTING → REVIEW_PENDING
NEEDS_ANSWERS → REVIEW_PENDING    # 三轮耗尽，或剩余问题只能留给新任务验证
REVIEW_PENDING → READY | READY_WITH_RISKS | BLOCKED
```

状态规则：

1. 初始化临时状态文件时写入 `handoff_status: COLLECTING`，`interrogation_round: 0`。
2. 每次收到子代理结果后，必须在内存中完整构造本轮批次，再按对应事务边界正式落盘；不得先提交部分内容后再判断状态。
3. `NEEDS_ANSWERS` 时，当前轮必须存在非空 `Questions`，且未答问题只能记录在该轮问题批次中；`last_audit_status` 必须为 `NEEDS_ANSWERS`，`status_reason` 与 `status_evidence` 必须解释问题及影响。问题批次与后续回答归并批次继续作为两个独立稳定事务。
4. 当前主 Agent 对本轮全部问题一次性批量回答并归并新事实；仅当所有问题均已有回答（允许明确回答“未知”）、未答项及其影响已归档，才可离开 `NEEDS_ANSWERS`。继续审问时转为 `COLLECTING`；停止审问时可直接转为 `REVIEW_PENDING`。
5. `REVIEW_PENDING` 时不得有未归档的未答项或影响，当前轮六字段、回答批次（若有）、风险和未知项均已正式落盘；此时不得再写预审终态。
6. 子代理返回 `READY` 或 `READY_WITH_RISKS` 仅代表预审结论，不直接写入终态。若该预审已满足停止条件，本轮六字段、正式章节归并、TL;DR、`last_audit_status`、`status_reason`、`status_evidence`、`updated_at` 与 `handoff_status: REVIEW_PENDING` 必须在同一个候选版本中一次正式替换；禁止先以 `COLLECTING` 提交完整批次再单独转态。
7. 达到三轮上限或剩余问题只能由新任务验证时，必须先将未答项及影响归档到风险或未知项，再转为 `REVIEW_PENDING`。
8. 机器交叉不变量必须拒绝：当前轮已经形成完整 `READY` 或 `READY_WITH_RISKS` 预审批次、对应停止条件已经满足，但 `handoff_status` 仍为 `COLLECTING` 的候选版本。
9. 只有终审可以写入 `READY`、`READY_WITH_RISKS` 或 `BLOCKED`。终态要求 `REVIEW_PENDING` 已成立、终审六字段的 `Questions` 为 `none`、`Final Successor Summary` 与 TL;DR 已完成，且 `handoff_status`、`last_audit_status`、`status_reason`、`status_evidence` 和正式章节互相一致。
10. 每次状态变化必须同时更新 `status_reason`、`status_evidence` 与 `updated_at`；存在证据时使用结构化证据项，无证据时使用唯一的 `unverified` 项。
11. 终审结论与最后一次预审结论不一致时，必须记录导致变化的新证据、遗漏冲突或违反的终态判据；没有这些依据时不得改变预审结论对应的终态等级。
12. 终态写入后不得继续审问；如发现新事实需要重启，必须创建新的交接会话，不得在原会话中把终态重置为中间态。

审问轮次最多为 3 次；终审不计入审问轮次，因此接任子代理调用总数最多为 4 次。

## 6. 执行流程

### 阶段 A：初始化交接状态

1. 收集当前任务的目标、验收标准、当前状态、用户偏好和明确约束。
2. 读取与当前任务直接相关的代码、文档、Git 状态和验证结果；不要进行无关的全仓库扫描。
3. 将以下内容写入临时状态文件：
   - 已完成与未完成事项。
   - 关键决策、理由和证据。
   - 修改过的文件及关键位置。
   - 失败尝试，以及为何不应重复。
   - 已知风险和未经验证的假设。
   - 推荐的下一步动作。
4. 不确定的信息标记为 `unverified`，不得补写猜测。

### 阶段 B：接任子代理审问

串行调用接任子代理。每次调用必须在任务描述中明确要求：

1. 读取指定临时状态文件。
2. 以即将接管任务的工程师身份审查交接包。
3. 自行读取与交接内容直接相关的仓库证据。
4. 找出会阻碍下一步工作的缺口、冲突和模糊决策。
5. 基于当前可见证据一次性穷举全部必须提问的问题，合并同类项，最多 5 个，并按影响从高到低排列；不得把已知问题拆到后续轮次。
6. 不询问可由代码或文档直接回答的问题。
7. 严格按以下固定契约返回，不增加同义字段；没有内容的字段写 `none`：
   - `Status`：只能是 `READY`、`READY_WITH_RISKS` 或 `NEEDS_ANSWERS`。
   - `Questions`：最多 5 个必须由当前主 Agent 回答的问题。
   - `Conflicts`：交接内容内部或与仓库证据之间的冲突。
   - `Risks`：不确定性可能造成的影响。
   - `Unknowns`：尚未验证的事实及建议验证方式。
   - `Evidence`：可读取的文件绝对路径与行号、提交、diff 或测试记录；不可读取或不存在的证据写 `unverified`。
8. 不修改代码或文件。

推荐的子代理任务模板：

```text
读取交接状态文件：<absolute-path>。
你是即将接管当前 coding 任务的接任者。请结合仓库中的相关代码、文档、Git 状态和测试证据审计交接内容。

要求：
- 找出会影响继续执行的缺失事实、矛盾、模糊决策和未验证假设；
- 能从仓库证据回答的问题自行验证，不要提问；
- 基于当前可见证据一次性穷举全部必须提问的问题，合并同类项，最多 5 个，按影响排序；不得预留已知问题到后续轮次；
- 每个发现附可读取的文件绝对路径与行号、提交、diff 或测试记录；证据不可读取或不存在时标记 unverified；
- 严格按以下六个标题返回；没有内容写 none，不增加同义字段：
  Status
  Questions
  Conflicts
  Risks
  Unknowns
  Evidence
- Status 只能是 READY、READY_WITH_RISKS 或 NEEDS_ANSWERS；
- 不修改任何文件或代码。
```

### 阶段 C：强制落盘、回答与停止判断

每轮子代理返回后，Skill 编排器必须严格按以下顺序执行，不得跳步、逐题落盘或先提交不符合最终事务边界的状态：

1. 在内存中将 `interrogation_round` 加一，构造本轮独立小节。
2. 原样收集子代理返回的预审状态、问题、冲突、风险、未知项和证据，并将本轮发现归并到 `Known Risks`、`Unverified Assumptions`、`Evidence` 等正式章节；重复内容合并，不覆盖更强证据。
3. 更新 TL;DR 投影及 YAML 中的 `last_audit_status`、`status_reason`、结构化 `status_evidence`、`updated_at`。
4. 若预审为 `READY`，或为 `READY_WITH_RISKS` 且风险及影响已归档，则停止条件已经满足：本轮完整六字段、正式章节归并、TL;DR、上述 YAML 字段和 `handoff_status: REVIEW_PENDING` 必须作为同一候选一次正式替换；不得先提交 `COLLECTING` 版本，也不得另做转态提交。
5. 若预审为 `NEEDS_ANSWERS`，将本轮完整六字段、正式章节归并、TL;DR 和 YAML 作为**一次问题批次正式替换**提交，并将 `handoff_status` 设为 `NEEDS_ANSWERS`；禁止按问题逐条写入。当前主 Agent 随后一次性批量回答本轮全部问题，只使用现有对话事实和已验证证据；无法确定时回答“未知”并说明验证方式，不得编造。
6. 在内存中将整批回答及其新事实归并到目标、决策、约束、风险、未知项或下一步，更新 TL;DR 与 YAML；将这些内容作为**一次回答归并批次正式替换**提交，禁止逐题落盘。
7. 仅当所有未答项及其影响已经归档后，回答归并批次才可将 `handoff_status` 设为 `COLLECTING`，或在三轮上限、仅剩执行期可验证问题等停止条件成立时直接设为 `REVIEW_PENDING`。
8. 每个候选均必须满足第 5 节交叉不变量；机器校验必须拒绝停止条件已满足、完整 `READY`/`READY_WITH_RISKS` 批次已存在但状态仍为 `COLLECTING` 的候选。只有正式替换成功后才能调用终审或下一轮。

落盘成功后，满足任一条件时停止审问：

- 子代理预审返回 `READY`。
- 子代理预审返回 `READY_WITH_RISKS`，且所有风险及其影响已经落盘。
- 已完成 3 轮；未答问题及其影响必须已经落盘。
- 剩余问题只能由新任务执行过程中验证；必须先将其归类为非阻塞风险或阻塞候选，并记录理由。

如果不满足停止条件，再次调用新的无状态接任子代理，并要求其重新读取完整临时状态文件。

### 阶段 D：封存交接包

最后调用一次接任子代理进行终审，要求它：

- 检查正式章节是否自洽并有足够证据。
- 把残余冲突、风险和未知项列出。
- 严格按 `Status / Questions / Conflicts / Risks / Unknowns / Evidence` 六个标题返回；终审的 `Status` 只能是 `READY`、`READY_WITH_RISKS` 或 `BLOCKED`，`Questions` 必须为 `none`。
- 在 `Evidence` 中包含最终状态理由及证据；若与 `last_audit_status` 对应的预期终态不同，必须指出新证据、遗漏冲突或被违反的终态判据。
- 另生成不超过 10 条的 `Final Successor Summary`；该摘要是交付内容，不改变六字段审计契约。

Skill 编排器随后执行一个封存事务：

1. 在内存中归并终审原始六字段、`Final Successor Summary`、正式章节、最终 TL;DR、终态及其 `status_reason` / `status_evidence`；合并重复内容，保留最新且有证据的结论。
2. 终审六字段、`Final Successor Summary`、TL;DR、`handoff_status` 终态、`last_audit_status`、`status_reason`、`status_evidence` 与 `updated_at` 必须作为**同一个候选版本、一次正式替换**提交，不得先提交内容再第二次提交终态。
3. 该候选必须通过 4.1 的安全 YAML 解析、确定性机器校验、状态交叉不变量校验和候选/正式文件 SHA-256 字节摘要一致性检查；成功后才视为封存完成。
4. 问答记录可留在临时文件中，但最终交付内容默认不复制完整问答过程。
5. `BLOCKED` 不表示禁止交付；必须明确列出新任务接管前需要补证的事项。

## 7. 最终交付方式

先估算最终交接正文的字符数和 Token 数。Token 无法精确计算时，可用保守估算并明确标注为估算值。

默认安全阈值：

| 估算长度 | 行为 |
|---|---|
| `≤ 6,000 tokens` | 询问用户选择提示词、文档或“文档 + 启动提示词” |
| `6,001–12,000 tokens` | 提醒可能占用过多新上下文，推荐“文档 + 启动提示词” |
| `> 12,000 tokens` | 不默认输出完整提示词；询问用户选择文档、文档 + 启动提示词或压缩提示词 |

如果宿主平台存在更小的已知输入上限，以宿主上限为准。检测到交接内容可能被截断时，必须询问用户，不得直接输出可能残缺的完整提示词。

使用结构化问题提供以下选项：

1. **文档 + 启动提示词（推荐）**：完整交接包保存为文档，同时生成短提示词指引新任务读取和验证。
2. **仅交接文档**：适合用户自行管理接管入口。
3. **完整提示词**：仅在安全阈值内默认提供。
4. **压缩提示词**：只保留高优先级事实；若存在完整文档，必须引用其路径。

若用户已明确指定交付方式且长度安全，不重复询问。

## 8. 输出格式

### 文档模式

最终交接文档必须直接使用**成功封存的正式 handoff 文件**，或使用与该正式文件 SHA-256 一致的字节级副本；不得另行生成丢失机器状态的普通 Markdown 摘要。文档必须以 v2 YAML Front Matter 开始，紧接 `# TL;DR`，并完整通过 4.1 的安全解析、Schema、Markdown、状态交叉不变量和摘要校验。

成功封存的文档正文至少包含：

- 目标和验收标准。
- 当前状态、已完成项与未完成项。
- 用户约束和偏好。
- 关键决策、理由和证据。
- 修改文件与关键位置。
- 失败尝试。
- 风险、未知项和未验证假设。
- 推荐下一步。
- 终审状态与接任摘要。

文档路径必须由用户确认或位于已获许可的专用目录中，不得默认写到项目根目录。

### 启动提示词模式

短启动提示词使用以下骨架：

```text
请接管当前任务。首先阅读交接文档：
<absolute-path-to-handoff>

然后检查文档列出的代码、Git 状态和验证结果，不要假设交接内容完全正确。
完成验证后：
1. 用不超过 10 条要点复述目标、当前状态和约束；
2. 指出冲突、缺失信息和未验证假设；
3. 从 Recommended Next Actions 开始继续执行；
4. 遇到交接文档与仓库事实冲突时，以可验证的当前仓库事实为准，并向用户报告。
```

### 压缩提示词优先级

按以下顺序保留，禁止从尾部机械截断：

1. 目标与验收标准。
2. 当前状态。
3. 用户明确约束与偏好。
4. 关键决策。
5. 未完成项和下一步。
6. 风险、冲突与未验证假设。
7. 关键文件和证据位置。
8. 失败尝试。
9. 详细问答过程。

## 9. 完成检查

交付前确认：

- [ ] 接任子代理至少完成一次独立审计。
- [ ] 每次子代理调用都重新读取了临时状态文件。
- [ ] 所有关键决策均有证据或 `unverified` 标记。
- [ ] 用户偏好、禁止事项和验收标准已记录。
- [ ] 失败尝试不会被新任务无意重复。
- [ ] 未完成项具有明确下一步或验证方式。
- [ ] 每轮与终审均使用 `Status / Questions / Conflicts / Risks / Unknowns / Evidence` 固定契约。
- [ ] 每轮审计输出均按确定性事务校验并完成 SHA-256 摘要一致性检查后，才回答、停止判断或流转状态。
- [ ] 问题批次和回答归并批次各自仅做一次正式替换，没有逐题落盘。
- [ ] 写入失败、部分写入、机器校验失败、摘要不一致或文件损坏时未推进轮次和状态，并已按 4.1 恢复或停止会话。
- [ ] YAML Front Matter 顶层与证据项字段均全部 required、拒绝未知键，类型、非空约束、枚举、`base_commit` 和 RFC 3339 均符合 v2 Schema。
- [ ] 初始化、更新、恢复时的 `session_id` 已分别与编排器预期值、最后可验证正式文件、被选恢复版本比较。
- [ ] TL;DR 六节模板、内容基数、Status 一致性、已修改/已验证区分、`none` 例外、证据锚点与 1500 Unicode 字符硬限制均通过机器校验。
- [ ] `READY` / `READY_WITH_RISKS` 的完整预审批次和 `REVIEW_PENDING` 在同一候选一次提交；`NEEDS_ANSWERS` 仍使用问题批次与回答归并批次两个稳定事务。
- [ ] 所有状态变化符合合法转移及交叉不变量，并记录了 `status_reason` 与结构化 `status_evidence`。
- [ ] 审问不超过 3 轮，终审作为额外一次调用且不计入审问轮次。
- [ ] 最终状态为 `READY`、`READY_WITH_RISKS` 或 `BLOCKED`，且符合状态机判据。
- [ ] 已估算交付长度，并在可能截断时询问用户。
- [ ] 最终交付方式已经用户确认，或用户此前已明确指定。
- [ ] 最终产物不包含敏感信息和无关思考过程。
