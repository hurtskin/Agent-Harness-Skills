# 决策索引

> 决策检索入口：先按关键词查本表定位文件，再读对应决策文件；文件名自带版本和关键词，`ls decisions/` 可直接浏览全史。新增决策 = 新建文件（`序号-版本-关键词.md`）+ 本表追加一行。旧决策被修正时：编辑对应文件，状态改「归档（见 后继序号）」。

| 文件 | 版本 | 关键词 | 状态 | 相关模块 |
|---|---|---|---|---|
| [001](001-v1-init-workspace.md) | v1 | 初始化,工作区,单一事实源,P0/P1/P2,changelog-rag,MCP | 归档（见 009） | global |
| [002](002-v2-rename-agent-harness.md) | v2 | 术语,更名,Hermes,Agent Harness,触发词 | 活跃 | global |
| [003](003-v3-lessons-resident-trae.md) | v3 | Trae,规则目录,常驻,P2,按需加载,lessons | 归档（见 004） | bootstrap-agent-workspace |
| [004](004-v4-merge-soul-lessons-agents.md) | v4 | 单一事实源,soul,lessons,AGENTS.md,P0,锚点目录,一句话教训 | 活跃 | bootstrap-agent-workspace |
| [005](005-v5-kanban-template-generalize.md) | v5 | 排期清单,模板,通用化,Asset Radar,残留清理 | 活跃 | bootstrap-agent-workspace |
| [006](006-v6-repo-migration-three-facts.md) | v6 | 迁移,dogfood,三事实源,soul,lessons,删除 | 活跃 | global |
| [007](007-v7-skill-align-dogfood.md) | v7 | 流程校准,dogfood,活样本,11 章节,决策日志格式 | 活跃 | bootstrap-agent-workspace |
| [008](008-v8-adapter-claude-only.md) | v8 | 适配器,Claude Code,零适配,temp_*,临时文件,Spec 层级,specs 目录 | 活跃 | bootstrap-agent-workspace |
| [009](009-v9-kill-mcp-decisions-dir.md) | v9 | MCP,废弃,changelog-rag,decisions 目录,文件名索引,_INDEX,关键词检索 | 活跃 | global |
| [010](010-v10-kanban-template-decisions-closure.md) | v10 | 模板,排期清单,闭环,decisions,残留检查,glob,drift-check 适配 | 活跃 | bootstrap-agent-workspace |
| [011](011-v11-rename-backlog.md) | v11 | 更名,排期清单,BACKLOG,文件名,英文命名,kanban | 活跃 | bootstrap-agent-workspace |
| [012](012-v12-add-spec-writing-skill.md) | v12 | spec-writing,新 Skill,收编,发布单元,README,适配声明,crawl 残留 | 活跃 | spec-writing |
| [013](013-v13-collaboration-mode.md) | v13 | 多人协同,协作模式,collaboration_mode,初始化询问,项目定位,标记 | 活跃 | bootstrap-agent-workspace |
| [014](014-v14-multi-collab-agents-layer.md) | v14 | 多人协同,协作模式,.agents,个人层,共享宪法,晋升流程,序号认领,撞号,起草确认制,gitignore | 活跃 | bootstrap-agent-workspace |
| [015](015-v15-path-align-default-correctness-gate.md) | v15 | 完整工具链,路径成对,path-align,drift-check,可选高级,Correctness,变更门,Properties,PBT | 活跃 | bootstrap-agent-workspace, spec-writing |
