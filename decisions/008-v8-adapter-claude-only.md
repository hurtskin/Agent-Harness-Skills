# v8 · 适配器收窄为仅 Claude Code；temp_* 红线；Spec 层级约定（2026-08-21）

- **状态**：活跃
- **关键词**：适配器,Claude Code,零适配,temp_*,临时文件,Spec 层级,specs 目录
- **相关模块**：bootstrap-agent-workspace

- **关联文档**：`skills/bootstrap-agent-workspace/`（SKILL.md、COMMON.md、README.md、adapters/、workflows/core-documents.md、scripts/self_check.py）、`README.md`（根）、`AGENTS.md`
- **变化程度**：删除 6 个适配器（trae/codex/opencode/pi/qoder/zcoder）和 adapter-template.example.md 及"新增适配器"流程，仅保留 claude-code.md（唯一真差异：原生入口是 CLAUDE.md）；所有原生加载 `AGENTS.md` 的工具零适配。理由：AGENTS.md 是所有 harness 的加载公约数，多数适配器已退化为空壳。红线新增临时文件规则：`temp_*` 前缀命名 + 使用后立即删除（替代原"任务结束前删除"）。core-documents.md 新增 Spec 层级约定：`specs/<模块>/<功能>/` 每节点三件套、按项目大小裁剪、只写约定不建目录。ADAPTERS 元组收窄为 `("claude-code",)`。
- **摘要**：适配器从 7 个减为 1 个；`AGENTS.md` 兜底所有原生加载它的工具，未识别工具询问用户。self_check 与单测通过。
