# 更新日志

## 2026-08-05 — task-handoff v2 协议更新

### 协议升级

- 将交接状态文件升级为 **YAML Front Matter + Markdown 正文**，并固定 `schema_version: 2`。
- 将 YAML Front Matter 定义为机器状态唯一事实源，正式章节作为事实与证据源，`# TL;DR` 作为派生阅读摘要。
- 明确 Front Matter 必填字段、字段类型、枚举、可空规则及未知键拒绝规则。
- 将 `status_evidence` 改为结构化证据数组，固定 `kind`、`ref`、`claim`、`verification` 字段。

### TL;DR 模板

- 强制 YAML Front Matter 后第一个标题为 `# TL;DR`。
- 固定包含以下六个章节：
  - `Objective`
  - `Current State`
  - `Next Action`
  - `Blockers and Risks`
  - `Critical Constraints`
  - `Evidence Anchors`
- 建议摘要不超过 200 tokens，硬限制为 1500 个 Unicode 字符。
- 为每个章节增加最低内容、`none`、`unverified` 和状态一致性约束，禁止空标题模板通过校验。

### 审问与状态机

- 要求接任子代理在每轮基于当前证据一次性穷举并合并最多 5 个高价值问题，禁止挤牙膏式提问。
- 要求主 Agent 一次性批量回答，禁止逐题落盘。
- 保留 `NEEDS_ANSWERS` 稳定态：问题批次和回答归并批次分别作为一个稳定事务提交。
- 预审返回 `READY`，或风险已归档的 `READY_WITH_RISKS` 时，将完整预审批次与 `REVIEW_PENDING` 在同一候选版本中原子提交。
- 终审六字段、`Final Successor Summary`、TL;DR、终态、状态理由和证据改为一次封存，消除两阶段提交的不一致窗口。

### 持久化与校验

- 用安全 YAML 解析、确定性 Markdown 校验和状态交叉不变量检查替代正常路径的 LLM 全文双回读。
- 使用候选文件与正式文件的 SHA-256 字节摘要一致性确认覆盖成功。
- 正常路径不再要求 LLM 再次阅读全文；仅在机器校验无法解释异常或恢复需要人工判断时按需回读。
- 明确初始化、更新和恢复场景下 `session_id` 的比较对象。
- 保留最后可验证副本及文件损坏、部分写入、摘要不一致时的恢复规则。

### 最终交付

- 最终交接文档必须使用成功封存的正式 handoff 文件或 SHA-256 一致的字节级副本。
- 禁止另行生成缺失 v2 Front Matter 或 TL;DR 的普通 Markdown 作为正式交接文档。

### 文档更新

- 更新 `skills/task-handoff/SKILL.md`，落地完整 v2 协议。
- 更新 `skills/task-handoff/README.md`，同步说明 v2 Schema、TL;DR、批量问答、确定性校验和原子封存规则。
- 更新仓库根 `README.md` 的目录结构，将 `skills/task-handoff/README.md` 列入发布单元。
- 移除无法由当前仓库测试文件佐证的“已有测试验证”声明，改为说明相关能力需由具体宿主环境验证。

### 全局安装同步

- 将工作区发布单元同步到 `c:\Users\haichaowind\.trae-cn\skills\task-handoff`。
- 逐文件覆盖全局 `SKILL.md` 与 `README.md`。
- 通过 SHA-256 校验确认工作区与全局安装副本完全一致。
- 重新加载全局 `task-handoff` Skill，确认已使用 v2 协议。

### 本次未包含

- 未引入 `LOW_RISK` 轻量模式。
- 未引入 `source_snapshots` 静态事实源快照。
- 未增加 `content_hash` 自引用字段。
- 未新增可执行校验器或自动化故障恢复测试；这些可作为后续增强项。
