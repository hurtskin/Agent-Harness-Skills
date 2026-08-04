# Qoder 适配器

## 检测信号

- 项目存在 `.qoder/rules/`
- 当前客户端明确为 Qoder 或 Qoder CLI
- 项目已有 Qoder 配置

## 官方入口

Qoder 默认支持项目根 `AGENTS.md`、本机项目差异文件 `AGENTS.local.md`，并支持 `.qoder/rules/` 下的项目规则。Qoder CLI 可通过 `context.fileName` 将上下文入口改为单个或多个文件名。发生冲突时，Qoder Rules 的优先级高于 `AGENTS.md`。

## 生成策略

1. 本适配器不创建公共核心文档。先读取 Qoder 配置并解析 `context.fileName`。
2. 自定义入口实际存在或确定由所选模块生成时，将其作为薄 P0 入口；未配置时，仅在公共 `AGENTS.md` 可用时复用它。多个 `context.fileName` 不得重复加载同一事实源。
3. 自定义入口与 `AGENTS.md` 均不可用时，跳过 Qoder 项目规则入口，不影响独立工具模块初始化。
4. 已有 `AGENTS.local.md` 时读取并检查，只允许保存本机差异；若 soul 不可用，则仅检查它不复制现有公共事实。新建该文件必须由用户明确要求，并加入 `.gitignore`。
5. 仅当用户需要且当前 Qoder 版本确认支持 Always、Model Decision、Specific Files 或 Manual 触发时，才生成 `.qoder/rules/` 文件：Always 只放最小 P0 差异，条件触发用于 P1，P2 仍按需读取。
6. Qoder 专属规则只写触发元数据和差异内容，只能引用 `available_artifacts`；不得重复公共入口已自动加载的内容。
7. 如用户使用 Qoder CN/Lingma 变体，不假设目录相同，必须询问实际自动加载目录；可能为 `.lingma/rules/`。

## 兼容边界

- 因 `.qoder/rules/` 优先级更高，生成前只与实际可用的 `AGENTS.md` 和 soul 检查冲突。
- 规则总长度和单文件限制可能随产品版本变化；生成时保持精简并以本地版本为准。
- 不将链接作为 Qoder Rule 唯一内容；规则系统可能不解析链接，必要关键规则需最小内嵌。
- 适配结果只在 `AGENTS.md` 可用时写入工具适配表，否则在执行结果中报告。

## 校验

- 只校验解析后实际采用的入口；没有可用入口时不因缺少 `AGENTS.md` 失败。
- 若存在 `AGENTS.local.md`，确认其只承载本机差异且不覆盖实际可用的公共红线。
- 专属规则的触发类型符合用户意图，引用目标均属于 `available_artifacts`。
- Qoder/Qoder CN 的目录已由运行时证据或用户确认。
- `AGENTS.md` 可用时记录实际入口和本地覆盖状态；否则在执行结果中报告。
