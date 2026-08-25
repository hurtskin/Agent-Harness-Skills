# v19 · 闭环 v17/v18：path-align + pre-commit 自动接线 dogfood 落地（2026-08-25）

- **状态**：活跃
- **关键词**：v17,v18,自动接线,dogfood,turn_align,pre_commit_entry,模板布局,失败兜底,COMMON §6.1,发布仓
- **相关模块**：bootstrap-agent-workspace（COMMON.md §6.1、modules/path-align-hooks.md、modules/verify-matrix.md）、spec-writing（SKILL.md §0）、AGENTS.md
- **关联决策**：[017](017-v17-path-align-agent-host-hook.md)、[018](018-v18-pre-commit-auto-wire-by-harness.md)、BACKLOG #003（v17 dogfood）、BACKLOG #004（v18 dogfood）

## 背景

- v17 / v18 已落「按 Harness 提示自动接线宿主 hook / pre-commit」决策语义，但都是「定调」——决策文件本身不证明执行链路通畅。
- BACKLOG #003「按 v17 改造 path-align 自动接线」与 BACKLOG #004「按 v18 改造 verify/drift pre-commit 自动接线」明确：定调≠闭环，必须 dogfood 试跳才能销项。

## 决定

1. **本仓（`Agent Harness Skills` 发布仓）作为 dogfood 试点**：在真实 Cursor/Trae 环境下把 `templates/path_align_hooks/` 复制到 `tools/path_align_hooks/`，把 `templates/spec_verification/` 复制到 `specs/verification/`，跑最小试跳验证脚本链路通畅。
2. **发布仓本身不接宿主 hook**（沿用 AGENTS.md 变更日志 2026-08-22 的有意决定）：`.cursor/hooks.json` 留空、`tools/` 不入库、`specs/` 不入库。dogfood 只验证脚本链路，不验证宿主配置文件已注册。
3. **`skills/bootstrap-agent-workspace/COMMON.md` §6.1「v17/v18 自动接线 dogfood 步骤」**：把本次 dogfood 流程固化为「消费者项目首次初始化必跑」的最小步骤 + 期望输出 + 失败兜底。三类失败情况必须汇报而非默认跳过：(a) 未识别 Harness；(b) 宿主不支持 turn-end / pre-commit 事件；(c) 模板物理布局与目标项目冲突（如 `pre_commit_entry.ps1` 硬编码 `..\..` 相对路径，迁到 `tools/` 之外的目录会破）。
4. **BACKLOG #003 与 #004 闭环**：本决策落地后两条排期项一并移除，移入 v19 闭环记录。

## 证据（本仓 dogfood 实跑，2026-08-25）

### A · path-align 链路（v17）

- 物理位置：`tools/path_align_hooks/{drift_lite,turn_align}.{ps1,sh}` + README（已存在，2026-08-22 起的本地缓存）。
- 试跳命令：`echo '' | powershell -NoProfile -ExecutionPolicy Bypass -File tools/path_align_hooks/turn_align.ps1`
- 试跳命令（带 stop 事件）：`echo '{"status":"completed","loop_count":0}' | powershell -NoProfile -ExecutionPolicy Bypass -File tools/path_align_hooks/turn_align.ps1`
- 期望输出：`stderr: [turn_align] status=... parse_ok=...`；`stdout: {}` 或 nudge JSON；`exit 0`。
- 实跑结果：stdout 含 `[turn_align] status=completed parse_ok=True risk_code=CODE_WITHOUT_SPEC actions=2`；nudge JSON 含 `[A1] Add or update specs/` + `[A2] Or briefly explain why this turn is intentionally code-only`。`risk_code=CODE_WITHOUT_SPEC` 是**本仓预期**：发布仓 `.gitignore` 屏蔽 `specs/`，drift-lite 按消费者项目语义把 v17/v18 决策产生的 7 个 `skills/` 改动判为契约/实现单边漂移。**这是 v17 决策的副作用，但 v17 决策本身要求「未识别 Harness 必问」，本仓是发布仓故意不接 host hook**，所以本仓受 drift-lite 误报是**符合预期**。详见 §4 边界。

### B · pre-commit 链路（v18）

- 物理位置：`specs/verification/{run_verify,matrix.yaml,hooks/,...}`（已存在，本轮 `Copy-Item -Recurse -Force` 同步刷新）。
- 试跳命令：`powershell -NoProfile -ExecutionPolicy Bypass -File specs/verification/hooks/pre_commit_entry.ps1 -Python python`
- 期望输出：`stderr: [verify] pre-commit: nothing to run (ok)`；`exit 0`。
- 实跑结果：3 模块全 SKIP（无 staged watch 命中），`[verify] done ran=0 skipped=3 python=python` + `[verify] pre-commit: nothing to run (ok)`，`exit 0`。**链路通畅**。
- 额外发现：把模板搬到 `tools/spec_verification/`（而非 `specs/verification/`）会触发 `pre_commit_entry.ps1` 第 31 行 `run_verify.ps1` 路径计算错误（`..\..` 算到仓库根漏一层）。**模板对消费者项目布局有硬假设**：`pre_commit_entry.ps1` 只在 `specs/verification/hooks/` 下正常工作。这条作为 v18 失败兜底分类「物理布局冲突」的具体例子写进 COMMON §6.1.3。

### C · drift-inventory 链路（跳过）

- 试跳命令：`powershell -NoProfile -File tools/drift_inventory/run_drift.ps1 -Inventory tools/drift_inventory/inventory.yaml -Format text`
- 实跑结果：`FileNotFoundError: 'E:\\dev-py\\Skills Creater\\tools\\language_profiles.yaml'`。
- 原因：`drift_inventory.py` 在仓库根找 `language_profiles.yaml`，但它在 `tools/drift_inventory/` 子目录内。同类「模板对项目布局的硬假设」问题。本决策**不**展开修复 `drift_inventory.py` 路径解析，标记为已知失败兜底分类「物理布局冲突」的另一个例子，留待后续决策。

## 边界

- 本决策只闭环 v17 + v18 的 dogfood 执行路径，**不**修复 `drift_inventory.py` 路径解析问题；那是独立排期项。
- 本决策**不**强制本仓启用 `.cursor/hooks.json` 或 `.git/hooks/pre-commit`：发布仓 AGENTS.md 变更日志 2026-08-22 已明示不接，v17/v18 的「必须接宿主 hook」语义适用于**消费者项目**。
- 本决策**承认** v17 在本仓的副作用：`drift-lite` 会在本仓报 `CODE_WITHOUT_SPEC`。该误报通过 `PATH_ALIGN_NUDGE=0` 或 `STOP_ALIGN_FOLLOWUP=0` 关停，符合 AGENTS.md「路径成对（L0，stop / drift-lite）」条款。

## 摘要

- v17（path-align 自动接线）：脚本试跳通过；本仓副作用 `CODE_WITHOUT_SPEC` 已说明并可关停。
- v18（pre-commit 自动注册）：脚本试跳通过；`pre_commit_entry.ps1` 对项目布局硬假设已记录为失败兜底分类。
- `drift-inventory` 路径解析错误：留作已知问题，独立排期处理。
- COMMON §6.1 已落地 dogfood 步骤 + 失败兜底；BACKLOG #003 / #004 一并销项。

## BACKLOG 同步

| 旧项 | 处理 |
|---|---|
| #003「按 v17 改造 path-align 自动接线」 | 已闭环：v17 决策 + 本仓狗食 + COMMON §6.1.1 |
| #004「按 v18 改造 verify/drift pre-commit 自动接线」 | 已闭环：v18 决策 + 本仓狗食 + COMMON §6.1.2 |