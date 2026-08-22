# v15 · 完整工具链默认路径成对 + Correctness 变更门；drift-check 降为可选（2026-08-22）

- **状态**：活跃
- **关键词**：完整工具链,路径成对,path-align,drift-check,可选高级,Correctness,变更门,Properties,PBT
- **相关模块**：bootstrap-agent-workspace, spec-writing

- **关联文档**：`skills/bootstrap-agent-workspace/SKILL.md`、`modules/path-align-hooks.md`、`modules/drift-check.md`、`skills/spec-writing/SKILL.md`（第 5 部分附 + Correctness 变更门）、`specs/skills/bootstrap-agent-workspace/spec.md`、`specs/skills/spec-writing/spec.md`、`AGENTS.md`、`BACKLOG.md`
- **变化程度**：产品定调——（1）bootstrap「完整工具链」默认模块改为「核心工作区文档 + 排期清单 + 路径成对钩子」；`drift-check`（D1–D6）移出所有默认套餐，仅自定义可选，并标明偏 Python + 特定 Spec 布局、需维护 Adapter。（2）`spec-writing` 钉死 Correctness 变更门：写 `P-*` 与跑 `PT-*` 分轨；仅 dirty/diff 命中相关实现或性质/oracle 时才必须跑对应 PT；path-align ≠ Correctness；禁止每轮 stop 全仓 PBT；PT 语言不绑定 Python。（3）path-align 模板保持 Harness 无关（通用脚本 + 宿主自行接线）。
- **摘要**：日常多语言 / Skill 仓库用 L0 路径成对即可覆盖「单边改文档/代码」痛点；结构扫描 drift-check 与行为证明 Correctness 分层，互不替代、互不默认捆绑。本决策闭环此前已落地的文档与模板变更，并约束后续排期不得再把 drift-check 写成完整工具链默认项。
