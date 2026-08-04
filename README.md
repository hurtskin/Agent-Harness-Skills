# Hermes Agent Skills

面向 Trae 与主流 Hermes 编程工具的可独立发布 Skills 集合。仓库根目录只负责索引；每个 `skills/<name>/` 目录都是自包含发布单元。

## Skills

| Skill | 用途 | 入口 |
|---|---|---|
| `bootstrap-agent-workspace` | 初始化跨 Trae、Claude Code、Codex、OpenCode、Pi、Qoder、ZCoder 的 Agent 工作区，可选 changelog-rag 与 drift-check | [`skills/bootstrap-agent-workspace/SKILL.md`](./skills/bootstrap-agent-workspace/SKILL.md) |
| `task-handoff` | 通过接任子代理审计当前任务上下文，生成可验证的任务交接包 | [`skills/task-handoff/SKILL.md`](./skills/task-handoff/SKILL.md) |

## 目录结构

```text
.
├── README.md
├── skills/
│   ├── bootstrap-agent-workspace/
│   │   ├── SKILL.md
│   │   ├── COMMON.md
│   │   ├── adapters/
│   │   ├── modules/
│   │   ├── workflows/
│   │   └── templates/
│   └── task-handoff/
│       ├── SKILL.md
│       └── README.md
```

## 发布约定

- 每个 `skills/<name>/` 的目录名必须与 `SKILL.md` frontmatter 中的 `name` 一致。
- 每个 Skill 必须自包含，不能依赖相邻 Skill 或仓库根目录中的运行时文件。
- 发布单个 Skill 时，只打包对应的 `skills/<name>/` 目录。
- 仓库根目录不放 `SKILL.md`，避免被识别为第三个 Skill 或产生重复入口。

## 安装

将需要的发布单元复制到宿主工具的 Skills 目录。例如 Trae：

```text
<skills-root>/bootstrap-agent-workspace/SKILL.md
<skills-root>/task-handoff/SKILL.md
```

具体能力和使用方式请阅读各 Skill 自己的 `SKILL.md` 或 README。
