# changelog-rag 模块

> 仅在用户选择 changelog-rag 时加载；同时加载 `python-workspace.md`。

## 前置条件

changelog-rag 的数据源是项目根 `决策日志.md`：

- 文件已存在：复用现有数据源，不要求同时选择核心文档。
- 文件不存在但同时选择核心工作区文档：先由核心流程创建，再配置工具。
- 文件不存在且未选择核心工作区文档：询问用户是补选核心文档、提供其他已有决策日志路径，还是取消 changelog-rag；不得生成指向不存在文件的 MCP 配置。

若用户提供其他数据源路径，将确认后的路径写入 MCP 环境变量并记录来源。

## 生成

1. 复制 `templates/changelog_rag/` 到项目 `tools/changelog_rag/`。
2. 将 `changelog_rag` 加入 `tools/pyproject.toml` 的 workspace members。
3. 从 `tools/` 执行统一 `uv sync --all-packages --all-extras`。
4. 按当前 Hermes 工具生成 MCP 配置：
   - Trae：使用 `templates/config/mcp-config.json.template`，写入项目 `.trae/mcp-config.json`。
   - OpenCode：使用 `templates/config/opencode-changelog-rag.json.template`，将其中 `mcp.changelog-rag` 增量合并到项目根已有的 `opencode.json` 或 `opencode.jsonc`；两者均不存在时创建 `opencode.json`。
5. 将 `<PROJECT_ROOT>` 替换为项目绝对路径，将 `<CHANGELOG_RAG_SOURCE>` 替换为已确认数据源的绝对路径；Trae 旧模板中的 `CHANGELOG_RAG_AGENTS_MD` 同样替换为该数据源。
6. 修改已有 OpenCode 配置时保留现有字段、注释和 JSON/JSONC 格式；不得用模板覆盖整个文件。

## 验证

```powershell
Set-Location "tools"
uv run pytest changelog_rag/tests
uv run python -m changelog_rag.server
```

第二条是 stdio Server，人工验证启动后应停止；自动验证优先运行测试。

## 文档联动

同时选择核心文档时：

- soul 启动流程改为按关键词调用 changelog-rag。
- `AGENTS.md` 增加共享环境命令和 MCP 使用说明。
- `决策日志.md` 明确由 RAG 按量检索。

未选择核心文档时，不修改不存在的 soul、AGENTS 或决策日志。

## 约束

- 数据源指向 `决策日志.md`，不是 `AGENTS.md`。
- MCP 命令的工作目录必须是项目 `tools/`，以使用共享 `.venv`。
- 不在成员目录创建第二套环境。
- 修改 Server 后提醒用户重启对应客户端的 MCP Server。
