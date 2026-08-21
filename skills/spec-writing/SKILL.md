---
name: "spec-writing"
description: "Spec 文档编写规范(10 段强制结构 + Properties 行为不变量推荐 + 完整示例 + 零自由发挥 + 落地前 15+2 题自检)。Invoke when 立 spec / 写 spec / 评审 spec / 补 spec 三件套(spec.md / tasks.md / checklist.md) / 检查 spec 完整性 / 排查自由发挥空间 / 补性质 Properties。按 10 段结构落 spec,关键推荐 Properties(∀ oracle) 供 PBT/Correctness;落地前必跑 15 题自检 + Properties 2 题。"
---

# Spec 文档编写规范与生成规则

> **来源**：2026-07-03 从 `.trae/rules/spec创建规则.md` 迁出,改为 skill。
> **触发**：用户提到「立 spec」「写 spec」「评审 spec」「补 spec 三件套」「spec 完整性」时,先调本 skill 拿 10 段骨架。

---

## 1. 核心原则

- **文档即代码**:Spec 文档与源代码存放在同一仓库,遵循相同的版本控制和评审流程。
- **唯一事实来源**:Spec 是所有相关角色(产品、开发、测试)的唯一真相源。代码只是其实现。
- **机器可读优先**:能用结构化语言(YAML、JSON、Gherkin、OpenAPI)描述的,绝不只依赖自然语言。纯文本仅作补充说明。
- **可执行可验证**:文档中的每一个行为、规则、场景都必须能够转化为自动化测试或验证脚本。
- **不可变绑定**:代码变更必须文档先行;文档变更也必须同步触发代码修改,CI 流水线强制执行这一绑定。
- **零自由发挥空间 `no_implementation_latitude`** ⚠️ **HIGHEST PRINCIPLE**:spec 必须达到「拿走 spec 直接复刻代码」的精度。字段名 / 类型 / 必填性 / 默认值 / 校验器 / 枚举值 / 工厂方法签名 / 错误码 / 状态转换 / 测试用例 ID / CI 门禁规则——11 个维度必须**全部钉死在 spec 正文**,实施阶段不允许自创任何一条。违反 = spec 未完成,不允许进入实施阶段(详见 §6 / §7)。

---

## 2. 文件组织与命名规范

- **存放路径**:所有 Spec 文档必须放在项目根目录下的 `/specs/{领域}/{功能模块}/` 目录中。
  - 示例:`/specs/auth/registration/`
- **文件命名**:
  - 主规范文档:`spec.md` (或 `spec.yaml`,若整个规范用结构化语言表达)
  - 可执行场景:`features/{功能名}.feature` (Gherkin)
  - API 契约:`openapi.yaml`
  - 数据模型:`{实体名}.schema.json`
  - 状态机:`{实体名}_states.yaml`
  - 行为不变量(推荐):`properties.md`（或写入 `spec.md` 的 Properties 小节）
- **代码关联**:在 `spec.md` 的元数据部分必须明确关联的代码路径,例如:
  - 代码包路径:`src/auth/registration/`
  - API 路由文件:`src/auth/routes/registration.ts`
  - 数据库迁移文件:`migrations/20260703_create_users.sql`

---

## 3. 文档结构模板

所有 Spec 文档必须严格包含以下 10 个部分,不可缺失任何一部分。

### 第 0 部分:文档头与元数据

- **规范标题**:`SPEC-{编号}: {特性名称}`
- **状态**:`提议 | 已批准 | 开发中 | 已实现 | 已废弃`
- **版本**:严格遵循语义化版本,如 `v1.0.0`,与 Git Tag 对应。
- **负责人**:`PO: @someone | TL: @someone | QA: @someone`
- **关联代码路径**:至少列出代码包路径、API 路由文件、数据库迁移文件。
- **最后修改时间**:由 Git 记录,文档中可标注 `(见 Git 提交记录)`。
- **CI 门禁规则**:简述关键绑定规则,如"本文件修改时必须同时修改对应代码路径"。

### 第 1 部分:术语表与统一语言

- 以表格形式定义所有领域专有名词,必须包含以下列:
  - `术语` `英文名` `类型`(聚合根/值对象/枚举/服务) `定义` `代码映射` `数据库映射` `示例`
- **强制要求**:所有代码中的枚举、实体、列名必须来自本表格。
- **一致性保障**:表中枚举值将用于代码生成和静态检查。

**示例片段:**

| 术语 | 英文名 | 类型 | 定义 | 代码映射 | 数据库映射 | 示例 |
|------|--------|------|------|----------|------------|------|
| 用户 | User | 聚合根 | 已注册的账户主体 | `class User` | `users` 表 | `User { id, email, status }` |
| 邮箱 | Email | 值对象 | 用户唯一标识 | `Email` 类型 | `email VARCHAR(254)` | `user@example.com` |
| 用户状态 | UserStatus | 枚举 | 账户生命周期状态 | `enum UserStatus` | `status VARCHAR(20)` | `PENDING_VERIFICATION`, `ACTIVE` |

### 第 2 部分:用户故事与验收场景(可执行规范)

- 必须使用 **Gherkin 语法**(Given-When-Then)编写。
- 场景文件单独存放于 `features/` 目录,主文档中仅列出关键场景概要,或直接嵌入核心特性文件内容。
- **场景必须可直接运行**,如使用 Cucumber/SpecFlow 框架执行。
- 必须覆盖:正常路径、异常路径、边界情况、权限校验。
- 每个场景都应关联到具体的 API 接口。

**示例:**

```gherkin
功能: 用户邮箱注册
  场景: 成功注册新账户
    假设 邮箱 "newuser@example.com" 未被注册
    当 我向 POST /api/v1/auth/register 发送请求
      """
      { "email": "newuser@example.com", "password": "SecureP@ss1" }
      """
    那么 响应状态码应该是 201
    且 用户状态应为 "PENDING_VERIFICATION"
    且 系统应发送一封验证邮件到 "newuser@example.com"
```

### 第 3 部分:API 接口与契约(OpenAPI 3.1 同源)

- 必须提供完整的 **OpenAPI 3.1** 规格文件(或 gRPC proto / GraphQL SDL)。
- 文件存放于同目录下 `openapi.yaml`,并在主文档中引用。
- 规格文件需包含:
  - 每个端点精确的路径、方法、请求体、响应体、状态码、错误响应。
  - 所有 Schema 定义(请求体、响应体、枚举、错误结构)。
  - 统一的错误响应格式(如 `error_code`, `message`, `details`)。
  - 至少一个完整的请求/响应示例。
