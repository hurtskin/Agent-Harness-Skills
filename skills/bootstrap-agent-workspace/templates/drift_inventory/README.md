# drift-inventory 模板（bootstrap 安装到 `specs/drift/`）

由 bootstrap `drift-inventory` 模块复制到消费者项目。用法见 `skills/spec-writing/tools/drift-inventory.md`。

> **路径硬假设（决策 v20）**：`drift_inventory.py` 用 `Path(__file__).resolve().parent` 锚定资源目录，自动找同目录的 `language_profiles.yaml`；`run_drift.{ps1,sh}` 用 `$PSScriptRoot` / `BASH_SOURCE` 锚定，可放在 `<repo>/specs/drift/`、`<repo>/tools/drift_inventory/`、或项目约定的其他目录，**无需改脚本**。调用方只需保证 `drift_inventory.py` 与 `language_profiles.yaml`、`run_drift.{ps1,sh}` **三者同目录**。

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
