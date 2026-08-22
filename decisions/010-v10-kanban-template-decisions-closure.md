# v10 · 排期清单模板补齐 decisions/ 闭环规则；登记 L-001（2026-08-21）

- **状态**：活跃
- **关键词**：模板,排期清单,闭环,decisions,残留检查,glob,drift-check 适配
- **相关模块**：bootstrap-agent-workspace

- **关联文档**：`skills/bootstrap-agent-workspace/templates/kanban/排期清单.md.template`、`modules/drift-check.md`、`AGENTS.md`
- **变化程度**：v9 执行补漏——排期清单模板的闭环规则从 `决策日志.md` 单文件改为 decisions/ 工作流（新建决策文件 + `_INDEX.md` 追加索引行）；drift-check 模块的 D5 适配说明补充新体系扫描源（`AGENTS.md`、`specs/**/*.md`、`decisions/*.md`）。模板代码 `templates/drift_check/` 内的 `asset_radar` 示例与测试保持旧体系 fixture 不动（自包含示例，模块文档已说明改写方式）。
- **摘要**：模板是初始化的直接产物，必须与新体系一致；v9 残留检查用 `*.md` glob 漏掉 `.template` 后缀文件，教训 L-001 登记：一致性检查不按文件后缀过滤。
