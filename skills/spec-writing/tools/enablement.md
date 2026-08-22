# Spec 工具启用检测

> 写 Spec / 跑验证 / 更新 inventory 前读取。安装步骤在 **bootstrap**；本文件只约束**是否启用**与**怎么用**。

## 1. 检测顺序

1. 读 `AGENTS.md`「Spec 工具（可选）」表（若存在）。
2. 对表中 `探测路径` 做存在性检查（与表一致）。
3. 未启用 → 只写 Spec 正文 / 手写 inventory 草案，**不跑** runner，文末提示用 bootstrap「规范交付」或自定义勾选安装。
4. 已启用 → 按任务读 [`verify-matrix.md`](./verify-matrix.md) 或 [`drift-inventory.md`](./drift-inventory.md)。

## 2. 默认探测路径

| 工具 | 探测路径 | 未启用时 |
|---|---|---|
| verify-matrix | `specs/verification/matrix.yaml` | 不写 matrix；PT 仅文档级 |
| drift-inventory | `specs/drift/drift_inventory.py` | 不写 inventory 或仅草案不跑 drift |
| path-align | `tools/path_align_hooks/drift_lite.ps1` | 不假设 turn-end hook |

path-align 由 bootstrap 安装；verify / drift 与 Spec 生命周期绑定，归本 Skill。

## 3. 与 bootstrap 边界

- **bootstrap**：装机、AGENTS 登记、pre-commit 接线示例。
- **spec-writing**：inventory / matrix 字段约定、变更门、命令与自检。

## 4. 解释器

verify / drift runner 使用项目解释器：`$env:PYTHON` 或 `-Python`；Skill 内不搜索 venv。
