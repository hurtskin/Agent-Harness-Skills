# v9 · 废弃 MCP 与 changelog-rag，决策日志改为 decisions/ 目录（2026-08-21）

- **状态**：活跃
- **关键词**：MCP,废弃,changelog-rag,decisions 目录,文件名索引,_INDEX,关键词检索
- **相关模块**：global

- **关联文档**：`skills/bootstrap-agent-workspace/`（SKILL.md、COMMON.md、README.md、workflows/core-documents.md、workflows/verification.md、modules/、templates/、scripts/self_check.py）、`decisions/`、`AGENTS.md`、`.github/workflows/bootstrap-agent-workspace.yml`、`tools/`（已删除）、`.trae/mcp-config.json`（已删除）
- **变化程度**：删除 changelog-rag 模块（模块文档、templates/changelog_rag/、三个 MCP 配置模板）、本仓库实装（`.trae/mcp-config.json`、`tools/` 整个 workspace）、CI 的 changelog-rag 测试 step、self_check.py 的相关检查与测试、失效排期项 #003/#004。决策记录从单文件 `决策日志.md` 改为 `decisions/` 目录：每个决策一个文件（命名 `序号-版本-关键词.md`），`_INDEX.md` 维护唯一索引表（文件/版本/关键词/状态/相关模块）；v1–v8 已全部迁移为独立文件，旧 `决策日志.md` 删除。
- **摘要**：RAG 的语义检索能力与 AI 实际的关键词查询行为不匹配，安装维护成本高；项目级 MCP 配置污染 harness。文件系统即索引：`ls decisions/` 一眼看全史，_INDEX.md 关键词表补足文件名猜不中的情况；每决策一文件天然支持 P2 按需局部读取，多人协作冲突收窄到 _INDEX.md。P2 检索路径改为：读 `decisions/_INDEX.md` 按关键词定位 → 读对应决策文件。
