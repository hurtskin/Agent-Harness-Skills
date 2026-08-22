# v12 · 收编 spec-writing 为第三个发布 Skill（2026-08-21）

- **状态**：活跃
- **关键词**：spec-writing,新 Skill,收编,发布单元,README,适配声明,crawl 残留
- **相关模块**：spec-writing

- **关联文档**：`skills/spec-writing/SKILL.md`、`skills/spec-writing/README.md`、`README.md`（根）、`AGENTS.md`
- **变化程度**：新增发布单元——从用户本地 skills 目录（`~/.trae-cn/skills/spec-writing/`）复制 SKILL.md（name 与目录名一致，符合发布约定），删除其中的 crawl 项目专属"适配声明(本项目裁剪)"段（Scrapy/MongoDB/BM25 技术栈裁剪与 soul §3.1 引用对发布仓库是无效上下文）；按 task-handoff 模式新增 README（定位、核心能力、适用场景、触发方式、文档结构、核心流程、与 bootstrap-agent-workspace 的 Spec 层级约定关系）。规范本体（10 段结构、11 维度钉死、15 题自检、SPEC-001 示例）一字未改。
- **摘要**：spec-writing 成为仓库第三个 Skill；其 `specs/{领域}/{功能模块}/` 布局与 bootstrap-agent-workspace 写入 AGENTS.md 的 Spec 层级约定兼容，README 中已注明分工（前者管单份 spec 内容规范，后者管工作区结构）。
