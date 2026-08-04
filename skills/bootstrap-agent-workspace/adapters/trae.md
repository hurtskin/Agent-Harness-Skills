# Trae 适配器

## 定位

Trae 是本 Skill 的基线适配器，保留当前五文档体系与现有规则目录。

## 检测信号

- 当前运行环境声明为 Trae IDE
- 项目存在 `.trae/`
- 项目存在 `.trae/rules/` 或 `.trae/mcp-config.json`

## 自动加载入口

- 项目根 `AGENTS.md`：项目上下文概要
- `.trae/rules/*.md`：Trae 规则文件，其中 `soul.md` 为完整行为准则规范源

具体加载行为可能受 Trae 客户端版本和用户配置影响；检测不到时询问用户实际自动加载路径。

## 生成策略

1. 本适配器只处理 Trae 入口和配置，不决定公共模块是否生成。
2. 用户选择核心工作区文档时，生成或升级 `.trae/rules/soul.md`、`AGENTS.md`、`决策日志.md` 和 `.trae/rules/lessons-learned.md`。
3. 用户选择排期清单时，生成或升级 `排期清单.md`。
4. 用户选择 changelog-rag 时，按对应模块生成 `.trae/mcp-config.json`；未选择时不生成。
5. `AGENTS.md` 存在或本次选择核心工作区文档时，在工具适配表登记 Trae 为 `active`；否则不为登记适配状态而擅自创建 `AGENTS.md`。

## 兼容边界

- `.trae/rules/soul.md` 是跨工具行为规范源，但保留 Trae 路径以兼容当前方案。
- 其他工具入口只索引该规范源，不反向覆盖它。
- Trae 专属 MCP 配置不得被复制为其他工具配置格式。

## 校验

- `.trae/rules/soul.md` 可达且包含完整红线。
- `AGENTS.md` 被识别为项目上下文入口。
- 启用 changelog-rag/MCP 或 `.trae/mcp-config.json` 已存在时，确认配置中的项目路径已替换。
