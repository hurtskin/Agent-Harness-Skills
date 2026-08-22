# verify-matrix（Correctness 验证）

> 使用前读 [`enablement.md`](./enablement.md)。未检测到 `specs/verification/matrix.yaml` 则跳过本文。

## 职责

- `matrix.yaml`：按模块声明 `kind`（`pbt | example | contract | manual`）、`watch` 路径、`test.command`。
- pre-commit / 手动：仅对 **staged 命中 watch** 的模块执行（`-PreCommit`）。
- 与 path-align、drift-inventory 独立。

## 命令

```powershell
# 全量（矩阵内非 manual 模块）
powershell -NoProfile -File specs/verification/run_verify.ps1 -Python python

# pre-commit 等价
powershell -NoProfile -File specs/verification/hooks/pre_commit_entry.ps1 -Python python

# 无 git stage 时模拟
powershell -NoProfile -File specs/verification/run_verify.ps1 -PreCommit -Paths path/to/changed/file -Python python
```

## 变更门（与 SKILL §5 附一致）

- 写 `P-*` ≠ 跑 `PT-*`；仅 dirty/diff 命中相关实现或性质正文时跑对应模块。
- `kind: manual` 不进 runner；无 PBT 框架用 `example` / `contract`。

## kind 速查

见 bootstrap 模板 `specs/verification/MATRIX_KINDS.md`（安装后路径）。

## 立 Spec 时

- 覆盖矩阵 `PT-*` 行与 `kind` 一致。
- 新模块在 `matrix.yaml` 增加 `watch` + `test`（Agent 填 `{python}` 占位）。
