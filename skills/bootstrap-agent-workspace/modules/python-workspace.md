# Python 工具共享 Workspace

> 选择 drift-check 模块时加载。当前唯一的 Python 工具是 drift-check；后续增加工具时共享同一套环境。

## 目标结构

```text
tools/
├── pyproject.toml
├── uv.lock
├── .venv/
└── drift_check/
    ├── pyproject.toml
    ├── src/
    └── tests/
```

`.venv` 和 `uv.lock` 只能位于 `tools/`，不得在成员目录分别执行 `uv sync`。

## 生成 workspace

复制 `templates/tools/pyproject.toml.template` 为 `tools/pyproject.toml`，把 `<WORKSPACE_MEMBERS>` 替换为实际选择的 TOML 数组（当前为 `["drift_check"]`）。

后续增加新工具时，精准更新 members，不重建环境。

## 统一安装

所有命令从 `tools/` 执行：

```powershell
Set-Location "tools"
uv sync --all-packages --all-extras
```

这会创建或更新唯一的 `tools/.venv` 和 `tools/uv.lock`。

## 统一测试

```powershell
Set-Location "tools"
uv run pytest drift_check/tests
```

## 约束

- 不在 `tools/drift_check/` 执行 `uv sync`。
- 不生成成员级 `uv.lock` 或 `.venv`。
- 添加、移除工具后必须更新 workspace members 并从 `tools/` 重新同步。
- CLI 通过 `uv --directory <PROJECT_ROOT>/tools run ...` 使用共享环境。
