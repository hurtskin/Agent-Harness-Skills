# verify-matrix 模板（bootstrap 安装到 `specs/verification/`）

由 bootstrap `verify-matrix` 模块复制到消费者项目。用法见 `skills/spec-writing/tools/verify-matrix.md`。

## 安装后路径

```text
specs/verification/
├── matrix.yaml
├── run_verify.ps1 | run_verify.sh
├── hooks/                    # pre-commit 入口
└── pilot/                    # 可删或替换为项目测试
```

解释器：`-Python` 或 `$env:PYTHON`；脚本不搜索 venv。

## 快速命令

```powershell
powershell -NoProfile -File specs/verification/run_verify.ps1 -Python python -PreCommit
```
