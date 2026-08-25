# v17 · path-align 由 Agent 按 Harness 提示自动接线（2026-08-25）

- **状态**：活跃
- **关键词**：path-align,宿主接线,Harness 提示,自动接线,turn_align,hooks.json,settings.json,SKILL §1.5/§3.2
- **相关模块**：bootstrap-agent-workspace（SKILL.md、modules/path-align-hooks.md、templates/path_align_hooks/README.md）、AGENTS.md
- **关联决策**：[015](015-v15-path-align-default-correctness-gate.md)（仅 §变化(3) 被本页修订）、v16 闭环节奏

## 背景

- v15 §变化(3) 钉死「path-align 模板保持 Harness 无关（通用脚本 + 宿主自行接线）」。
- 现 SKILL.md §3.2 路由规则 + modules/path-align-hooks.md §3 共同把「宿主 hook 注册」明示为「执行 Agent 按工具惯例自行完成」，并禁止 Agent 写任何 harness 专属配置文件作为「标准答案」。
- 用户初衷：模型既然知道当前 Harness 怎么接 hook（Trae/.claude/.cursor 各自有官方 hook 机制），就该按 Harness 自己的提示去生成对应配置文件，而不是丢个脚本让用户自己接。

## 决定

1. **废止 v15 §变化(3)**「path-align 模板保持 Harness 无关（通用脚本 + 宿主自行接线）」中**后半句**「宿主自行接线」。**保留**前半句「模板保持 Harness 无关」——模板脚本（`drift_lite.*` / `turn_align.*`）继续不写任何 Harness 假设。
2. **SKILL.md §1.5「汇报产物」清单**增补：选 path-align 时，必须把「宿主 hook 配置文件（如 `.cursor/hooks.json` / `.claude/settings.json` / 其他 Harness 惯例路径）」列在汇报中等待用户确认。
3. **SKILL.md §3.2 路由规则**改写：去掉「宿主 hook 由执行 Agent 注册」这句含义模糊的话。改为「Agent 按所识别 Harness 的官方 hook 提示生成对应配置文件，并把 `turn_align.{ps1,sh}` 注册到『轮次结束』类事件；未识别 Harness 走必问用户」。
4. **modules/path-align-hooks.md §3** 改写：去掉「禁止在本模块产物中写入某工具的 hooks 配置文件作为标准答案」。改为「Agent 按当前 Harness 的 hook 机制生成配置（不维护分 Harness 适配清单；不写『标准答案』样板；用时由 Agent 现场按 Harness 提示生成）」。
5. **templates/path_align_hooks/README.md** 顶部去掉「挂载方式由当前 Harness 的 hook 机制决定」类把责任推给用户的话；改为「模板脚本无 Harness 假设；hook 配置文件由执行 Agent 在 bootstrap 时按当前 Harness 提示生成并落地」。

## 边界

- 模板脚本本身保持 Harness 无关：本次只解除「不写宿主 hook 配置」的禁令，不引入分 Harness 适配长文。
- Harness 识别复用 SKILL §1.2 已检测结果（Claude Code 走 `adapters/claude-code.md`，Trae 与其他原生加载 `AGENTS.md` 的工具走通用分支）；未识别 Harness **必问用户**，不得默认跳过接线、不得默认套 Trae。
- 接线工作目录 = 仓库根；脚本入口固定为 `tools/path_align_hooks/turn_align.{ps1,sh}`，与现模板一致。
- 真实验证命令维持不变（不绑 Harness）。

## 破例执行

- 本决策与改动于同一会话内同步落地：先写决策 → 改 SKILL/modules/模板 README → BACKLOG 增排期项 → 闭环决策。理由：用户已在本会话明确同意「按这个方案来」，且改动范围与意图完全一致。

## 摘要

- v15 仅保留「模板 Harness 无关」前半句；后半句「宿主自行接线」被本页接管。
- path-align 套餐默认行为升级为「自动按 Harness 提示生成宿主 hook 配置文件并注册 `turn_align`」，未识别 Harness 必问。
- BACKLOG 新增排期项「按 v17 改造 path-align 自动接线」；落地完成即在闭环决策中销项。