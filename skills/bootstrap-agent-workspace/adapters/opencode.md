# OpenCode 适配器

## 检测信号

- 项目存在 `opencode.json` 或 `opencode.jsonc`
- 当前客户端明确为 OpenCode
- 用户存在 `~/.config/opencode/AGENTS.md`

## 官方入口

OpenCode 优先读取项目 `AGENTS.md`；缺失时可回退到 `CLAUDE.md`。还可通过 `opencode.json` 的 `instructions` 加载额外文件。

## 生成策略

1. 本适配器不创建公共文档。项目 `AGENTS.md` 已存在或本次将生成时，直接复用；不存在时不把它当作有效入口。
2. 只有 `available_artifacts` 中存在额外规则且用户确认需要显式加载时，才升级已有 `opencode.json/jsonc` 的 `instructions`。
3. `instructions` 只加入实际存在或确定将生成的 `.trae/rules/soul.md`、`.trae/rules/lessons-learned.md` 等规则文件。
4. 不把 `AGENTS.md` 再加入 `instructions`，避免与 OpenCode 原生加载重复。
5. `决策日志.md` 或 `排期清单.md` 实际可用时，只能在 OpenCode 实际采用的 Markdown 入口中将其列为按需读取目标；不得把说明写入 `instructions` 字段，也不得全文自动加载。没有可用 Markdown 入口时跳过该说明。
6. `AGENTS.md` 和可用 instructions 均不存在时，允许本次不生成 OpenCode 项目规则入口，只初始化用户选择的独立工具模块。
7. 选择 changelog-rag 时，使用 `templates/config/opencode-changelog-rag.json.template`：将 `mcp.changelog-rag` 增量合并到项目根已有的 `opencode.json` 或 `opencode.jsonc`，两者均不存在时创建 `opencode.json`；替换项目根和已确认数据源占位符，不得覆盖其他配置。
8. 已有 `AGENTS.md` 时不要依赖 `CLAUDE.md` 回退。

## 兼容边界

- 修改 `opencode.json/jsonc` 前必须保留现有字段与格式。
- 不假设 JSONC 可以用严格 JSON 序列化覆盖。
- OpenCode Agent/权限配置不属于公共规则，只有用户要求时才调整。
- 适配结果只在 `AGENTS.md` 可用时写入其工具适配表，否则在执行结果中报告。

## 校验

- 仅校验实际使用的入口；`instructions` 中路径存在且无重复。
- 公共规则没有被同时通过多条路径重复加载。
- `AGENTS.md` 可用时记录原生入口或自定义 instructions；不可用时不因缺少适配表失败。