- **一致性保障**:从此文件生成服务端接口骨架和客户端 SDK;通过契约测试工具(Dredd)验证真实 API 与文档完全一致。

**示例片段(OpenAPI YAML):**

```yaml
paths:
  /api/v1/auth/register:
    post:
      summary: 邮箱注册
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterRequest'
      responses:
        '201':
          description: 注册成功
          headers:
            X-Spec-Version:
              schema: { type: string, example: v1.0.0 }
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RegistrationResponse'
        '409':
          $ref: '#/components/responses/Conflict'
```

### 第 4 部分:数据模型与校验规则

- 对每个核心实体提供 **JSON Schema** 定义,文件命名 `{实体名}.schema.json`。
- 在主文档中建立 **映射关系表**,将业务字段、JSON Schema、数据库列、代码属性一一对应。
- 字段必须包含:类型、格式、长度、正则、枚举值、默认值、是否必填。
- **一致性保障**:运行时使用 JSON Schema 校验请求与响应;通过数据库 Schema 同步工具(如 Prisma)保证与 JSON Schema 一致。

**示例:映射表**

| 业务字段 | JSON Schema 属性 | 数据库列 (PostgreSQL) | 代码属性 |
|----------|------------------|------------------------|----------|
| 用户邮箱 | email | email VARCHAR(254) UNIQUE | email: string |
| 用户状态 | status { enum: [...] } | status VARCHAR(20) | status: UserStatus |

### 第 5 部分:业务规则与状态流转

- 状态流转必须用 **状态机图** 或 **YAML 定义**,描述实体所有可能的状态和转换事件。
- 复杂业务规则使用 **决策表**(条件-动作表)表达,消除歧义。
- 每一条规则必须能映射到具体的测试用例。
- **一致性保障**:状态机定义直接导入代码生成状态对象;决策表通过属性测试(Property-based Testing)覆盖。

**示例:状态机 YAML**

```yaml
stateMachine: UserLifecycle
initial: PENDING_VERIFICATION
states:
  PENDING_VERIFICATION:
    on:
      VERIFY: ACTIVE
      EXPIRE: DISABLED
  ACTIVE:
    on:
      DISABLE: DISABLED
```

**示例:决策表(密码强度)**

| 条件:长度 >=8 | 条件:包含字母 | 条件:包含数字 | 动作 |
|----------------|----------------|----------------|------|
| 是             | 是             | 是             | 接受 |
| 是             | 否             | 是             | 拒绝 (缺少字母) |
| 否             | 任意           | 任意           | 拒绝 |

### 第 5 部分附: Properties 行为不变量（推荐 / Correctness）

> **推荐升格（非第 11 段强制）:** 10 段骨架不变。凡含**关键业务行为**（注册、状态迁移、冲突、决策表）的 Spec,**应**增加 Properties,把 SHALL 写成可执行 ∀ 公式,供 Property-Based Testing 作 oracle。纯叙事 NFR / 假设段可不写性质。  
> **沙箱说明:** 发布仓可不跟踪 `specs/`；性质示例与装订片段见下文「推荐范例」。消费者项目按自身栈实现 `PT-*`，勿默认嵌入全仓 PBT。

- 每条性质必须有:`性质 ID`（`P-{域}-{序号}`）`回链`（Gherkin / 状态机 / 错误码 / REQ-ID）`量化式` `生成器约定` `自动化 ID`（`PT-…`,可暂「未自动化」但须给期限）。
- 量化式须可判定真假:优先 `∀ … ⇒ …`;禁止「体验良好」等不可观测结论。
- 覆盖矩阵（§7）**允许**增加 `P-*` / `PT-*` 行;类型可标「属性测试」。
- **一致性保障:** 性质是行为契约;字段级零自由发挥（§4）仍要钉死。两者叠加:结构可复刻 + 行为可证伪。
- **语言不绑定:** PT 用被测实现同语言的属性测试工具即可;本仓 pilot 用 Python 仅为示范。

**最小表格模板:**

| 性质 ID | 回链 | 量化式（oracle） | 生成器 | 自动化 |
|---------|------|------------------|--------|--------|
| P-XXX-01 | REQ-… / Gherkin… | `∀ … ⇒ …` | `valid_…` | PT-XXX-001 |

#### Correctness 变更门（何时必须跑 PT）

分清两步：**写 P-\***（立/改 Spec）与 **跑 PT-\***（验证实现）。path-align / drift-lite 只做路径成对，**从不**自动等于 Correctness。

| 动作 | 必须何时做 | 不做的情况 |
|---|---|---|
| **写 `P-*`** | Spec 含写入 / 状态迁移 / 冲突·幂等 / 决策表等关键行为（落地前 Q16） | 纯叙事 NFR、假设段、仅改措辞 → Q16 = N/A + 理由 |
| **跑对应 `PT-*`** | 本轮 dirty/diff **命中**该 `P-*` 所约束的实现，或改了该 `P-*` / 生成器 / oracle 正文；或覆盖矩阵已标「已自动化」且上述文件进入合并 diff | 仅 path-align 报警；只改 `AGENTS.md` / 排期 / 排版；该 Spec 对 Properties 合法 N/A |

执行约定：

1. 只跑**命中的** `PT-*`，禁止「每轮 stop 全仓扫一遍 PBT」。
2. 合并/CI：由项目自行决定是否把已声明「已自动化」的 `PT-*` 进门禁；Skill **不**强制全仓绑定某一 PBT 库。
3. 未自动化的 `PT-*` 须在矩阵留期限；逾期未补 = Spec/门禁未完成（与 Q17 一致）。

### 第 6 部分:错误处理与日志规范

- 定义 **错误码字典**,表格列:`错误码` `HTTP 状态码` `触发条件` `日志级别`。
- 所有 API 错误响应必须遵循统一格式(参照 OpenAPI 中的 Error schema)。
- 规定关键操作的日志等级和必须记录的字段(如 `requestId`, `userId`, `action`)。
- **一致性保障**:错误码字典直接生成为常量类,业务代码只能引用这些常量;静态检查扫描任何硬编码错误码或异常。

**示例:**

