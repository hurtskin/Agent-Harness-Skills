# drift-inventory 模板（bootstrap 安装到 `specs/drift/`）

由 bootstrap `drift-inventory` 模块复制到消费者项目。用法见 `skills/spec-writing/tools/drift-inventory.md`。

## 安装后路径

```text
specs/drift/
├── drift_inventory.py
├── language_profiles.yaml
├── run_drift.ps1 | run_drift.sh
└── pilot/                    # 示例；各功能目录另有 inventory.yaml
```

各 Spec 目录：`specs/{领域}/{功能}/inventory.yaml`（与 spec.md 同目录）。

## 快速命令

```powershell
powershell -NoProfile -File specs/drift/run_drift.ps1 -Python python
```
