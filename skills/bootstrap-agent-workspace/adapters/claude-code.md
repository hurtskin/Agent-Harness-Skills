# Claude Code 适配器

## 检测信号

- 项目存在 `CLAUDE.md`、`CLAUDE.local.md` 或 `.claude/`
- 当前客户端明确为 Claude Code

## 官方入口

Claude Code 使用项目 `CLAUDE.md` 或 `.claude/CLAUDE.md`，并支持 `.claude/rules/*.md`。`CLAUDE.md` 可通过 `@path` 导入其他文件。

## 生成策略

1. 本适配器只处理 Claude 原生入口，不创建任何公共核心文档。
2. 仅当 `available_artifacts` 中至少存在一个需要 Claude 自动加载的公共文件时，才生成或升级 `CLAUDE.md`。
3. 将 `CLAUDE.md` 作为薄 P0 入口：
   - 有 `AGENTS.md` 时只加入对应 `@` 导入；协作原则、红线与踩坑教训已在其内，无需另行导入。
   - 不直接导入 `decisions/` 或 `BACKLOG.md`；在入口中列为 P1/P2 路径与读取条件。
   - `.claude/rules/*.md` 仅承载 Claude 专属或路径条件规则，不重复导入 `AGENTS.md` 已提供的事实。
4. 若没有可用公共文件，不新建空壳 `CLAUDE.md`；已有入口默认保留，不追加失效引用。
5. 如项目已有 `.claude/CLAUDE.md`，先询问保留该位置还是迁移到根目录，不得同时维护两份不同入口。
6. 相对导入按入口所在目录计算：根 `CLAUDE.md` 使用 `@AGENTS.md`；`.claude/CLAUDE.md` 使用 `@../AGENTS.md`，其他路径同理增加 `../`。

## 可选规则拆分

需要路径规则时可生成 `.claude/rules/*.md`，但仅写 Claude 专属范围或路径触发规则。通用项目事实仍来自实际可用的公共事实源。

## 兼容边界

- 适配器不得为了生成 Claude 入口而创建 `AGENTS.md`、decisions/ 或 `BACKLOG.md`。
- 未选择核心文档且公共文件不存在时，允许本次只配置 drift-check 等工具，不生成 Claude 项目规则入口。
- 适配结果仅在 `AGENTS.md` 已存在或本次将生成时写入工具适配表，否则只在执行结果中报告。

## 校验

- 实际生成或升级的 Claude 入口中，所有导入路径均存在或确定由所选模块生成。
- 不把 `decisions/` 全目录或单条决策全文导入启动上下文。
- 未生成入口时，不把缺少 `CLAUDE.md` 判为工具模块初始化失败。
- 若用户自定义自动加载目录，以用户确认值为准。
