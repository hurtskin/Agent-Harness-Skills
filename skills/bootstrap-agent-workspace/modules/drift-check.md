# drift-check 模块

> 仅在用户选择 drift-check 时加载；同时加载 `python-workspace.md`。

## 生成

1. 复制 `templates/drift_check/` 到项目 `tools/drift_check/`。
2. 将 `drift_check` 加入 `tools/pyproject.toml` 的 workspace members。
3. 从 `tools/` 执行统一 `uv sync --all-packages --all-extras`。
4. 根据项目 Spec 布局选择或实现 Adapter。

## 验证

```powershell
Set-Location "tools"
uv run pytest drift_check/tests
uv run drift-check scan --project-root ..
```

因为命令从 `tools/` 执行，项目根是 `..`。

常用命令：

```powershell
uv run drift-check scan --project-root .. --format json
uv run drift-check scan --project-root .. --only D1 --only D4
uv run drift-check list-detectors
```

## 文档联动

同时选择核心文档时：

- 将 drift-check 写入文档先行流程的验证步骤。
- 在 `AGENTS.md` 记录从 `tools/` 执行的共享环境命令。

未选择核心文档时，仅生成工具，不修改其他项目规则。

## 约束

- 不在 `tools/drift_check/` 执行 `uv sync`。
- `--project-root` 必须按 `tools/` 工作目录计算为 `..`。
- ERROR 作为失败；WARNING 由用户或项目规则决定。
- 项目不是 `.trae/specs/` 布局时，先适配再把扫描设为强制门禁。
