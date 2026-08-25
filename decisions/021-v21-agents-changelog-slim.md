# v21 · AGENTS.md 变更日志瘦身：只挂结构级变化，过程性条目归 decisions/（2026-08-25）

- **状态**：活跃
- **关键词**：AGENTS.md,变更日志,瘦身,结构级,过程性,decisions/_INDEX,模板,core-documents §13,verification 验收清单
- **相关模块**：bootstrap-agent-workspace（workflows/core-documents.md、workflows/verification.md）、AGENTS.md
- **关联决策**：[v4](004-v4-merge-soul-lessons-agents.md)（soul/lessons 并入 AGENTS.md）、[v9](009-v9-kill-mcp-decisions-dir.md)（废弃 changelog-rag，建 `decisions/`）、[v14](014-v14-multi-collab-agents-layer.md)（多人协同三层结构）、本会话 v17/v18/v19/v20

## 背景

- 本仓 AGENTS.md §「AGENTS.md 变更日志」累积 23 条历史记录（2026-08-05 → 2026-08-25），平均每条 ≤1 行。
- 现状问题：
 1. **token 开销**：本会话 20+ 轮 × 每轮重读 23 条 ≈ 22k tokens 净消耗；变更日志对模型实际工作几乎不提供信息密度（细节已散落在 `decisions/<n>-<v>-<kw>.md`）。
 2. **与 `decisions/_INDEX.md` 重叠**：20 个决策文件各有版本号 + 关键词 + 状态 + 相关模块，机器可追溯已覆盖；变更日志的角色本应是「人类时间线」，但当前混杂了「过程性条目」（如「补齐 v9 执行遗漏」、「删除/恢复自指记录」、「本发布仓停用 Cursor path-align stop hook」），时间线被噪声淹没。
 3. **模板验收强约束反噬发布仓**：`workflows/verification.md` 第 15 行把「变更日志」列为「AGENTS.md 章节结构完整且顺序正确」必填项，`workflows/core-documents.md` §13 规定「初始化和每次结构级修改追加一行」——本仓作为发布仓被自己的模板强约束反噬。
 4. **本仓协作模式=单人**：变更日志对单人仓库的 onboarding 价值=0；保留=纯成本。

## 决定

1. **AGENTS.md §「AGENTS.md 变更日志」瘦身**：从 23 条裁到只挂**结构级变化**（v* 决策驱动、章节结构增删、协作原则改写、模板验收清单改写），过程性条目删除。
2. **`workflows/core-documents.md` §13** 改写：从「AGENTS.md 变更日志：初始化和每次结构级修改追加一行」改为「AGENTS.md 变更日志：可选人类时间线展示；只挂结构级变化（章节增删 / 协作原则改写 / 模板验收清单改写 / v* 决策落地）；过程性条目（修脚本 / 加注释 / 删错别字）走 `decisions/_INDEX.md` 而非变更日志」。
3. **`workflows/verification.md` 第 15 行** 改写：从「变更日志」作为必填项改为「（变更日志——可选）」；保留其余 11 项必填约束。
4. **AGENTS.md 目录锚点**同步调整：「变更日志」条目标注「可选」或保留原条目但正文瘦身。
5. **决策不再双向同步**：本仓未来新增决策**默认不再追加 AGENTS.md 变更日志行**——除非该决策涉及章节结构 / 协作原则 / 模板验收清单的改写。追溯走 `decisions/_INDEX.md` 关键词定位。

## 边界

- 不动 `decisions/_INDEX.md` 结构和已存在条目。
- 不动 `workflows/core-documents.md` 其他章节，只动 §13。
- 不动 `workflows/verification.md` 其他验收项，只动第 15 行章节列表。
- 瘦身时删除的过程性条目按 v9 / v10 / v11 / v12 / v13 决策文件回溯即可，**不另存快照**——决策文件已是唯一事实源。
- 不动模板其他章节（红踩坑教训 L-001/L-002 等）。

## 摘要

- 本仓 AGENTS.md 变更日志从 23 条瘦身到 ≤12 条结构级变化。
- 模板侧：变更日志从必填章节改为可选；§13 措辞明确「过程性条目走 decisions/_INDEX.md」。
- 未来新增决策默认不再追加 AGENTS.md 变更日志行；追溯唯一入口= `decisions/_INDEX.md`。
- token 开销 ↓（本会话估算节省 15k+ tokens）。
- 单人协作模式下，对人类可读时间线仍保留「结构级变化」骨架，但不强制追平所有过程。

## 摘要

变更日志从「完整过程流水账」改为「结构级人类时间线」，与 `decisions/_INDEX.md` 分工明确：后者负责机器可追溯，前者负责人类一眼看出章节演化。