# Pi 适配器

## 检测信号

- 项目存在 `.pi/`
- 当前客户端明确为 Pi Coding Agent
- 用户存在 `~/.pi/agent/AGENTS.md`

## 官方入口

Pi 在启动时加载 `AGENTS.md`，来源包括 `~/.pi/agent/`、当前目录及其父目录。项目级系统提示文件位于 `.pi/`：`.pi/SYSTEM.md` 会替换默认系统提示，`.pi/APPEND_SYSTEM.md` 用于追加内容；追加文件的自动发现能力应以当前 Pi 版本为准。

## 生成策略

1. 本适配器不创建公共 `AGENTS.md`；仅在它已存在或本次核心流程将生成时，将其作为 Pi 的 P0 短入口复用。
2. AGENTS 仅索引 P1/P2 文件；决策日志和 lessons 不写入 `.pi/SYSTEM.md` 或 `.pi/APPEND_SYSTEM.md`，也不默认全文加载。
3. 核心文档未选择且项目 `AGENTS.md` 不存在时，跳过 Pi 项目规则入口，不影响独立工具模块初始化。
4. 除非用户明确要求替换 Pi 默认系统提示，否则不生成 `.pi/SYSTEM.md`。
5. 用户明确需要追加 Pi 专属系统提示，且当前版本能力得到确认时，才使用 `.pi/APPEND_SYSTEM.md` 或 `--append-system-prompt`；不得假设自动发现。
6. 系统提示文件只写 Pi 专属最小 P0 差异，并且只引用 `available_artifacts` 中的文件，不复制公共规则。
7. Pi Skills、扩展和 Prompt Templates 属于可选增强，不在工作区初始化时自动安装。

## 兼容边界

- Pi 默认不等同于其他工具的 subagent/plan 工作流，不把公共“并行子代理”规则硬映射为不存在的能力。
- 若用户安装了第三方 Pi 扩展，先询问扩展实际自动加载路径和优先级。
- 用户级 `~/.pi/agent/AGENTS.md` 不由项目 Skill 修改。
- 适配结果只在项目 `AGENTS.md` 可用时写入工具适配表，否则在执行结果中报告。

## 校验

- 项目 `AGENTS.md` 实际可用时，才检查从父目录到当前目录的规则链。
- 未经用户授权不创建或覆盖 `.pi/SYSTEM.md` 或 `.pi/APPEND_SYSTEM.md`。
- 未生成项目入口时，不把缺少 `AGENTS.md` 或工具适配表判为失败。
