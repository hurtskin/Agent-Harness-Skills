# v16 · 闭环 BACKLOG #001：task-handoff 校验器、对拍测试与 CI 落地（2026-08-23）

- **状态**：活跃
- **关键词**：task-handoff,校验器,validate_handoff,双语言,ps1/sh,对拍,fixtures,CI,单条 evidence 缺陷,移除 py
- **相关模块**：task-handoff

- **关联文档**：`skills/task-handoff/SKILL.md`、`skills/task-handoff/README.md`、`skills/task-handoff/scripts/validate_handoff.{ps1,sh}`、`skills/task-handoff/tests/`、`.github/workflows/bootstrap-agent-workspace.yml`、`AGENTS.md`、`BACKLOG.md`
- **变化程度**：（1）落地 §4.1 确定性校验器双语言参考实现——PowerShell（Windows）与 bash+gawk（Linux/macOS）共享同一 Schema 与失败语义，均只依赖系统内置工具；Python 版因冗余移除（ps1+sh 已覆盖所有平台，py 还需 PyYAML 且是唯一不做 CRLF 归一化的实现）。（2）新增 `skills/task-handoff/tests/`：`good.md` + `bad1..5` 六个 fixture 与 `test_validator_parity.py`——`good.md` VALID 且摘要等于文件自身 SHA-256，`bad1..5` 一致拒绝；按 OS 分流（Linux 跑 bash、Windows 跑 ps1），CI 矩阵 ubuntu/windows 各跑全量 fixtures。（3）现有 CI 矩阵增补 task-handoff tests 步骤。（4）修复 `validate_handoff.ps1` 缺陷：尾部单条 evidence 未 flush，使 SKILL §4 初始化候选（单条 unverified）被误判非法。（5）SKILL/README 增「交接完成后删除交接文档」第 5 步与生命周期说明。
- **摘要**：闭环 BACKLOG #001，校验器、测试与 CI 全部落地；对拍测试顺带暴露并修复 ps1 单条 evidence 丢失缺陷（此前被 bad1..5 全 exit-1 掩盖），双语言等价经本机 WSL 实测 + 双路 CI（ubuntu/windows）确认。