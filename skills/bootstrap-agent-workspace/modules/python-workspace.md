# Python 工具共享 Workspace

> 选择 changelog-rag 或 drift-check 任一模块时加载。两个工具必须共享一套 Python 环境。

## 目标结构

```text
tools/
├── pyproject.toml
├── uv.lock
├── .venv/
├── changelog_rag/      # 仅选择时存在
│   ├── pyproject.toml
│   ├── src/
│   └── tests/
└── drift_check/        # 仅选择时存在
    ├── pyproject.toml
    ├── src/
    └── tests/
```

`.venv` 和 `uv.lock` 只能位于 `tools/`，不得在两个成员目录分别执行 `uv sync`。

## 生成 workspace

复制 `templates/tools/pyproject.toml.template` 为 `tools/pyproject.toml`，把 `<WORKSPACE_MEMBERS>` 替换为用户实际选择的 TOML 数组：

| 选择 | members |
|---|---|
| 仅 changelog-rag | `["changelog_rag"]` |
| 仅 drift-check | `["drift_check"]` |
| 两者 | `["changelog_rag", "drift_check"]` |

后续增加第二个工具时，精准更新 members，不重建环境。

## 统一安装

所有命令从 `tools/` 执行：

```powershell
Set-Location "tools"
uv sync --all-packages --all-extras
```

这会创建或更新唯一的 `tools/.venv` 和 `tools/uv.lock`。

## 统一测试

按实际成员运行：

```powershell
Set-Location "tools"
uv run pytest changelog_rag/tests
uv run pytest drift_check/tests
```

两个成员都存在时可一次运行：

```powershell
uv run pytest changelog_rag/tests drift_check/tests
```

## 约束

- 不在 `tools/changelog_rag/` 或 `tools/drift_check/` 执行 `uv sync`。
- 不生成成员级 `uv.lock` 或 `.venv`。
- 添加、移除工具后必须更新 workspace members 并从 `tools/` 重新同步。
- MCP 与 CLI 都通过 `uv --directory <PROJECT_ROOT>/tools run ...` 使用共享环境。