| 错误码 | HTTP 状态码 | 触发条件 | 日志级别 |
|--------|-------------|----------|----------|
| `EMAIL_ALREADY_REGISTERED` | 409 | 注册时邮箱已存在 | INFO |
| `VALIDATION_ERROR` | 422 | 请求参数不满足 Schema | WARN |
| `INTERNAL_ERROR` | 500 | 未预期的服务器错误 | ERROR |

### 第 7 部分:测试用例与需求覆盖矩阵

- 建立 **需求追溯矩阵**,表格列:`需求来源` `需求 ID` `类型` `测试用例 ID` `自动化状态`。
- 需求来源必须是本文档中的具体章节(如 Gherkin 场景、API 端点、状态机转换、业务规则、**Properties**)。
- **自动化状态** 只有 `已自动化` 或 `未自动化`(未自动化必须给出理由和期限)。
- 允许行:`TC-*`(验收)、`CT-*`(契约)、`UT-*`(单元)、`PT-*` / `P-*`(属性 / 性质)。
- **一致性保障**:通过代码注解(如 `@spec("SPEC-001", "REQ-XX")`)自动生成该矩阵,并作为 CI 覆盖率门禁。

**示例:**

| 需求来源 | 需求 ID | 类型 | 测试用例 ID | 自动化状态 |
|----------|---------|------|-------------|------------|
| Gherkin: 成功注册新账户 | REQ-REG-01 | 验收测试 | TC-REG-001 | 已自动化 |
| API: POST /register 201 | REQ-REG-04 | 契约测试 | CT-REG-001 | 已自动化 |
| 状态机: PENDING -> ACTIVE | REQ-REG-06 | 单元测试 | UT-REG-003 | 已自动化 |

### 第 8 部分:非功能性需求

- 必须量化指标,禁止使用"快速"、"稳定"等模糊词。
- 典型分类:性能、安全、可用性、可靠性、可观测性。
- 每项需求必须配套 **验证方法**(如压测脚本、安全扫描、集成测试断言)。
- **一致性保障**:验证方法必须自动化,放入 CI 对应阶段(性能测试、安全扫描)。

**示例:**

| 类别 | 具体要求 | 验证方法 |
|------|----------|----------|
| 性能 | `POST /register` P95 < 200ms (500并发) | k6 脚本在 CI 负载测试阶段运行 |
| 安全 | 密码不能明文记录日志 | 集成测试中检查日志输出 |
| 限流 | 同一 IP 每分钟最多 10 次注册 | 连续发送 11 次请求,断言第 11 次返回 429 |

### 第 9 部分:假设、约束与变更日志

- **假设**:列出所有外部依赖和前提条件(如"数据库为 PostgreSQL 15"、"邮件服务可用")。
- **约束**:技术选型限制、不可变规则(如"密码必须 bcrypt 散列"、"API 路径前缀 `/api/v1/`")。
- **变更日志**:严格按 Git 提交记录自动生成,表格列:`日期` `版本` `变更说明` `关联 Commit`。**禁止手写变更日志**。

**示例:**

| 日期 | 版本 | 变更说明 | 关联 Commit |
|------|------|----------|-------------|
| 2026-07-03 | v1.0.0 | 初始版本,邮箱注册与验证 | `a1b2c3d` |

---

## 4. 全局生成规则

1. **文档语言**:主体使用中文,术语、代码、技术标识使用英文。
2. **完整性检查**:生成 Spec 后,必须自我检查 10 个部分是否全部涵盖,不能遗漏。
3. **示例驱动**:每一部分至少包含一个具体示例(参考下文给出的示例片段)。
4. **可执行性声明**:在文档头部注明"本规范中的 Gherkin 场景可执行,OpenAPI 文件可用于代码生成,状态机可导入代码;关键行为宜附 Properties 供 PBT",提醒使用者这是可运行制品。
5. **与示例风格保持一致**:当遇到新领域时,类比示例"用户邮箱注册与验证"的详细程度和编排方式生成对应内容。
6. **落地前自检门禁 `pre_implementation_gate`** ⚠️ **MANDATORY**:spec 三件套(spec.md / tasks.md / checklist.md)写完后,**必须**执行 §6「落地前自检」全部 15 题,**外加** §6.4 Properties 2 题(共 17)。任一题答 ❌ → 回修补 spec → 重检 → 全部 ✅ 才允许进入实施阶段。**禁止**「先动手再补自检」「自检不通过先开着口子后续补」。无关键业务行为的纯文档 Spec,Properties 2 题可答「N/A(无关键行为)」并写明理由。
7. **零自由发挥铁律 `zero_improvisation`** ⚠️ **MANDATORY**:实施阶段(写代码 / 写测试 / 改字段)发现 spec 漏了某条约束 → **暂停** → 回 §5 补 spec → §6 重检 → 再继续写代码。**禁止**「我先这样写,spec 后补」「这个字段 spec 没写我就按习惯来」「这点小事不用进 spec」。

---

## 5. 实施零自由发挥约束 (No-Free-Land Gate)

> 本节是 §1「零自由发挥空间」最高原则的具体落地清单。spec 落地前必须**逐维度**确认 11 个维度全部钉死;实施阶段必须**逐条**确认 8 类禁止行为未触发。

### 5.1 spec 必须钉死的 11 维度清单

> **下表「spec 哪段写」列中的 §N 指 spec 文档的段落编号**(即 §3 文档结构模板定义的 10 段,§0 元数据 / §1 术语表 / §2 Gherkin / §3 API / §4 数据模型 / §5 业务规则 / §6 错误处理 / §7 覆盖矩阵 / §8 非功能 / §9 假设约束),**不是本 skill 的章节编号**。

