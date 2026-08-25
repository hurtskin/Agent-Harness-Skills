# v18 · pre-commit 接线也按 Harness 提示自动落地（2026-08-25）

- **状态**：活跃
- **关键词**：pre-commit,verify-matrix,drift-inventory,自动接线,Harness 提示,pre-commit 框架,Git 原生 hook,bootstrap
- **相关模块**：bootstrap-agent-workspace（modules/verify-matrix.md、templates/spec_hooks/、templates/spec_verification/hooks/）、spec-writing（SKILL.md §0）、AGENTS.md
- **关联决策**：[017](017-v17-path-align-agent-host-hook.md)（path-align turn-end 已按 Harness 提示自动接线）、[015](015-v15-path-align-default-correctness-gate.md)（归档，已被 v17 接管后半句）、v16 闭环节奏

## 背景

- v17 已把 path-align 的「宿主 hook 接线」明确为「Agent 按所识别 Harness 官方提示生成宿主配置文件并注册 `turn_align`」；未识别 Harness 走必问用户。
- 现 bootstrap 在用户选「规范交付」套餐（含 verify-matrix + drift-inventory）时，相关文档措辞仍停留在 v15 时期：
  - `modules/verify-matrix.md` §3：「若用户需要 pre-commit：复制 `hooks/` 内示例，或 `templates/spec_hooks/pre-commit-combined.example`（verify + drift 串联）；**由执行 Agent 按当前工具注册**。**不**写入 Harness 专属 hook 配置样板。」
  - `templates/spec_hooks/` README 同步留「按当前工具注册」类模糊话术。
  - `templates/spec_verification/hooks/README.md` 给出三套可选安装路径（pre-commit 框架 / Git 原生 hook / 不装 hook），但未在 SKILL/modules 路线图上钉死「Agent 默认走哪一套」。
- 用户痛点：跟 path-align 同源——选了「规范交付」却没真把 pre-commit 接线落地，pre-commit 模板静静躺在 `templates/`，consumer 还得自己 `pre-commit install` 或 `cp .git/hooks/pre-commit`，等于又一份「宿主自行接线」。

## 决定

1. **pre-commit 接线同样走 v17 语义**：选 verify-matrix / drift-inventory（含「规范交付」套餐）时，**Agent 按所识别 Harness 的官方 pre-commit 机制生成对应宿主配置文件并注册**。具体落点：
   - **Git 原生 hook**：按对应 Harness 惯例，把 `templates/spec_verification/hooks/pre-commit.{example,ps1.example}`（或 `templates/spec_hooks/pre-commit-combined.example`）注册到 `.git/hooks/pre-commit`。
   - **pre-commit 框架**：按 `templates/spec_verification/.pre-commit-config.yaml.example` 生成 `.pre-commit-config.yaml` 并执行 `pre-commit install`。
   - **未识别 Harness / 宿主不支持**：落地模板与脚本，在执行结果中说明「pre-commit 仅作手动调用；未识别 Harness，未注册宿主 hook」。
   - **未识别 Harness 走必问用户**，不得默认套 Trae，不得默认跳过。
2. **`modules/verify-matrix.md` §3** 改写：去掉「由执行 Agent 按当前工具注册」这句含义模糊的话。改为「Agent 按所识别 Harness 的 pre-commit 机制生成对应宿主配置（pre-commit 框架 / Git 原生 hook 任一），并执行安装命令；未识别 Harness 走必问用户」。
3. **`templates/spec_hooks/README.md`** 顶部去掉把责任推给用户的话；改为「pre-commit 接线由执行 Agent 在 bootstrap 时按当前 Harness 提示生成并落地（决策 v18）」。
4. **`templates/spec_verification/hooks/README.md`** 保留三套可选安装路径（pre-commit 框架 / Git 原生 hook / 不装 hook），但**追加一段「Agent 默认行为」**：复用 SKILL §1.2 已识别的 Harness 类型选最匹配的一套；未识别走必问。
5. **`spec-writing/SKILL.md §0`** 同步增补「pre-commit 接线在 bootstrap（决策 v18）」一句话（已在本会话同步落地）。

## 边界

- pre-commit 框架本身（`pre-commit.com`）是跨 Harness 的第三方库，本决策只规定「何时由 Agent 调用 `pre-commit install`」与「未识别 Harness 时如何兜底」，不强制改 `pre-commit.com` 的行为。
- 模板脚本（`templates/spec_verification/hooks/*`、`templates/spec_hooks/*`）保持 Harness 无关；不写 `.git/hooks/pre-commit` 字面量样板以外的 Harness 专属 hook 配置（与 v17 边界一致）。
- 与 path-align（turn-end）互不替代：path-align 是会话级 nudge，pre-commit 是提交级门禁；两者可同仓并存。
- 真实验证命令维持不变（不绑 Harness）。

## 破例执行

- 本决策与改动于同一会话内同步落地：先写决策 → 改 `modules/verify-matrix.md` + 两个 README → `spec-writing/SKILL.md` 同步 → BACKLOG 增排期项。

## 摘要

- v17「按 Harness 提示自动接线宿主 hook」语义延伸至 pre-commit：选 verify-matrix / drift-inventory 即自动注册 pre-commit；未识别 Harness 必问。
- `templates/spec_hooks/` / `templates/spec_verification/hooks/` 仍为 Harness 无关模板，**样板注册策略由 Agent 现场按 Harness 提示决定**，不维护在本仓。
- BACKLOG 新增排期项「按 v18 改造 verify/drift pre-commit 自动接线」；落地完成即在闭环决策中销项。