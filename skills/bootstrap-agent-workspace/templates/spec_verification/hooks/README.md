# pre-commit hook 接线（本地沙盒）

> 仅示例，未写入 `skills/`。解释器由 Agent / 开发者通过 `$env:PYTHON` 或 `-Python` 指定。

## 三种接法

| 方式 | 适用 | 入口 |
|---|---|---|
| **pre-commit 框架** | 团队已用 [pre-commit](https://pre-commit.com/) | `.pre-commit-config.yaml.example` → 仓库根 |
| **Git 原生 hook** | 单人、无额外依赖 | `pre-commit.example` → `.git/hooks/pre-commit` |
| **手动** | 调试 / CI | `pre_commit_entry.ps1` 或 `run_verify.ps1 -PreCommit` |

## 1. pre-commit 框架（推荐混合仓库）

```powershell
# 仓库根
Copy-Item specs/verification/.pre-commit-config.yaml.example .pre-commit-config.yaml
pip install pre-commit   # 或 uv tool install pre-commit
pre-commit install

# 试跑（不提交）
pre-commit run verify-matrix --all-files
```

`entry` 指向 `hooks/pre_commit_entry.ps1`，内部再调 `run_verify.ps1 -PreCommit`。

## 2. Git 原生 hook

```bash
cp specs/verification/hooks/pre-commit.example .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
chmod +x specs/verification/hooks/pre_commit_entry.sh
```

```powershell
# Windows（若宿主直接跑 ps1 hook）
Copy-Item specs/verification/hooks/pre-commit.ps1.example .git/hooks/pre-commit
```

提交前设置解释器（可选）：

```bash
export PYTHON='uv run --no-project python'
```

## 3. 不装 hook，模拟 pre-commit

```powershell
# staged 命中矩阵 watch 才跑
powershell -NoProfile -File specs/verification/hooks/pre_commit_entry.ps1 -Python python

# 无 git stage 时用 -Paths（specs/ 被 ignore 时很有用）
powershell -NoProfile -File specs/verification/run_verify.ps1 -PreCommit -Paths skills/spec-writing/SKILL.md -Python python
```

## 行为

- **未命中** `matrix.yaml` 的 `watch`：exit 0，打印 `nothing to run (ok)`
- **命中且测试失败**：exit 非 0，阻止提交（git hook / pre-commit 默认）
- **与 path-align 无关**：path-align 在 Agent turn-end；本 hook 只在 `git commit` 前

## 非目标

- 不搜索 venv / 不猜解释器
- 不进本发布仓 CI
- 不复制到 `skills/bootstrap` 直到沙盒验收完成