| # | 维度 | spec 哪段写 | 实施如何对齐 | 违反即红线 |
|---|------|-------------|--------------|------------|
| 1 | 字段名 | §4 数据模型 + 术语表 | 代码字段名逐字一致(含大小写 / 下划线 / 复数) | 自创字段名 / 改命名风格 |
| 2 | 字段类型 | §4 数据模型映射表 | Python type hint / TS 类型逐字一致 | 自创类型(`str` 改 `Decimal` 等) |
| 3 | 必填性 | §4 数据模型(required 列) | `Field(...)` vs `Field(default=...)` 一致 | 必填改可选 / 可选改必填 |
| 4 | 默认值 | §4 数据模型(default 列) | `Field(default=X)` 逐字一致 | 自创默认值 / 改 sentinel |
| 5 | 校验器 | §4 / §5 业务规则 | validator 函数名 + 触发条件逐字一致 | 自创校验器 / 加未声明校验 |
| 6 | 枚举值 | §1 术语表 + §4 | enum 成员逐字一致(顺序 / 大小写) | 加 / 删 / 改枚举成员 |
| 7 | 工厂方法签名 | §5 业务规则 / §4 | 方法名 / 参数 / 返回类型逐字一致 | 自创工厂 / 改参数顺序 / 加默认参数 |
| 8 | 错误码 | §6 错误处理 | 错误码字符串逐字一致 | 自创错误码 / 改 HTTP 状态码 |
| 9 | 状态转换 | §5 状态机 YAML | state→event→state 三元组逐字一致 | 自创转换 / 删转换 / 改事件名 |
| 10 | 测试用例 ID | §7 覆盖矩阵 | TC-XX-NNN 编号逐字一致 | 自创编号 / 改编号格式 / 漏编号 |
| 11 | CI 门禁规则 | §0 元数据 + §8 非功能 | grep 表达式 / 阈值 / 脚本逐字一致 | 自创 grep / 改阈值 / 加未声明检查 |

### 5.2 实施阶段禁止行为清单(8 类自创动作)

| # | 禁止行为 | 反例 | 正确动作 |
|---|----------|------|----------|
| 1 | 自创命名 | spec 写 `throttle_seconds`,代码用 `delay_seconds` | 回 §4 改 spec → 按改后字段名写代码 |
| 2 | 加防御性代码 | spec 未声明 `try/except`,代码自行加 fallback | 回 §5 / §6 补异常处理约束 → 按补后写 |
| 3 | 加未来扩展点 | spec 写 6 字段,代码加 `metadata: dict = {}` 留扩展 | 删扩展字段;如确需,回 §4 改 spec |
| 4 | 改默认值 | spec 写 `default=UTC now`,代码用 `default=None` | 回 §4 改 spec 默认值 → 按改后写 |
| 5 | 改测试矩阵编号 | spec 写 TC-sub03-T-01,代码用 TC-001 | 回 §7 改 spec 编号 → 按改后写 |
| 6 | 改 grep 红线 | spec 写 `grep -E '"etsy"|"amazon"'`,代码用 `grep etsy` | 回 §8 改 spec grep 表达式 → 按改后写 |
| 7 | docstring 写字面量例子 | docstring 写 `"""取 value 字符串 ("etsy" / "amazon")"""` | docstring 只描述概念,不举字面量 |
| 8 | spec 未声明的二次发挥 | spec 没写 `__str__`,代码加 `__str__ = str` | 回 §5 补方法签名约束 → 按补后写 |

### 5.3 模糊词黑名单(spec 正文出现即视为未完成)

以下词汇在 spec.md / tasks.md / checklist.md **正文**中出现 = spec 未完成,**不允许**进入实施阶段:

| 黑名单词 | 为什么禁 | 应该写成什么 |
|----------|----------|--------------|
| 待定 / TODO / TBD | 没钉死 | 具体值或显式「待用户决策」+ 阻塞标记 |
| 可酌情 / 视情况 / 按需 | 实施可自由发挥 | 明确触发条件 + 默认行为 |
| 暂定 / 后续补 / 后续再定 | 漂移入口 | 当次写完;如不能写完,标阻塞等用户决策 |
| 类似 X / 参考 X / 同 X | 实施可自由解读 | 完整复刻 X 的字段 / 约束 / 示例 |
| 一般 / 通常 / 大概 / 约 | 不可量化 | 精确数值 / 精确范围 |
| 等等 / 诸如此类 / 等 | 实施可扩展 | 完整穷举清单 |
| 简单实现 / 简化版 / 最小版 | 实施可降级 | 完整实现规格 |

**例外**:`假设` 段 / `约束` 段 / `变更日志` 段允许出现时间性表述(如「v2 评估」),但仍需钉死 v1 边界。

---

## 6. spec 落地前自检 (Mandatory Pre-Implementation Self-Audit)

> 本节是 §4 第 6 条「落地前自检门禁」的具体清单。spec 三件套写完 → 实施阶段开始前**必答 15 题 + Properties 2 题(共 17)**;任一题 ❌ → 回修补 spec → 重检;全部 ✅(或 Properties 合法 N/A) → 才允许动代码。**禁止**「先动手再补自检」「自检不通过先开着口子」。
>
> **下表「失败处理」列中的「§N」指 spec 文档的段落编号**(§0-§9,见 §3 文档结构模板),**不是本 skill 的章节编号**;「§5」特指本 skill 的 §5「实施零自由发挥约束」。

### 6.1 严格对齐自检(5 题)

| # | 自检问题 | ✅ 通过标准 | ❌ 失败处理 |
|---|----------|-------------|-------------|
| 1 | 代码中每个字段名是否都能在 spec §4 找到一一对应出处? | 100% 字段名逐字一致 | 回 §4 改 spec 或改代码 → 重检 |
| 2 | 每个函数签名(参数 / 返回类型 / 默认值)是否与 spec §5 一致? | 100% 签名逐字一致 | 回 §5 改 spec 或改代码 → 重检 |
| 3 | 每个枚举值是否与 spec §1 术语表 + §4 完全一致(含顺序)? | 成员 + 顺序逐字一致 | 回 §1 / §4 改 → 重检 |
| 4 | 每个测试用例 ID 是否与 spec §7 覆盖矩阵逐字一致? | `TC-`/`CT-`/`UT-`/`PT-` 编号 100% 一致 | 回 §7 改 → 重检 |
| 5 | 每个默认值 / 校验器 / 错误码是否与 spec 逐字一致? | 100% 一致 | 回 §4 / §5 / §6 改 → 重检 |

### 6.2 细节遗漏自检(5 题)

