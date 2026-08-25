# verify-matrix 模块（Correctness 验证）

> 仅在用户选择「verify-matrix」或套餐「规范交付 / 大型协作」时加载。用法见 `skills/spec-writing/tools/verify-matrix.md`；本模块只负责**安装模板**与 AGENTS 登记。

## 生成

1. 将 `templates/spec_verification/` 复制到项目 `specs/verification/`（含 `matrix.yaml`、`run_verify.*`、`hooks/`、示例 `pilot/`）。
2. 若本次同时选择核心工作区文档：在 `AGENTS.md`「Spec 工具（可选）」表登记 `verify-matrix`，探测路径 `specs/verification/matrix.yaml`。
3. **pre-commit 接线（决策 v18）**：复用 SKILL §1.2 已识别的 Harness 类型，**Agent 按当前 Harness 的 pre-commit 机制生成对应宿主配置并安装**：
   - **Git 原生 hook**：按对应 Harness 惯例，把 `templates/spec_verification/hooks/pre-commit.{example,ps1.example}` 或 `templates/spec_hooks/pre-commit-combined.example` 注册到 `.git/hooks/pre-commit`。
   - **pre-commit 框架**：按 `templates/spec_verification/.pre-commit-config.yaml.example` 生成 `.pre-commit-config.yaml` 并执行 `pre-commit install`。
   - **未识别 Harness / 宿主不支持**：落地模板与脚本，在执行结果中说明「pre-commit 仅作手动调用；未识别 Harness，未注册宿主 hook」。
   - **未识别 Harness 走必问用户**，不得默认跳过接线，也不得默认套 Trae。
   - 不维护分 Harness 适配清单；不写「标准答案」样板；用时由 Agent 现场按 Harness 提示生成。
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
