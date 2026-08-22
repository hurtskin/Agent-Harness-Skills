# Sandbox spec excerpt — paired with inventory.yaml (not production).
version: "0.1.0"

## 3. 用户故事与验收场景 (可执行 Gherkin)

```gherkin
Scenario: 成功注册新账户
  Given 邮箱未被占用
  When 用户提交有效邮箱与密码
  Then 返回 201 且状态为 PENDING_VERIFICATION

Scenario: 已注册邮箱再次注册
  Given 邮箱已存在
  When 用户提交相同邮箱
  Then 返回 409 EMAIL_ALREADY_REGISTERED
```

## 第 5 部分附: Properties

| 性质 ID | 回链 | 量化式（oracle） | 自动化 |
|---|---|---|---|
| P-REG-01 | Gherkin 成功注册 | ∀ 新邮箱 ⇒ PENDING_VERIFICATION | PT-REG-101 |
| P-REG-02 | Gherkin 已注册 | ∀ 已占用 ⇒ 409 且不改写 | PT-REG-102 |
| P-REG-03 | 状态机 | ∀ 迁移 ⇒ 仅允许表内 | PT-REG-103 |