| # | 自检问题 | ✅ 通过标准 | ❌ 失败处理 |
|---|----------|-------------|-------------|
| 6 | spec.md 10 段结构是否齐全(§0-§9)? | 10 段全部存在,无空段 | 补齐缺失段 → 重检 |
| 7 | 每段是否至少 1 个具体示例(非占位)? | 每段示例可执行 / 可复刻 | 补示例 → 重检 |
| 8 | CI 门禁规则是否可执行(脚本 / 阈值 / grep 全给出)? | 可直接复制到 CI yaml 跑 | 补可执行细节 → 重检 |
| 9 | 假设 / 约束段是否写明所有外部依赖 + 不可变规则? | 无遗漏外部依赖 | 补假设 / 约束 → 重检 |
| 10 | 变更日志是否记录本次 spec 版本 / 日期 / 一句话摘要? | 表格 + 日期 + 版本 + 摘要 | 补变更日志 → 重检 |

### 6.3 自由发挥空间自检(5 题)

| # | 自检问题 | ✅ 通过标准 | ❌ 失败处理 |
|---|----------|-------------|-------------|
| 11 | spec 正文是否含 §5.3 黑名单模糊词? | 0 次出现 | 删模糊词,改精确表述 → 重检 |
| 12 | 是否存在「可选字段」未明示触发条件? | 每个 Optional 都有「何时为 None」说明 | 补触发条件 → 重检 |
| 13 | 是否存在未给出验证方法的非功能需求? | 每条非功能需求都有可执行验证 | 补验证方法 → 重检 |
| 14 | 是否存在「类比 X」「参考 X」未给精确约束? | 类比项都展开成完整字段清单 | 展开类比 → 重检 |
| 15 | 是否存在 spec 未声明但实施必须做的动作(如导入 / 序列化 / 比较)? | 实施所需动作 100% 在 spec 中 | 回 §5 补声明 → 重检 |

### 6.4 Properties 门禁(2 题，小步升格)

| # | 自检问题 | ✅ 通过标准 | ❌ 失败处理 |
|---|----------|-------------|-------------|
| 16 | 关键业务行为(写/状态迁移/冲突/决策表)是否都有 `P-*` 性质 ID + ∀ 量化式(或合法 N/A)? | 每条关键行为有 P-id 与可判定 oracle;无关键行为则 N/A+理由 | 按「第 5 部分附」补 Properties → 重检 |
| 17 | 每条 `P-*` 是否回链 REQ/Gherkin/状态机/错误码,且覆盖矩阵有对应 `PT-*`(或未自动化期限)?后续变更是否按「Correctness 变更门」只跑命中 PT? | 回链完整;矩阵有 PT 行或未自动化+期限;变更门约定已理解 | 补回链 / 矩阵行 / 重读变更门 → 重检 |

### 6.5 自检执行模板(粘贴到 spec 同目录 `self-check.md`)

```markdown
# Spec 落地前自检(15+2) - {spec 编号}

> 执行时间: {YYYY-MM-DD HH:MM}
> 执行人: {agent / user}

## 6.1 严格对齐(5 题)
- [ ] Q1 字段名: ✅/❌ {证据}
- [ ] Q2 函数签名: ✅/❌ {证据}
- [ ] Q3 枚举值: ✅/❌ {证据}
- [ ] Q4 测试用例 ID: ✅/❌ {证据}
- [ ] Q5 默认值/校验器/错误码: ✅/❌ {证据}

## 6.2 细节遗漏(5 题)
- [ ] Q6 10 段结构: ✅/❌ {缺失段}
- [ ] Q7 每段示例: ✅/❌ {缺失示例段}
- [ ] Q8 CI 门禁可执行: ✅/❌ {不可执行项}
- [ ] Q9 假设约束: ✅/❌ {遗漏项}
- [ ] Q10 变更日志: ✅/❌ {缺失字段}

## 6.3 自由发挥空间(5 题)
- [ ] Q11 黑名单模糊词: ✅/❌ {命中词 + 位置}
- [ ] Q12 Optional 触发条件: ✅/❌ {未明示字段}
- [ ] Q13 非功能需求验证方法: ✅/❌ {未给方法项}
- [ ] Q14 类比精确约束: ✅/❌ {未展开类比}
- [ ] Q15 实施必需动作声明: ✅/❌ {未声明动作}

## 6.4 Properties(2 题)
- [ ] Q16 关键行为有 P-* / 或 N/A: ✅/❌/N/A {证据或理由}
- [ ] Q17 P-* 回链 + PT-* 矩阵行: ✅/❌/N/A {证据}

## 结论
- 总计 ✅: {N}/17（N/A 计为通过并附理由）
- 总计 ❌: {N}/17
- 进入实施阶段: 是 / 否(否则回修补 spec → 重检)
```

---

## 7. 完整示例参考

> 以下示例不仅展示 10 段结构,还展示如何达到 §5「零自由发挥」标准——每个字段、每个错误码、每个测试用例 ID 都钉死到可逐字复刻。新领域写 spec 时应类比此示例的精度,而非仅类比结构。

下面给你一个完整的 Spec 文档示例,主题是 **"用户邮箱注册与验证"** 。这份文档严格按照前文所述的 10 个部分编写,并附 **Properties 推荐范例**;每一部分都会连带说明它 **如何与代码保持高度一致**。

# SPEC-001: 用户邮箱注册与验证

> **规范状态:** 已实现
> **版本:** v1.0.0
> **负责人:** PO: @amy | TL: @ben | QA: @cathy
> **代码包路径:** `src/auth/registration/`
> **API 路由文件:** `src/auth/routes/registration.ts`
> **数据库迁移文件:** `migrations/20260703_create_users.sql`
> **最后修改:** 2026-07-03 (Git 提交记录为准)

---

## 1. 规范元数据与治理 (同仓同源)

- **文件路径:** `/specs/auth/registration/spec.md`
- **关联代码路径:** `/src/auth/registration/`
- **CI 门禁规则:**
  - 本文件被修改时,对应的 `src/auth/registration/` 或 API 测试文件必须同时被修改。
  - 当 API 版本号变更时,CI 会检查代码中返回的 `X-Spec-Version` 响应头是否与本文档的 `info.version` 一致。

---

## 2. 术语表与统一语言

