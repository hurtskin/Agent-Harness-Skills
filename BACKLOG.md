# 排期清单

> 仅登记真实未完成工程项。完成项立即移除，并在 `decisions/` 新建含排期编号的闭环决策文件（追加 `_INDEX.md` 索引行）。
>
> 优先级：H = 高，M = 中，L = 低。最后更新：2026-08-23。
>
> **套餐定调（见决策 v15）**：完整工具链默认 = 核心文档 + 排期 + 路径成对；`drift-check` 仅自定义可选，不得再写回默认套餐。

## #002 Python 3.10 / 3.11 兼容覆盖（可选工具）

- **优先级**：L
- **现状**：bootstrap CI 仍以 Python 3.12 为主；`drift-check` 模板仍声明兼容 3.10+，但该模块已降为自定义可选（决策 v15），3.10/3.11 矩阵尚未验证。
- **原因**：CI matrix 未覆盖声明的最低版本；在 drift-check 非默认的前提下，该项紧迫性下降。
- **方案**：若继续维护 `templates/drift_check/`，再扩展 CI Python matrix（至少 3.10、3.11）并保留 Windows/Linux 代表性；否则可随模板退役一并关闭本项。
- **收益**：可选 Python 工具的版本声明与证据一致，避免「声明 3.10、只测 3.12」。

## 已闭环（勿复活为默认项）

- 路径成对 L0 + Correctness 变更门 + 完整工具链不含 drift-check → **决策 [015](decisions/015-v15-path-align-default-correctness-gate.md)**
