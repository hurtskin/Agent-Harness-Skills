# 按需初始化验收

> 执行结束时加载，只校验用户选择的范围。

## 通用

- [ ] 已有文件未被无授权覆盖
- [ ] `AGENTS.md` 已存在或本次选择核心文档时，工具适配表记录实际客户端和入口
- [ ] `AGENTS.md` 不可用时，执行结果已报告适配状态，且未为登记状态创建核心文档
- [ ] 未选模块未生成源码、依赖、配置或强制规则
- [ ] 所有链接和相对路径可达

## 核心文档（选择时）

- [ ] `AGENTS.md` 章节结构完整且顺序正确：目录锚点、项目定位、当前入口、真实验证命令、协作原则、红线、（多人协作——仅多人协同模式）、踩坑教训、（Spec 工具——若安装）、P1/P2 索引、文档职责、Agent 工具适配、变更日志
- [ ] 目录锚点链接全部指向文内章节，无失效锚点
- [ ] 项目定位章节含协作模式标记（单人 / 多人协同），与项目识别阶段的确认结果一致
- [ ] decisions/ 目录含 `_INDEX.md` 索引表和 `001-v1-init-*.md` 首条决策；文件命名符合 `序号-版本-关键词.md`，索引行含版本、关键词、状态、相关模块；序号无重复且与版本号一一对应
- [ ] 多人协同模式：`.agents/<当前成员>/` 含 context.md 与 scratchpad.md 骨架；`.gitignore` 含 `.agents/`；AGENTS.md 项目定位列出成员名单，多人协作章节存在；决策文件含「作者」行且 `_INDEX.md` 含作者列
- [ ] 单人模式：无 `.agents/` 目录与多人协作章节
- [ ] AGENTS、decisions、排期职责不重叠；协作原则、红线与踩坑教训都在 `AGENTS.md` 内，无独立 soul / lessons 文件
- [ ] 存在旧体系 `.trae/rules/soul.md` / `lessons-learned.md` 时，已按迁移流程并入 `AGENTS.md` 并经授权删除，无残留引用
- [ ] 工具入口只索引公共事实
- [ ] 文档中的工具说明与实际选择一致

## BACKLOG / 排期清单（选择时）

- [ ] 只包含未完成项
- [ ] 闭环规则指向 decisions/（新建决策文件 + `_INDEX.md` 追加索引行）

## 路径成对钩子（选择时）

- [ ] `tools/path_align_hooks/` 含 `drift_lite` 与 `turn_align` 的 `.ps1` / `.sh` 与 README
- [ ] 独立运行 `drift_lite` 能输出含 `ok` 的 JSON
- [ ] 未在产物中写入某 Harness 专属 hooks 配置作为「标准答案」
- [ ] 宿主支持 hook 时：已按当前工具惯例注册 `turn_align`（或在执行结果中说明已跳过注册及原因）

## verify-matrix（选择时）

- [ ] `specs/verification/` 含 `matrix.yaml`、`run_verify.*`、`hooks/`
- [ ] `AGENTS.md`「Spec 工具」表 `verify-matrix` 为 yes
- [ ] `run_verify.ps1 -DryRun -Python python` 可执行

## drift-inventory（选择时）

- [ ] `specs/drift/` 含 `drift_inventory.py`、`language_profiles.yaml`、`run_drift.*`
- [ ] `AGENTS.md`「Spec 工具」表 `drift-inventory` 为 yes
- [ ] `run_drift.ps1 -Python python` 可执行（示例 pilot 以模板为准）
