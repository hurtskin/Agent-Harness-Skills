# drift-inventory（结构漂移 L1/L2）

> 使用前读 [`enablement.md`](./enablement.md)。未检测到 `specs/drift/drift_inventory.py` 则跳过本文。

## 职责

- 各功能目录 `inventory.yaml`（与 spec 三件套同目录）：`counts` + `bindings`（见 §2 附）。
- 全局 runner：`specs/drift/drift_inventory.py` 比对 Markdown 计数（L1）与代码符号名（L2，regex profile）。
- 不是语义字段类型深度扫描；L3 语义对比留待后续或人工 review。

## 立 Spec 时同步 inventory

在 `specs/{领域}/{功能}/inventory.yaml` 填写：

```yaml
spec_id: ...
version: ...
sources:
  spec_md: specs/.../spec.md
  tasks_md: specs/.../tasks.md
counts:
  gherkin_scenarios: N
  tc_markers: N
  properties: N
  pt_automated: N
symbols: []   # 文档用
bindings:     # L2：symbol + paths + expect.type_name + expect.members
  - symbol: EntityName
    language: python
    paths: [src/...]
    expect:
      type_name: EntityName
      members: [field_a, field_b]
```

无 PBT 框架的语言：`bindings` + `kind: example` 在 verify-matrix；inventory 仍可做 L1 计数。

## 命令

```powershell
powershell -NoProfile -File specs/drift/run_drift.ps1 -Python python

# 单模块 inventory（未来可扩展 --inventory 参数）
python specs/drift/drift_inventory.py --repo-root . --inventory specs/auth/register/inventory.yaml
```

## pre-commit

与 verify 并列第二条 hook；入口 `specs/drift/run_drift.ps1` 或包装脚本。安装见 bootstrap 模板 `hooks/README.md`（verify 同目录可参考）。

## 跨语言

`specs/drift/language_profiles.yaml` 提供 regex baseline；成员名不一致时在 `bindings` 显式写 `expect.members`，勿硬猜 `UserID` ↔ `user_id`。