| 术语 | 英文名 | 类型 | 定义 | 代码映射 | 数据库映射 | 示例 |
|------|--------|------|------|----------|------------|------|
| 用户 | User | 聚合根 | 已注册的账户主体 | `class User` | `users` 表 | `User { id, email, status }` |
| 邮箱 | Email | 值对象 | 用户唯一标识,需满足正则校验 | `Email` 类型 | `email VARCHAR(254) UNIQUE` | `user@example.com` |
| 用户状态 | UserStatus | 枚举 | 账户生命周期状态 | `enum UserStatus` | `status VARCHAR(20)` | `PENDING_VERIFICATION`, `ACTIVE`, `DISABLED` |
| 验证令牌 | VerificationToken | 值对象 | 用于邮箱验证的 JWT 令牌,24 小时有效 | `class VerificationToken` | 不持久化,无列 | `eyJhbGci...` |
| 密码 | Password | 值对象 | 至少 8 位,含数字和字母的散列值 | `Password` 值对象 | `password_hash VARCHAR(255)` | `(bcrypt hash)` |

**一致性保障:**
- `UserStatus` 枚举直接由本表格生成 TypeScript 类型和 Prisma 枚举。
- 任何代码中出现的用户状态字符串,必须通过 `UserStatus` 枚举引用,CI 中运行 `grep` 检查硬编码状态字符串的脚本。

---

## 3. 用户故事与验收场景 (可执行 Gherkin)

以下场景文件位于 `/specs/auth/registration/features/registration.feature`,由 Cucumber 框架直接执行。

```gherkin
功能: 用户邮箱注册
  作为一名网站访客
  我想要使用我的邮箱注册一个新账户
  以便能登录并使用网站功能

  背景:
    假设 系统处于正常运行状态

  场景: 成功注册新账户
    假设 邮箱 "newuser@example.com" 未被注册
    当 我向 POST /api/v1/auth/register 发送以下请求
      """
      {
        "email": "newuser@example.com",
        "password": "SecureP@ss1"
      }
      """
    那么 响应状态码应该是 201
    且 响应体应包含一个用户 ID
    且 用户状态应为 "PENDING_VERIFICATION"
    且 系统应发送一封验证邮件到 "newuser@example.com"
    且 响应头 X-Spec-Version 应为 "v1.0.0"

  场景: 使用已注册的邮箱注册
    假设 邮箱 "duplicate@example.com" 已被注册且状态为 "ACTIVE"
    当 我向 POST /api/v1/auth/register 发送以下请求
      """
      {
        "email": "duplicate@example.com",
        "password": "AnotherP@ss1"
      }
      """
    那么 响应状态码应该是 409
    且 错误码为 "EMAIL_ALREADY_REGISTERED"

  场景大纲: 使用无效格式的邮箱或密码
    当 我向 POST /api/v1/auth/register 发送以下请求
      """
      {
        "email": "<邮箱>",
        "password": "<密码>"
      }
      """
    那么 响应状态码应该是 422
    且 错误码为 "VALIDATION_ERROR"
    且 响应体 details 应包含字段 "<字段>"

    例子:
      | 邮箱              | 密码         | 字段    |
      | invalid           | SecureP@ss1  | email   |
      | user@example      | SecureP@ss1  | email   |
      | good@example.com  | 123         | password |
```

**一致性保障:**
- 本文件即为自动化测试套件。所有场景必须在 CI 中 100% 通过。
- 测试步骤中的 `发送请求` 直接调用真实 API,`系统应发送一封验证邮件` 这一步会检查邮件发送服务是否被调用(通过 mock 验证)。

---

## 4. API 接口与契约 (OpenAPI 3.1 同源)

文件路径:`/specs/auth/registration/openapi.yaml`。该文件是接口的 **唯一事实来源**。

```yaml
openapi: 3.1.0
info:
  title: 用户注册服务
  version: v1.0.0
paths:
  /api/v1/auth/register:
    post:
      summary: 邮箱注册
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterRequest'
      responses:
        '201':
          description: 注册成功,等待邮箱验证
          headers:
            X-Spec-Version:
              schema:
                type: string
                example: v1.0.0
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RegistrationResponse'
        '409':
          $ref: '#/components/responses/Conflict'
        '422':
          $ref: '#/components/responses/ValidationError'
  /api/v1/auth/verify-email:
    post:
      summary: 邮箱验证
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [token]
              properties:
                token:
                  type: string
                  description: 注册后通过邮件收到的验证令牌
      responses:
        '200':
          description: 验证成功,账户激活
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: "邮箱验证成功,账户已激活"
        '410':
          $ref: '#/components/responses/Gone'

components:
  schemas:
    RegisterRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
          maxLength: 254
          description: 用户邮箱
        password:
          type: string
          minLength: 8
          maxLength: 128
          pattern: '^(?=.*[a-zA-Z])(?=.*\d).+$'
          description: 密码,至少8位,包含字母和数字
      example:
        email: "newuser@example.com"
        password: "SecureP@ss1"

    RegistrationResponse:
      type: object
      properties:
        user_id:
          type: string
          format: uuid
        status:
          $ref: '#/components/schemas/UserStatus'
      example:
        user_id: "550e8400-e29b-41d4-a716-446655440000"
        status: "PENDING_VERIFICATION"

    UserStatus:
      type: string
      enum: [PENDING_VERIFICATION, ACTIVE, DISABLED]

  responses:
    Conflict:
      description: 资源冲突
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error_code: "EMAIL_ALREADY_REGISTERED"
            message: "该邮箱已被注册"

    ValidationError:
      description: 请求参数校验失败
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationErrorBody'

    Gone:
      description: 资源已过期
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/Error'
          example:
            error_code: "VERIFICATION_TOKEN_EXPIRED"
            message: "验证令牌已过期,请重新注册"

    Error:
      type: object
      required: [error_code, message]
      properties:
        error_code:
          type: string
        message:
          type: string

    ValidationErrorBody:
      allOf:
        - $ref: '#/components/schemas/Error'
        - type: object
          properties:
            details:
              type: array
              items:
                type: object
                properties:
                  field: { type: string }
                  reason: { type: string }
```

**一致性保障:**
- **服务端代码生成:** 使用 OpenAPI Generator 生成 Express 路由接口和 DTO 类,开发人员只能实现业务逻辑。
- **契约测试:** CI 中运行 Dredd,用真实请求比对 API 返回是否与该文档完全一致,包括状态码、错误体结构。
- **消费者驱动契约:** 前端团队提供 Pact 文件,验证注册 API 满足他们期望的字段,存放于 `/pacts/registration-web.json`,CI 中运行 Pact 验证。
- **差异检查:** 任何 PR 修改本文件时,运行 `openapi-diff` 与主干比较,如有 Breaking Change 则必须人工审批。

---

