# Spec Writing

一个约束 AI 与人按统一骨架编写软件 Spec 的 Skill。它提供 10 段强制结构模板、Properties 行为不变量（推荐）、零自由发挥约束清单和落地前 15+2 题自检，目标是让 Spec 达到「拿走文档直接复刻代码」的精度，消除实施阶段的自创空间。

与自由格式的需求文档相比，`spec-writing` 更强调机器可读、字段级钉死和实施前门禁，适合行为、接口或数据模型必须严格对齐代码的项目。

## 核心能力

- 强制 10 段结构：元数据、术语表、验收场景（Gherkin）、API 契约（OpenAPI 3.1）、数据模型（JSON Schema + 映射表）、业务规则与状态机、错误码字典、需求覆盖矩阵、非功能需求、假设约束与变更日志
- Properties（推荐附节）：关键业务行为写成 `P-*` ∀ 量化式，覆盖矩阵允许 `PT-*`；供 PBT / Correctness 作 oracle（工具语言不绑定，不强制全仓 CI）
- Correctness 变更门：写 `P-*` 与跑 `PT-*` 分开；仅 dirty/diff 命中相关实现或性质正文时才必须跑对应 PT；path-align 不等于 Correctness
- 零自由发挥铁律：字段名、类型、必填性、默认值、校验器、枚举值、工厂方法签名、错误码、状态转换、测试用例 ID、CI 门禁规则共 11 个维度必须全部钉死在 spec 正文
- 落地前 15+2 题自检：严格对齐 5 题、细节遗漏 5 题、自由发挥空间 5 题、Properties 2 题；任一题 ❌ 不允许进入实施阶段（无关键行为可 N/A）
- 模糊词黑名单：待定、TODO、视情况、类似 X、简化版等词汇出现在 spec 正文即视为未完成
- 实施阶段 8 类禁止行为清单：自创命名、防御性代码、未来扩展点、改默认值、改测试编号、改门禁规则、docstring 字面量、未声明的二次发挥
- 完整示例：用户邮箱注册与验证（SPEC-001）贯穿 10 段 + Properties 推荐范例，展示可逐字复刻的精度标准

## 适用场景

满足以下任一情况时可以使用：

- 新功能需要立项，要写 spec 或补全 spec 三件套（spec.md / tasks.md / checklist.md）
- 已有 spec 需要评审，检查结构完整性或排查实施自由发挥空间
- 团队协作中代码与文档频繁漂移，需要文档先行 + CI 门禁约束
- 希望接口、数据模型、错误码、状态机有机器可读的唯一事实源
- AI 编码时经常"自由发挥"，需要把实施约束全部前置钉死
- 需要为关键行为补 Properties / 属性测试回链

以下情况通常不需要使用：

- 一次性脚本或原型，没有长期维护需求
- 纯文档类改动，不涉及行为、接口或数据模型
- 已有更轻量的任务描述约定且运转良好

## 触发方式

可以直接向 Agent 表达意图，例如：

```text
使用 spec-writing 为支付模块立 spec。
```

```text
按 spec-writing 规范补全 spec 三件套。
```

```text
用 spec-writing 的 15+2 题自检评审这份 spec 是否留有自由发挥空间。
```

## 文档结构

Spec 文档与源代码同仓存放，路径约定 `specs/{领域}/{功能模块}/`：

```text
specs/auth/registration/
├── spec.md            # 主规范文档（10 段结构 + 推荐 Properties）
├── properties.md      # 可选：行为不变量单独文件
├── features/          # 可执行 Gherkin 验收场景
├── openapi.yaml       # API 契约（唯一事实源）
├── user.schema.json   # 数据模型 JSON Schema
└── user_states.yaml   # 状态机定义
```

## 核心流程

1. 按触发意图加载 10 段骨架，逐段落 spec（术语表 → 验收场景 → 契约 → 数据模型 → 规则 → Properties → 错误码 → 覆盖矩阵 → 非功能 → 假设约束）
2. 对照 11 维度钉死清单逐项确认，实施阶段必须的每个细节都写入 spec 正文
3. 执行落地前 15+2 题自检并记录到 spec 同目录 `self-check.md`
4. 全部 ✅ 才允许进入实施；实施中发现遗漏 → 暂停 → 回补 spec → 重检 → 继续写代码
5. 改到某 `P-*` 所约束的实现（或改性质/oracle）→ 按变更门只跑命中的 `PT-*`，再继续

## 与其他 Skill 的关系

`spec-writing` 定义的 `specs/{领域}/{功能模块}/` 三件套布局，与 `bootstrap-agent-workspace` 初始化工作区时写入 AGENTS.md 的 Spec 层级约定（`specs/<模块>/<功能>/` 每节点 spec.md + tasks.md + checklist.md）兼容；后者负责工作区结构，前者负责单份 spec 的内容规范。

## 进一步阅读

- `SKILL.md`：完整的 10 段结构模板、Properties 附节、Correctness 变更门、11 维度钉死清单、15+2 题自检和 SPEC-001 完整示例
