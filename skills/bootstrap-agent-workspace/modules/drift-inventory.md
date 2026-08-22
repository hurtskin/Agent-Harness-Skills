# drift-inventory 模块（结构漂移 L1/L2）

> 仅在用户选择「drift-inventory」或套餐「规范交付 / 大型协作」时加载。用法见 `skills/spec-writing/tools/drift-inventory.md`；本模块只负责**安装模板**与 AGENTS 登记。

## 生成

1. 将 `templates/drift_inventory/` 复制到项目 `specs/drift/`。
2. 立 Spec 时由 spec-writing 在各功能目录生成 `inventory.yaml`。
3. 若本次同时选择核心工作区文档：在 `AGENTS.md`「Spec 工具（可选）」表登记 `drift-inventory`，探测路径 `specs/drift/drift_inventory.py`。
4. pre-commit：见 `templates/spec_hooks/pre-commit-combined.example`（可与 verify 串联）。
5. 解释器由 Agent / 开发者指定；脚本**不**搜索 venv。

## 验证

```powershell
powershell -NoProfile -File specs/drift/run_drift.ps1 -Python python
```

## 约束

- L0 path-align 不做本模块检查；本模块是 **inventory 计数 + 符号名**（L1/L2）。
- 未选本模块：不复制 `specs/drift/`，不在 AGENTS 登记。