## 5. 数据模型与校验规则 (JSON Schema + 数据库映射)

用户实体 JSON Schema 定义:`/specs/auth/registration/user.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "User",
  "type": "object",
  "properties": {
    "id": { "type": "string", "format": "uuid" },
    "email": { "type": "string", "format": "email", "maxLength": 254 },
    "password_hash": { "type": "string" },
    "status": { "enum": ["PENDING_VERIFICATION", "ACTIVE", "DISABLED"] },
    "created_at": { "type": "string", "format": "date-time" },
    "verified_at": { "type": ["string", "null"], "format": "date-time" }
  },
  "required": ["id", "email", "password_hash", "status", "created_at"]
}
```

数据库 Schema (Prisma) 直接从上述文档生成,文件 `prisma/schema.prisma` 中相关部分由工具保证同步:

```prisma
enum UserStatus {
  PENDING_VERIFICATION
  ACTIVE
  DISABLED
}

model User {
  id            String     @id @default(uuid())
  email         String     @unique @db.VarChar(254)
  passwordHash  String     @map("password_hash")
  status        UserStatus @default(PENDING_VERIFICATION)
  createdAt     DateTime   @default(now()) @map("created_at")
  verifiedAt    DateTime?  @map("verified_at")
  @@map("users")
}
```

**一致性保障:**
- **运行时校验:** 在 API Controller 中,使用 `ajv` 编译该 JSON Schema 作为请求体二次校验(即使已经生成类型,但防御性检查仍有必要)。
- **快照测试:** 单元测试中序列化一个新创建的用户对象,断言其 JSON 结构与 `user.schema.json` 中的 `example` 一致。
- **数据库迁移自动生成:** Prisma 的文件由 `prisma generate` 从 Schema 生成,而 Schema 的变更规则是:必须与 JSON Schema 同步修改。

---

## 6. 业务规则与状态流转

**用户状态机 (YAML):** `/specs/auth/registration/user_states.yaml`

```yaml
stateMachine: UserLifecycle
initial: PENDING_VERIFICATION
states:
  PENDING_VERIFICATION:
    on:
      VERIFY: ACTIVE
      EXPIRE: DISABLED   # 注册后超过24小时未验证
  ACTIVE:
    on:
      DISABLE: DISABLED
  DISABLED:
    type: final
```

**决策表:密码强度规则**

| 条件:密码长度 | 条件:包含字母 | 条件:包含数字 | 动作:是否接受 |
|----------------|----------------|----------------|----------------|
| < 8            | -              | -              | 否             |
| >= 8           | 是             | 是             | 是             |
| >= 8           | 否             | 是             | 否 (缺少字母)  |
| >= 8           | 是             | 否             | 否 (缺少数字)  |

**一致性保障:**
- **状态机代码生成:** 使用 `xstate` 导入 YAML,实际业务逻辑的状态转换必须经过该状态机对象,非法转换会抛出错误。
- **基于属性的测试:** 根据密码决策表编写属性测试,随机生成符合/不符合规则的字符串,断言 `isValidPassword()` 结果与决策表一致。
- **集成测试状态流转:** 模拟调用邮箱验证接口,断言数据库状态从 `PENDING_VERIFICATION` 变为 `ACTIVE`,并检查状态机是否允许。

### Properties（推荐范例 / Correctness）

> **状态:** 推荐范例（小步升格）。**不是**第 11 段强制结构;有关键业务行为的 Spec 应按「第 5 部分附」书写同类小节。  
> **文件建议:** `/specs/auth/registration/properties.md`（或本文件子节）。发布 Skill 仓可不入库 `specs/`。  
> **生成器约定:** `valid_email` = 满足 JSON Schema `format:email` 且 `maxLength≤254`；`valid_password` = 满足 `minLength≥8` 且 pattern「至少一字母一数字」；`UserStatus` / `Event` 枚举取自本 Spec 正文。

| 性质 ID | 回链 | 量化式（oracle） | 建议生成器 | 自动化 |
|---------|------|------------------|------------|--------|
| P-REG-01 | Gherkin 成功注册；REQ-REG-01 | 见下 | `valid_email` × `valid_password` + `assume(not email_exists)` | PT-REG-101 |
| P-REG-02 | Gherkin 已注册邮箱；错误码表；REQ-REG-02 | 见下 | `valid_email` × `valid_password` × `UserStatus` | PT-REG-102 |
| P-REG-03 | 状态机 YAML；REQ-REG-06 | 见下 | `UserStatus` × `Event` | PT-REG-103 |

**P-REG-01 — 新邮箱注册必进入待验证态**

```text
∀ email ∈ valid_email, ∀ password ∈ valid_password,
当 email 未被占用时：
  r = register(email, password)
  ⇒ r.http == 201
  ∧ r.body.user_id 存在且为 UUID
  ∧ r.user.status == PENDING_VERIFICATION
  ∧ r.user.email == email
```

**P-REG-02 — 已占用邮箱注册必冲突且不改写用户**

```text
∀ email ∈ valid_email, ∀ password_old, password_new ∈ valid_password,
∀ status ∈ {PENDING_VERIFICATION, ACTIVE, DISABLED},
当 email 已以 status 存在时：
  before = snapshot(email)
  r = register(email, password_new)
  ⇒ r.http == 409
  ∧ r.error_code == "EMAIL_ALREADY_REGISTERED"
  ∧ snapshot(email) == before
```

**P-REG-03 — 状态机闭包（仅允许表内迁移）**

```text
Allowed = {
  (PENDING_VERIFICATION, VERIFY) → ACTIVE,
  (PENDING_VERIFICATION, EXPIRE) → DISABLED,
  (ACTIVE, DISABLE) → DISABLED
}

∀ status ∈ UserStatus, ∀ event ∈ {VERIFY, EXPIRE, DISABLE}:
  若 (status, event) ∈ Allowed
    ⇒ apply(status, event) == Allowed[(status, event)]
  否则
    ⇒ apply(status, event) 抛出领域错误（不得静默保持或迁到表外状态）
```

**装订示例（Hypothesis；工具可选，oracle 必填）:**

