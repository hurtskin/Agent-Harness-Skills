# path-align-hooks 模块

> 仅在用户选择「路径成对钩子」或套餐映射包含该模块时加载。

## 生成

1. 将 `templates/path_align_hooks/` 复制到项目 `tools/path_align_hooks/`（含 README 与 `*.ps1` / `*.sh`）。
2. 若本次同时选择核心工作区文档：在 `AGENTS.md` 协作原则中补一句路径成对约定（契约侧 ↔ 实现侧），真实验证命令可附独立运行 `drift_lite` 的示例；**不要**写入某 Harness 的专属 hook 配置样板。
3. 若当前 Agent Harness **支持**会话/轮次结束 hook：按该工具惯例，把 `turn_align`（Windows 用 `.ps1`，Unix 用 `.sh`）注册到「轮次结束」类事件，工作目录为仓库根。注册细节由执行 Agent 按当前工具自行完成——**本模块不提供分 Harness 适配清单**。
4. 若当前工具不支持 hook：只落地 `tools/path_align_hooks/`，在执行结果中说明「可手动跑 drift_lite；宿主无 hook 则跳过注册」。

已有 `tools/path_align_hooks/` 时默认升级缺失文件，不覆盖用户改过的脚本（除非用户明确授权覆盖）。

## 验证

```powershell
powershell -NoProfile -File tools/path_align_hooks/drift_lite.ps1
```

或：

```bash
bash tools/path_align_hooks/drift_lite.sh
```

期望：stdout 为 JSON，含 `ok` / `risk_code` / `actions` 等字段；无相关 dirty 时 `ok=true`。

可选：向 `turn_align` 喂入最小事件 JSON，确认能解析并不崩：

```powershell
'{ "status": "completed", "loop_count": 0 }' | powershell -NoProfile -File tools/path_align_hooks/turn_align.ps1
```

## 约束

- 模板与安装路径均无 Harness 专属目录名；禁止在本模块产物中写入某工具的 hooks 配置文件作为「标准答案」。
- 未选本模块：不复制脚本、不改 AGENTS、不注册任何 hook。
- 与 verify-matrix、drift-inventory 独立：本模块是 L0 路径成对，不替代 Correctness 或 inventory L1/L2。
