# Hermes Agent Skills — Agent 导航（P0）

## 项目定位

Hermes Agent Skills 是面向 Trae 与主流 Hermes 编程工具的多 Skill 自包含发布仓库。根目录只负责索引；`skills/<name>/` 各自独立发布。

- **Scope**：Skill 激活与按需路由、公共事实源治理、客户端适配、模板工具及其自动校验。
- **Non-goals**：不在根目录发布 Skill；不让一个 Skill 依赖相邻 Skill 或根目录运行时文件；不把本仓库扩展为业务应用或共享运行时框架。
- **协作语言**：中文；代码、命令和路径保持原文。

## 当前入口

| 入口 | 用途 |
|---|---|
| [`README.md`](README.md) | 仓库索引、发布边界和两个现有 Skill 入口 |
| [`skills/bootstrap-agent-workspace/SKILL.md`](skills/bootstrap-agent-workspace/SKILL.md) | 工作区初始化激活与模块路由 |
| [`skills/task-handoff/SKILL.md`](skills/task-handoff/SKILL.md) | 可验证任务交接协议 |
| [`排期清单.md`](排期清单.md) | 当前未完成工程项；任务开始时按相关性读取 |

当前无单独活跃 Spec；实施以用户已确认任务和对应 Skill 内流程文档为准。

## 真实验证命令

在仓库根目录执行：

```powershell
uv run --no-project python skills/bootstrap-agent-workspace/scripts/self_check.py
uv run --no-project python -m unittest discover -s skills/bootstrap-agent-workspace/tests -v
```

在 `tools/` 执行共享工具验证：

```powershell
uv sync --all-packages --all-extras
uv run pytest changelog_rag/tests
```

## P1 / P2 索引

| 级别 | 路径 | 读取条件 |
|---|---|---|
| P1 | `README.md` | 确认仓库定位、发布约定或 Skill 入口时 |
| P1 | `skills/<name>/SKILL.md` 及其按需路由文档 | 修改对应 Skill 或执行其流程时；不得预读未选模块 |
| P1 | `.github/workflows/bootstrap-agent-workspace.yml` | 修改或核对现有 CI 验证范围时 |
| P1 | `排期清单.md` | 规划任务、判断是否闭环待办时 |
| P2 | `决策日志.md` | 追溯决策时由 changelog-rag 按量检索，或按关键词局部读取 |
| P2 | `.trae/rules/lessons-learned.md` | 问题命中既有教训编号时按需读取；即使 Trae 自动加载规则目录，也不得将其正文复制进 P0 |
| P2 | 归档 Spec（当前无） | 仅在追溯对应历史主题时读取 |

## 文档职责

- `.trae/rules/soul.md`：P0 稳定原则与安全红线。
- `AGENTS.md`：P0 短导航、当前入口和 P1/P2 索引。
- `排期清单.md`：只保留未完成项；完成即移除，闭环事实追加到决策日志。
- `决策日志.md`：P2 append-only 决策索引，由 changelog-rag 按量检索。
- `.trae/rules/lessons-learned.md`：P2 稳定编号的跨任务教训，不作常驻正文。

## Agent 工具适配

| 工具 | 自动加载入口 | 状态 | 来源 | 最后确认日期 |
|---|---|---|---|---|
| Trae | `AGENTS.md` + `.trae/rules/*.md` | active | 运行时证据 | 2026-08-05 |

## AGENTS.md 变更日志

- 2026-08-05：初始化规范治理短导航，登记 Trae 入口，建立 P1/P2 索引和共享工具命令。