```python
# 示意：消费者项目用同语言属性测试工具装订；非发布仓 CI 门禁。
@given(valid_email(), valid_password())
def test_P_REG_01(email, password, fresh_db):
    assume(not email_exists(email))
    r = register(email, password)
    assert r.status_code == 201
    assert r.user.status == "PENDING_VERIFICATION"

ALLOWED = {
    ("PENDING_VERIFICATION", "VERIFY"): "ACTIVE",
    ("PENDING_VERIFICATION", "EXPIRE"): "DISABLED",
    ("ACTIVE", "DISABLE"): "DISABLED",
}

@given(st.sampled_from(USER_STATUSES), st.sampled_from(EVENTS))
def test_P_REG_03(status, event):
    if (status, event) in ALLOWED:
        assert apply_transition(status, event) == ALLOWED[(status, event)]
    else:
        with pytest.raises(DomainError):
            apply_transition(status, event)
```

**范例要点:**
- Gherkin 单例邮箱 → 性质需补 **输入空间**（生成器）与 **assume**。
- 冲突场景只写了 ACTIVE → 性质要求 **∀ UserStatus**，比原场景更强。
- 状态机 YAML → `Allowed` 表即唯一迁移 oracle；非法边必须有失败语义（本范例钉死为抛错）。

---

## 7. 错误处理与日志规范

**错误码字典:**

| 错误码 | HTTP 状态码 | 触发条件 | 日志级别 |
|--------|-------------|----------|----------|
| `VALIDATION_ERROR` | 422 | 请求参数不满足 JSON Schema | WARN |
| `EMAIL_ALREADY_REGISTERED` | 409 | 注册时邮箱已存在 | INFO |
| `VERIFICATION_TOKEN_EXPIRED` | 410 | JWT 过期或被篡改 | WARN |
| `VERIFICATION_TOKEN_INVALID` | 400 | 令牌格式错误 | WARN |
| `INTERNAL_ERROR` | 500 | 未预期的服务器错误 | ERROR |

**一致性保障:**
- **统一异常类:** 所有抛出的业务异常必须使用 `BusinessError` 类,其构造参数 `errorCode` 必须为上述字典中的值。在 CI 中,使用静态分析扫描 `throw new BusinessError('SOME_STRING')`,若字符串不在字典中则编译失败。
- **响应体验证:** 契约测试中针对每个错误场景,严格比对 `error_code` 和状态码,不允许返回自定义消息或 500 堆栈。

---

## 8. 测试用例与需求覆盖矩阵 (自动生成)

> 此矩阵由测试运行时注解自动生成,不手工维护。

| 需求来源 | 需求 ID | 类型 | 测试用例 ID | 自动化状态 |
|----------|---------|------|-------------|------------|
| Gherkin: 成功注册新账户 | REQ-REG-01 | 验收测试 | TC-REG-001 | 已自动化 |
| Gherkin: 已注册邮箱 | REQ-REG-02 | 验收测试 | TC-REG-002 | 已自动化 |
| Gherkin: 无效格式邮箱或密码 | REQ-REG-03 | 验收测试 | TC-REG-003-005 | 已自动化 |
| API: POST /register 201 | REQ-REG-04 | 契约测试 | CT-REG-001 | 已自动化 |
| API: POST /register 409 | REQ-REG-05 | 契约测试 | CT-REG-002 | 已自动化 |
| 状态机: PENDING -> ACTIVE | REQ-REG-06 | 单元测试 | UT-REG-003 | 已自动化 |
| 业务规则: 密码强度 | REQ-REG-07 | 属性测试 | PT-REG-001 | 已自动化 |
| Properties: P-REG-01 新邮箱→PENDING | REQ-REG-01 | 属性测试 | PT-REG-101 | 示例行（消费者项目自行自动化；非本仓 CI） |
| Properties: P-REG-02 冲突不改写 | REQ-REG-02 | 属性测试 | PT-REG-102 | 示例行（消费者项目自行自动化；非本仓 CI） |
| Properties: P-REG-03 状态机闭包 | REQ-REG-06 | 属性测试 | PT-REG-103 | 示例行（消费者项目自行自动化；非本仓 CI） |

**一致性保障:**
- **覆盖率门禁:** CI 中运行需求覆盖率报告,所有 `REQ-REG-*` 必须有对应的自动化测试通过,否则不允许合并。
- **自动关联:** 在测试代码中使用 `@spec("SPEC-001", "REQ-REG-01")` 装饰器,脚本扫描测试代码生成上述矩阵。
- **Properties:** `P-REG-*` / `PT-REG-101..103` 为推荐范例；关键行为须过自检 Q16/Q17。Hypothesis 为可选工具,不以全仓 CI 强制依赖为门槛。

---

## 9. 非功能性需求

| 类别 | 具体要求 | 验证方法 |
|------|----------|----------|
| 性能 | `POST /register` 接口 P95 < 200ms (500并发) | k6 脚本在 CI 负载测试阶段运行,不达标阻断 |
| 安全 | 密码输入不能明文记录到日志 | OWASP ZAP 动态扫描 + 测试用例断言日志中不含密码 |
| 安全 | 注册接口必须限流:同一 IP 每分钟最多 10 次 | 集成测试中连续发送 11 次请求,断言第 11 次返回 429 |
| 可靠性 | 数据库写失败时,不能发送验证邮件 | 测试中模拟数据库异常,检查邮件服务调用次数为 0 |
| 可观测性 | 注册成功与失败均需打印结构化日志,含 `requestId` | 集成测试后解析日志,检查必需字段 |

**一致性保障:**
- 上述验证方法均编写为自动化测试/脚本,放入 CI 对应阶段。
- 性能基线文件 `benchmarks/register_threshold.json` 与 Spec 同步更新。

---

## 10. 假设、约束与变更日志

**假设:**
- 系统运行在 Node.js 20 LTS 环境。
- 数据库为 PostgreSQL 15,支持 `uuid-ossp` 扩展。
- 邮件发送服务 `email-service` 可用,调用其 `sendVerificationEmail` 接口,成功率 99.9%。

**约束:**
- 密码必须 bcrypt 散列存储,轮数为 12。
- JWT 验证令牌使用 `RS256` 算法,过期时间 24 小时。
- 所有 API 路径前缀 `/api/v1/` 不得改变。

**变更日志 (由 semantic-release 基于 Git 提交自动生成):**

| 日期 | 版本 | 变更说明 | 关联 Commit |
|------|------|----------|-------------|
| 2026-07-03 | v1.0.0 | 初始版本,包含邮箱注册和验证 | `a1b2c3d` |
