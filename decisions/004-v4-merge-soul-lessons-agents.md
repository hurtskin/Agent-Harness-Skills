# v4 · soul 与 lessons 并入 AGENTS.md，五文档改三事实源（2026-08-21）

- **状态**：活跃
- **关键词**：单一事实源,soul,lessons,AGENTS.md,P0,锚点目录,一句话教训
- **相关模块**：bootstrap-agent-workspace

- **关联文档**：`skills/bootstrap-agent-workspace/`（SKILL.md、COMMON.md、README.md、workflows/core-documents.md、workflows/verification.md、adapters/*、modules/*、templates/kanban/、scripts/self_check.py）
- **变化程度**：架构变更——公共事实源从 5 个减为 3 个（`AGENTS.md`、`决策日志.md`、`排期清单.md`）；协作原则、安全红线与踩坑教训成为 `AGENTS.md` 章节，顶部锚点目录提供跳转；教训格式回归一句话式（错误做法 → 正确做法），废弃三段式要求；触发词"生成灵魂文档 / 配三件套"改为"生成协作准则 / 配 AGENTS"。
- **摘要**：所有 Agent Harness 都原生加载 `AGENTS.md`，事实并入公约数后换工具零迁移，适配器职责收窄为纯入口差异（CLAUDE.md、MCP 配置等）；分文件维护性由锚点跳转解决。旧体系 `soul.md` / `lessons-learned.md` 迁移策略见 `workflows/core-documents.md`；drift-check D5 锚点文件由 Adapter 定义，代码零改动；本仓库自身迁移作为第二步待确认（排期清单 #005）。self_check 与单测通过。
