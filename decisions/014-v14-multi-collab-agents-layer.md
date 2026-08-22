# v14 · 多人协同模式：共享宪法 + .agents/ 个人层 + 决策晋升流程（2026-08-21）

- **状态**：活跃
- **关键词**：多人协同,协作模式,.agents,个人层,共享宪法,晋升流程,序号认领,撞号,起草确认制,gitignore
- **相关模块**：bootstrap-agent-workspace

- **关联文档**：`skills/bootstrap-agent-workspace/`（workflows/core-documents.md §1/§2/§4/§5/§6、COMMON.md、workflows/verification.md、SKILL.md、README.md）
- **变化程度**：bootstrap-agent-workspace 新增多人协同能力——三层结构（宪法层 AGENTS.md/BACKLOG.md Git 跟踪 + 决策层 decisions/ Git 跟踪 + 个人层 .agents/<成员>/ Git 忽略）；AI 权限为起草-确认制（可起草共享层修改，经人工 review 合并后生效，不做绝对只读）；个人层含 context.md（当前任务上下文）与 scratchpad.md（跨会话持久草稿，区别于 temp_* 用后即删）；决策序号晋升时刻认领（读 _INDEX.md 取 max+1，序号↔vN 一一对应，草稿阶段不编号）；并发撞号四条规则（认领/报警：_INDEX.md 尾部追加必然冲突/修复：后合并者整体+N/兜底：验收查序号无重复）；多人模式决策文件必填作者行、_INDEX.md 增加作者列；AGENTS.md 多人协作章节（仅多人模式生成）。单人模式产物与章节完全不变。
- **摘要**：方案源自用户与 Kimi 的讨论，经修正采纳——修正点：共享层 AI 不做绝对只读（会堵死文档先行流程），改起草-确认制；决策层允许 AI 起草新决策（一决策一文件本就为多人并发优化）；"谁写的"进元数据（作者行）而非文件名，序号留给全局顺序、在晋升时刻分配，_INDEX.md 尾部冲突是系统唯一的串行化点和报警器而非故障。本仓库为单人模式，不建 .agents/。
