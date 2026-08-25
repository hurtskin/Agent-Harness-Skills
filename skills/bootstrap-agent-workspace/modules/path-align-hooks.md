# path-align-hooks 模块

> 仅在用户选择「路径成对钩子」或套餐映射包含该模块时加载。

## 生成

1. 将 `templates/path_align_hooks/` 复制到项目 `tools/path_align_hooks/`（含 README 与 `*.ps1` / `*.sh`）。
2. 若本次同时选择核心工作区文档：在 `AGENTS.md` 协作原则中补一句路径成对约定（契约侧 ↔ 实现侧），真实验证命令可附独立运行 `drift_lite` 的示例；**不要**在 AGENTS.md 写入某 Harness 的专属 hook 配置样板。
3. **宿主 hook 接线（决策 v17）**：复用 SKILL §1.2 已识别的 Harness 类型，**Agent 按当前 Harness 的官方 hook 提示生成对应宿主配置文件**（如 `.cursor/hooks.json` / `.claude/settings.json` / 其他惯例路径），把 `turn_align`（Windows 用 `.ps1`，Unix 用 `.sh`）注册到「轮次结束」类事件，工作目录为仓库根。
   - 不维护分 Harness 适配清单；不写「标准答案」样板；用时由 Agent 现场按 Harness 提示生成。
   - **未识别 Harness 走必问用户**，不得默认跳过接线，也不得默认套 Trae。
4. 当前工具不支持 hook：落地 `tools/path_align_hooks/` 与宿主配置后，在执行结果中说明「宿主未启用会话结束 hook，`turn_align` 仅作手动调用」。

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

- 模板脚本与安装路径均无 Harness 专属目录名；**禁止**把任一工具的 hook 配置文件作为「标准答案样板」维护在本仓（决策 v17）。接线由 Agent 现场按 Harness 提示生成。
- 未选本模块：不复制脚本、不改 AGENTS、不注册任何 hook。
- 与 verify-matrix、drift-inventory 独立：本模块是 L0 路径成对，不替代 Correctness 或 inventory L1/L2。
