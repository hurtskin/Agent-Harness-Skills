# v20 · 模板脚本路径硬假设收敛：用 git rev-parse / __file__ 锚定 RepoRoot（2026-08-25）

- **状态**：活跃
- **关键词**：模板脚本,硬假设,git rev-parse,__file__,BASH_SOURCE,RepoRoot,language_profiles.yaml,pre_commit_entry,drift_inventory,跨布局
- **相关模块**：bootstrap-agent-workspace（templates/drift_inventory/、templates/spec_verification/、templates/spec_verification/hooks/）、AGENTS.md
- **关联决策**：[019](019-v19-v17-v18-dogfood-closure.md)（v19 dogfood 发现的两处硬假设）、[017](017-v17-path-align-agent-host-hook.md)（turn_align 已用 `git rev-parse --show-toplevel` 算 RepoRoot，作为本决策的范式来源）、[018](018-v18-pre-commit-auto-wire-by-harness.md)

## 背景

- v19 dogfood 实跑发现两类硬假设：
 1. **`templates/spec_verification/hooks/pre_commit_entry.{ps1,sh}` 硬编码 `..\..`** 算仓库根：ps1 第 17-19 行用 `Join-Path $VerifyDir '..\..'`，sh 第 6 行用 `$HERE/../../..`。两者都假设 entry 在 `<repo>/specs/verification/hooks/`，搬到 `tools/spec_verification/hooks/` 等其他位置就破。
 2. **`templates/drift_inventory/drift_inventory.py` 第 302 行 `inventory_path.parent.parent / "language_profiles.yaml"`**：硬编码 inventory 必须在某个二层深度的目录（如 `specs/drift/pilot/inventory.yaml`），但 `language_profiles.yaml` 实际与脚本同目录。
- v19 闭环时把这两类失败记进 COMMON §6.1.3「物理布局冲突」分类，并列入 BACKLOG #005。

## 决定

1. **统一范式：所有 bootstrap 模板脚本算 `RepoRoot` 时，优先 `git rev-parse --show-toplevel`，回退到 `__file__` / `$PSScriptRoot` 锚定 + 上溯直至找到 `AGENTS.md` 或 git 标记**。范式来源：决策 v17 `turn_align.ps1` / `turn_align.sh` 已使用 `git rev-parse --show-toplevel` 算 RepoRoot。
2. **`templates/spec_verification/hooks/pre_commit_entry.ps1`** 改写：用 `git rev-parse --show-toplevel` 算 `$RepoRoot`（与 v17 turn_align 同款）；保留 `-RepoRoot` 入参作为覆盖。`$VerifyDir` 仍由 `$PSScriptRoot` 锚定，不依赖 `..\..`。
3. **`templates/spec_verification/hooks/pre_commit_entry.sh`** 改写：同样改用 `git rev-parse --show-toplevel` 算 `$ROOT`。
4. **`templates/drift_inventory/drift_inventory.py` 第 302 行** 改写：`Path(__file__).resolve().parent / "language_profiles.yaml"` 替代 `inventory_path.parent.parent / "language_profiles.yaml"`。`--profiles` 入参与 `default` 都重命名为「脚本同目录」。
5. **`templates/spec_verification/hooks/README.md` 顶部** 加一段「硬假设警告」：`run_verify.{ps1,sh}` 与 `pre_commit_entry.{ps1,sh}` 默认在 `<repo>/specs/verification/` 或 `<repo>/tools/spec_verification/` 等任意深度都能工作（已用 git rev-parse / `$PSScriptRoot` 锚定），迁移到其他位置也无需改路径。
6. **`templates/drift_inventory/README.md` 顶部** 加一段「硬假设警告」：`drift_inventory.py` 与 `language_profiles.yaml` / `run_drift.{ps1,sh}` 必须在同一目录；`run_drift.{ps1,sh}` 与 `drift_inventory.py` 必须在同一目录（已用 `$PSScriptRoot` 锚定）；`inventory.yaml` 路径仍由调用方决定。
7. **不动** `run_verify.{ps1,sh}`（已经用 `$PSScriptRoot` / `BASH_SOURCE`，无硬假设）；**不动** `pre_commit.{example,ps1.example}`（这两个是给用户复制到 `.git/hooks/pre-commit` 的纯文本示例，调用者自带完整路径）。

## 边界

- 本决策只动 `templates/` 下的脚本与 README，不动发布仓本身的 `tools/` 或 `specs/` 副本（那些副本每次 Copy-Item 同步刷新，无独立逻辑）。
- 不强制消费者项目必须用 git：脚本在非 git 仓库下运行时，`git rev-parse` 静默失败，回退到 `__file__` 上溯到 `AGENTS.md` 或仓库根的启发式（详见修后脚本注释）。
- 不动现有 v17 turn_align 脚本（已是范式）。
- 不修 `pre-commit.example` / `pre-commit.ps1.example` 字面量里的 `specs/verification/` 路径——这两个是 Git 原生 hook 的安装示例，安装时调用方自带 `pwd` 在仓库根，路径以「相对仓库根」理解，与本决策无冲突。

## 摘要

- 模板脚本路径硬假设全部改为「git rev-parse → `__file__`/`$PSScriptRoot` → AGENTS.md 锚定」三层回退。
- 消费者项目可以把 `specs/verification/` 或 `drift_inventory/` 模板自由复制到 `specs/`、`tools/`、项目约定的其他目录，脚本无需改路径。
- 失败兜底（COMMON §6.1.3「物理布局冲突」）的具体两类问题（pre_commit_entry `..\..`、drift_inventory `parent.parent`）一并消除。
- BACKLOG #005 闭环。