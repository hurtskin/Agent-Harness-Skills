# drift-check 模块

> **可选高级模块**：不在「快速开始 / 完整工具链」默认套餐内；仅自定义勾选时加载，并同时加载 `python-workspace.md`。
>
> **定位：** D1–D6 静态结构扫描（三件套版本、字段表↔模型、Gherkin↔测试计数、任务状态等）。当前检测器与模板 Adapter **偏 Python / 特定 Spec 布局**；多语言或纯 Skill 文档仓库日常优先用「路径成对钩子」，不要默认装本模块。
>
> **非替代关系：** 不替代 path-align（L0 路径成对），也不替代 Spec Properties / Correctness（行为证明）。

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

D5 教训锚点检测的扫描源与锚点格式由 Adapter 定义（`lesson_refs_file()` / `parse_lesson_refs()` / `decision_log_file()`）：模板自带的 `asset_radar` 示例面向旧体系（扫描 `.trae/rules/soul.md`、`决策日志.md`，锚点是 `lessons-learned.md` 的 `§XX`）。新体系项目应在自定义 Adapter 中改写：锚点文件指向 `AGENTS.md` 的踩坑教训章节（`L-NNN` 编号），扫描源覆盖 `AGENTS.md`、`specs/**/*.md` 与 `decisions/*.md`；`decision_log_file()` 返回 `None` 或指向单个高价值决策文件均可。

## 约束

- 不在 `tools/drift_check/` 执行 `uv sync`。
- `--project-root` 必须按 `tools/` 工作目录计算为 `..`。
- ERROR 作为失败；WARNING 由用户或项目规则决定。
- 项目不是 `.trae/specs/` 布局时，先适配再把扫描设为强制门禁。
