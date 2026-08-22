# matrix.yaml `kind` 字段

| kind | 何时用 | 典型命令 | 无 PBT 框架？ |
|---|---|---|---|
| `pbt` | 有 QuickCheck/Hypothesis/fast-check 等，或 stdlib 随机搜索 | `{python} -m pytest tests/pt_*.py` | 可用 stdlib 随机代替库 |
| `example` | Bash/Go/Rust 等只有表驱动或脚本断言 | `bash scripts/test.sh`、`go test ./...` | ✅ 默认落点 |
| `contract` | OpenAPI / JSON Schema / 矩阵自检 | `npx @redocly/cli lint …`、`{python} validate.py` | ✅ |
| `manual` | Spec 里保留 `P-*`，人工 checklist | 无 `test.command`，runner **跳过** | ✅ |

## 原则

- **Properties（`P-*`）写在 Spec**，与语言无关。
- **`PT-*` 实现按 `kind` 选**，不要给没有 PBT 库的语言硬塞 `pbt`。
- `manual` 模块仍可写 `watch`，用于文档提醒，但不会进 pre-commit 自动跑。

## 示例模块（本沙盒）

| id | kind | watch |
|---|---|---|
| `example-register` | pbt | `skills/spec-writing/**` |
| `example-readme` | example | `README.md` |
| `example-matrix-contract` | contract | `matrix.yaml` |
| `docs-manual-only` | manual | `BACKLOG.md`（不执行） |

## 与旧字段 `pbt:` 的关系

- 新矩阵用 `kind:`；`pbt: true` 仅作兼容，未写 `kind` 时视为 `pbt`。
- 未写 `kind` 且 `pbt: false` → 视为 `manual`。
