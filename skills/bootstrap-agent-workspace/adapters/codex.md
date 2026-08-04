# Codex 适配器

## 检测信号

- 当前客户端明确为 OpenAI Codex
- 用户目录或环境存在 Codex 专属配置，例如 `$CODEX_HOME`、`~/.codex/config.toml` 或项目已记录的 Codex 适配
- 项目存在 `AGENTS.override.md` 时，将其作为候选证据并结合运行时、配置或用户确认判断

仅存在通用 `AGENTS.md` 不得判定为 Codex；按主索引询问当前工具。

## 官方入口

Codex 使用 `AGENTS.md`，并支持目录级 `AGENTS.md` 与 `AGENTS.override.md`。

## 生成策略

1. 本适配器不创建公共 `AGENTS.md`；仅当它已存在或本次选择核心工作区文档将生成时，才将其作为 Codex 入口。
2. 可用的 `AGENTS.md` 是 P0 短入口，只索引 `available_artifacts` 中的 P1/P2 soul、lessons、Spec、决策或排期路径；不得因适配 Codex 扩写其正文。
3. 核心文档未选择且 `AGENTS.md` 不存在时，跳过 Codex 项目规则入口；这不影响 changelog-rag 等独立工具模块初始化。
4. Codex 的目录级 `AGENTS.md` 仅在确有局部差异且公共入口可用时生成，承载对应目录的最小 P0/P1 差异，不复制根入口或历史。
5. 只有需要替换同目录规则时才使用 `AGENTS.override.md`，并要求用户确认；不得用 override 补造缺失的公共事实。

## 兼容边界

- 避免把完整 soul 或决策日志复制进 `AGENTS.md`。
- Codex 的目录级覆盖只承载局部差异，不复制全局规则。
- 如本地 Codex 配置指定 fallback filename 或大小限制，在 `AGENTS.md` 可用时记录到适配表，否则在执行结果中报告。

## 校验

- 仅在实际存在 Codex 规则入口时检查从项目根到工作目录的规则链。
- `AGENTS.override.md` 不会意外遮蔽必要规则。
- 入口中的引用均属于 `available_artifacts`。
- 未生成入口时，不把缺少 `AGENTS.md` 判为独立工具模块初始化失败。
