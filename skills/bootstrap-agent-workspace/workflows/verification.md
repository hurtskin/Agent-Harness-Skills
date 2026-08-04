# 按需初始化验收

> 执行结束时加载，只校验用户选择的范围。

## 通用

- [ ] 已有文件未被无授权覆盖
- [ ] `AGENTS.md` 已存在或本次选择核心文档时，工具适配表记录实际客户端和入口
- [ ] `AGENTS.md` 不可用时，执行结果已报告适配状态，且未为登记状态创建核心文档
- [ ] 未选模块未生成源码、依赖、配置或强制规则
- [ ] 所有链接和相对路径可达

## 核心文档（选择时）

- [ ] soul、AGENTS、决策日志、lessons 职责不重叠
- [ ] 工具入口只索引公共事实
- [ ] 文档中的工具说明与实际选择一致

## 排期（选择时）

- [ ] 只包含未完成项
- [ ] 闭环规则指向决策日志

## Python workspace（任一工具选择时）

- [ ] `tools/pyproject.toml` members 与实际目录一致
- [ ] 仅存在 `tools/.venv` 和 `tools/uv.lock`
- [ ] 所有安装、测试和运行命令从 `tools/` 执行

## changelog-rag（选择时）

- [ ] MCP 中配置的数据源文件实际存在，且默认数据源为 `决策日志.md`
- [ ] 数据源不存在时已补选核心文档、提供有效替代路径或取消模块
- [ ] MCP 配置使用当前客户端原生格式，并使用 `uv --directory <PROJECT_ROOT>/tools run`
- [ ] OpenCode 使用项目根 `opencode.json/jsonc` 的 `mcp.changelog-rag`，`type` 为 `local` 且 `command` 为单一数组；已有配置的其他字段与 JSON/JSONC 格式未被覆盖
- [ ] `uv run pytest changelog_rag/tests` 通过

## drift-check（选择时）

- [ ] Adapter 匹配项目 Spec 布局
- [ ] 从 `tools/` 执行时 `--project-root ..`
- [ ] `uv run pytest drift_check/tests` 通过
