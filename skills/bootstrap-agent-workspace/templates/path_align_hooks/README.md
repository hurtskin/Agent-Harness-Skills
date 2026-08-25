# path-align hooks（模板）

轮次结束时的 **L0 路径成对** 诊断脚本：根据 git dirty 树判断契约侧（`specs/` / openapi / `*.schema.json`）与实现侧（`skills/` / `src/` / 常见源码后缀）是否同现，输出 JSON 报告与可选 nudge。

## 产物（复制到目标项目）

复制本目录全部脚本到项目：

```text
tools/path_align_hooks/
├── drift_lite.ps1 | drift_lite.sh
└── turn_align.ps1 | turn_align.sh
```

不要改脚本业务逻辑去迁就某个 Agent Harness；**hook 配置文件由执行 Agent 在 bootstrap 时按当前 Harness 提示生成并落地**（决策 v17）。本 Skill **不**维护各 Harness 的逐一适配说明。

## 脚本职责

| 脚本 | 输入 | 输出 |
|---|---|---|
| `drift_lite.*` | 可选 `--root` / `-RepoRoot`；可选 `--fail-on-risk` | stdout：配对报告 JSON；写 `last-drift.json` |
| `turn_align.*` | stdin：轮次结束事件 JSON（字段因宿主而异，尽力解析 `status` / `loop_count`） | stdout：无风险时 `{}`；有风险且允许 nudge 时见下 |

`turn_align` nudge 形状（宿主自行映射到自己的 follow-up / continue 字段）：

```json
{
  "nudge": true,
  "message": "…人类可读工单…",
  "actions": [{ "id": "A1", "instruction": "…" }]
}
```

关闭 nudge：环境变量 `PATH_ALIGN_NUDGE=0`。

## 独立运行

```powershell
powershell -NoProfile -File tools/path_align_hooks/drift_lite.ps1
powershell -NoProfile -File tools/path_align_hooks/drift_lite.ps1 -FailOnRisk
```

```bash
bash tools/path_align_hooks/drift_lite.sh
bash tools/path_align_hooks/drift_lite.sh --fail-on-risk
```

## 非目标

- 不做函数级 / 行为级 Correctness
- 不替代 drift-inventory（L1/L2）或 verify-matrix（Correctness）
- 不内置任何 Harness 专属配置文件
