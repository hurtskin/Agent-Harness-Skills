# verify-matrix 模块（Correctness 验证）

> 仅在用户选择「verify-matrix」或套餐「规范交付 / 大型协作」时加载。用法见 `skills/spec-writing/tools/verify-matrix.md`；本模块只负责**安装模板**与 AGENTS 登记。

## 生成

1. 将 `templates/spec_verification/` 复制到项目 `specs/verification/`（含 `matrix.yaml`、`run_verify.*`、`hooks/`、示例 `pilot/`）。
2. 若本次同时选择核心工作区文档：在 `AGENTS.md`「Spec 工具（可选）」表登记 `verify-matrix`，探测路径 `specs/verification/matrix.yaml`。
3. 若用户需要 pre-commit：复制 `hooks/` 内示例，或 `templates/spec_hooks/pre-commit-combined.example`（verify + drift 串联）；由执行 Agent 按当前工具注册。**不**写入 Harness 专属 hook 配置样板。
4. 解释器由 Agent / 开发者通过 `$env:PYTHON` 或 `-Python` 指定；模板脚本**不**搜索 venv。

已有 `specs/verification/` 时默认补缺失文件，不覆盖用户改过的 `matrix.yaml`（除非明确授权）。

## 验证

```powershell
powershell -NoProfile -File specs/verification/run_verify.ps1 -Python python -DryRun
```

期望：能列出矩阵模块计划；全量跑通取决于项目是否已按 matrix 配置测试。

## 约束

- 与 path-align、drift-inventory 分层：本模块是 pre-commit / 手动 **Correctness**（`kind: pbt | example | contract`），不是路径成对。
- 未选本模块：不复制 `specs/verification/`，不在 AGENTS 登记 verify-matrix。
- 日常命令与变更门规则在 **spec-writing**，不在本 Skill 重复长文。
