# 拼多多拉图工具 — vibecoding 全过程复盘

> **本文是 `bootstrap-agent-workspace` 工作区体系的真实使用案例**：一个从「拉取开源项目」到「交付单文件 exe」的完整 vibecoding 项目，全程使用本仓库的 skill 组合（bootstrap-agent-workspace 初始化工作区 + spec-writing 规范 + decisions 决策目录 + lessons 教训沉淀）驱动。

> **复盘依据**：《拉取开源项目.md》《管理页面新增分页和下载功能.md》《打包benchmark-collector为exe.md》三份对话实录 + 《决策日志.md》（v0.1 ~ v1.15 共 25 条决策）。
> **复盘目的**：还原一个真实 vibecoding 项目从「拉取开源项目」到「交付单文件 exe」的完整过程，提炼协作模式、踩坑与决策链。

---

## 一、项目概览

**业务背景**：用户是打印照片商家，买家在拼多多客服对话里发待打印的图片，手动逐张下载太慢，希望有一个按订单自动下载图片的工具。

**最终形态**：双击即用的单文件 exe（约 85.7MB，免装 Node），自动拉起带调试端口的 Chrome/星愿浏览器，本地 Web 管理界面（http://localhost:8300）支持扫描建台账、单订单精确下载、一键批量下载、分页、订单号搜索、打开目录、30 天过期自动清理。

**技术路线**：以 npm 开源包 benchmark-collector（Playwright 采集工具）为底座二次开发，CDP 复用真实浏览器登录态，拦截拼多多 `getMessages` 接口提取买家图片（`type=1 && direction=false`），按订单号归档，三重去重（URL / MD5 / 感知哈希），Node SEA 打包。

**vibecoding 数据一览**：

| 维度 | 数据 |
|---|---|
| 对话轮次（用户消息） | 约 53 轮，横跨 3 个会话文档 |
| 决策日志 | 25 条（v0.1 ~ v1.15） |
| Spec 体系 | 36 个文件（项目级 + 4 大模块 + 7 个 subspec，各含 spec/tasks/checklist 三件套） |
| 单元测试 | 从 16 条增长到 30 条，全绿 |
| 核心脚本 | `pdd-image-downloader.js`（采集下载核心）+ `pdd-order-manager.js`（管理系统） |
| 沉淀经验教训 | lessons-learned 2 条（Windows detached COM 抑制、Node SEA require.resolve 受限） |
| 交付产物 | `dist-exe/pdd-order-manager.exe`（Node SEA 单文件） |

---

## 二、全过程时间线

整个过程可划分为五个大阶段、十六个小步。下面按时间顺序还原每一步的用户输入、AI 响应与关键决策。

### 阶段 A：获取底座与可行性验证

#### A1. 拉取开源项目

用户丢来一个 npm 链接，要求拉取 benchmark-collector。npm 页面被安全验证拦截后，AI 改走 registry API 拿元数据，发现该包没有公开 Git 仓库、source map 不含 `sourcesContent`，**无法还原 TS 源码**，只能基于编译后的 dist 做 JS 二次开发。这个客观限制被如实告知，并记入决策日志 v0.2。

用户随后要求把项目集成进工作目录先测试效果。AI 复制文件、`npm install`（postinstall 自动下载 Chromium），并写了 `test-run.js` + 本地 `demo.html` 做无头冒烟测试，9 步采集产物（纯净截图/SoM 标注图/元素 JSON/DOM 快照/AX 树）全部齐全，证明底座可用。

#### A2. 需求澄清：按订单拉图并不存在

用户问「它现在是按照什么来获取的图片？订单吗」。AI 检索源码后给出结论：**项目没有任何订单维度的图片逻辑**，现有能力只是对话消息图片提取（DOM 扫描 + API 拦截两种模式）。随后用户才完整说出真实场景（打印照片商家、买家发图、手动下载慢），AI 调研了市面上的 RPA 工具和浏览器插件，确认**没有直接对口的开源项目**，但 benchmark-collector 已具备四块关键能力中的三块：CDP 登录态复用、拼多多历史会话遍历、API 图片提取、带登录态下载。二次开发路线成立。

这一步的价值在于：vibecoding 不是一上来就写代码，而是先弄清「用户要什么」和「底座有什么」，中间的差距才是要开发的部分。

#### A3. 真实环境验证（关键一步）

用户说「我们先验证一下真实的情况」。AI 写了轻量验证脚本 verify-pdd.js，只采前 2 个账号，目标是看清 `getMessages` 返回的数据结构。这一步遭遇了本项目第一个环境坑：**用户机器上没有 Google Chrome，只有星愿浏览器（Twinkstar）**，AI 搜索磁盘定位到 `F:\星愿\Twinkstar Browser\twinkstar.exe`，用独立数据目录 + `--remote-debugging-port=9222` 拉起调试窗口，用户登录后验证跑通。

验证产出了一条最重要的数据契约（决策日志 v0.3）：

| 字段 | 含义 | 对产品的意义 |
|---|---|---|
| `type === 1` | 图片消息 | 判定是不是图 |
| `direction === false` | 买家发送 | 判定是不是买家发的图 |
| `content` | 图片 URL（type=1 时） | 下载来源 |
| 文本消息中的「订单编号:xxx」 | 订单号藏在文本里 | 需正则提取，**无独立订单字段** |

另外验证时一个头像 URL 下载失败（`avatar3.pddpic.com` 无 CORS 头被浏览器 fetch 拦截），AI 确认这是验证脚本扫描过宽所致，正式工具只下 `type=1` 对话图不受影响，且明确了「优先 CDP/带 Referer 方式下载」的策略。

### 阶段 B：工程化基建

#### B1. 工作区初始化（bootstrap-agent-workspace）

用户主动要求初始化项目规范。AI 按技能流程生成五文档体系：AGENTS.md（导航入口）、soul.md（行为红线）、决策日志、排期清单、lessons-learned。原套餐包含 changelog-rag 决策检索（需 HuggingFace 嵌入模型），因模型缺失、用户判断「项目挺小，不需要 RAG」而整体移除（决策日志 v0.4）。这个决定让项目保持了零 Python 依赖的轻量形态。

#### B2. 产品规则确认

AI 在开发前用选项把模糊点逐条问清，用户给出全部规则：**只下买家发的图、按订单号命名目录、近 30 天、有图无订单号（未下单）不下载跳过、默认输出 output 目录**。这些规则后来成为 spec 的骨架，全程未再动摇。

#### B3. Spec 体系重构（用户纠偏）

AI 最初把整个项目写成一个大 spec，用户立刻指出问题：「这么多的东西一个 spec 完成？我以后需要更改的需求怎么办」，要求建立**项目级 → 大模块 → subspec** 的层级结构。AI 重构出 24 个文件的 spec 体系（session / collector / image-downloader 三大模块 + 4 个 subspec），并在项目级 spec 里定死需求变更流程：新需求到达 → 判定所属模块 → 新增/更新 subspec → 文档先行 → 确认 → 实施。这是本项目 vibecoding 的一次关键用户纠偏，后续所有功能（包括整个管理系统）都受益于这套结构。

### 阶段 C：核心下载工具开发

#### C1. 主体实现（决策日志 v0.6）

按 session → collector → image-downloader 顺序实现 `pdd-image-downloader.js`：CLI 参数解析、CDP 连接（失败退出码 1）、近 30 天时间选择、`getMessages` 拦截（按 msgId 去重）、账号列表与消息翻页、订单号正则提取、买家图判定、URL 去重 + 3 次重试、订单目录归档、manifest.json + summary.json。配套 node:test 单元测试（无新依赖）。

实施中发现 `getMessages` 消息对象不含 `uid`，按纪律回写进 order-archiving subspec（buyerUid 按昵称匹配 convUsers，否则 null），体现了「实现反哺文档」的闭环。

#### C2. 小规模真实验证与三个待办（v0.7）

带真实登录态跑 `--max-accounts 8 --max-msg-pages 2`，过程中连环踩坑：

- **终端 node 输出完全不可见**：`node` 命令被解析成 PowerShell 的 `node.ps1` shim，退出码和 stdout 捕获均不可靠。AI 定位真实 node.exe（`F:\java\nodejs\node.exe`）后改用「输出重定向到文件再读」的方式调试，这个环境缺陷贯穿了整个项目（后续测试一律用 execFileSync 写报告文件）。
- **页面复用失败**：复用用户已打开的 `mms.pinduoduo.com/home` 首页时 SPA 不渲染客服搜索界面，改为新建独立页面。
- **时间选择失败**：默认近 7 天被当成目标范围，根因是选择器时序不稳。修复为 readonly 输入框精确定位 → 等快捷面板弹出 → 点近 30 天 → 校验日期范围 27~31 天。

修复后成功下载 2 张买家图（`chat-img.pddugc.com/chat-pic-mall-user-v1/` 路径证明是买家图），同时登记三个待办进排期清单：#001 单测 2 项失败、#002 扩展名与真实格式不符、#003 部分会话未提取到订单号。

#### C3. 三个待办的闭环（v0.8、v0.9）

**#003（无订单号）** 的处理最能体现 vibecoding 的诊断文化：AI 没有直接改代码，而是先写诊断脚本 dump 会话原始响应，发现 `s***` 会话是「发图 → 图坏了 → 商家退款」的完整链路，**数据源本身就没有订单号**——不是代码 bug，是未下单/退款场景的天然属性。拿着这个证据问用户，得到产品规则裁定：「有图无订单 = 未下单，不下载直接跳过」。随后按文档先行把 spec 从「未匹配目录归档」改为 `NO_ORDER` 错误码跳过，再改代码，重跑验证。

**#002（扩展名）**：下载的 `.jpeg` 文件头实为 WebP/BMP。新增 `detectImageExt()` 按文件头 magic bytes 判定真实格式（JPEG/PNG/GIF/WebP/BMP），回退 URL 匹配。真实环境 25 账号验证：账号「少\*\*\*」33 张图 URL 后缀全是 `.jpeg/.png`，文件头全是 `BM`，全部正确存为 `.bmp`。

#### C4. 去重的两次演进（v1.0、v1.1）

用户发现三张图内容相同质疑重复下载。AI 算 MD5 证实其中两张字节级相同但 URL 不同（买家 7-22 和 8-01 两次发送，平台分配了不同 URL）——**URL 去重无法识别内容重复**。用户确认做内容去重后，实现订单内 MD5 去重，manifest 增加 `duplicates` 记录。

紧接着用户又反馈「每张图片基本都重复了一次」。AI 复查发现这批重复 **MD5 全部不同**——是买家重新上传同一批图产生的字节不同、视觉相同的文件。这引出了第二层去重：感知哈希。选型上先试 sharp（用户确认引入依赖），实测 **sharp 不支持 BMP 解码**而本项目图片恰以 BMP 为主，换 jimp（纯 JS 支持 BMP）实现 dHash 感知哈希，验证 5 对视觉重复全部识别为汉明距离 0。

这一阶段还连环修复了四个稳定性问题（v1.1）：

| 问题 | 根因 | 修复 |
|---|---|---|
| 运行后商家界面自动关闭 | `cleanup()` 无条件关闭复用页面 | CDP 模式不关闭任何页面 |
| 采集完进程不退出 | CDP 连接保持事件循环存活 | `run()` 结尾显式 `process.exit(0)` |
| 时间选择偶发失败 | 复用页面旧状态 + 固定等待不足 | 一律 goto 刷新 + 轮询等待元素出现 |
| 主脚本文件意外丢失 | 非 agent 删除的意外事件 | 按会话完整编辑历史重建，24/24 单测通过 |

最终验证：31 张唯一图 + 18 张重复跳过（md5_dup 13 + phash_dup 5）+ 0 失败，页面保留，进程正常退出。其中被视觉去重识别的 `d47a3a93` 正是用户最初怀疑的那张图——用户的直觉是对的，只是 MD5 识别不了。

#### C5. Spec 闭环（v1.2）

用户问「下一个 spec 是什么」，AI 如实回答：功能 spec 已全部实现完毕，剩下的是**文档滞后于代码**。随后把项目级 spec 从 v0.1.0 升到 v0.2.0（术语「未匹配订单」→「未下单会话」、错误码 `UNMATCHED_ORDER`→`NO_ORDER`、补三重去重/页面生命周期等全局规则），全层 tasks/checklist 勾选闭环。

### 阶段 D：从脚本到管理系统

#### D1. 管理系统立项与 spec 覆盖（v1.3）

用户提出升级需求：「当前只是一个一次性脚本，我要变成一个可持续用的软件，需要一个管理系统，自动获取订单然后有状态显示……点击爬取的按钮会精确去爬取这个订单的图片」。

AI 先起草 management 模块 spec，被用户指出**需求牵动多个既有模块却只写了一个新 spec**。AI 补齐完整覆盖：新增 management 大模块（order-ledger / scan-and-fetch / web-ui 三个 subspec 共 12 文件），同时增量更新 collector（扫描模式）、image-downloader（单订单精确下载 fetchOrder）、session（长驻服务模式）三个既有模块 spec。这次「多 spec 覆盖」的教训被固化成惯例。

实现上先重构 downloader 暴露 `scanMode`（只收集不下载）和 `fetchOrder`（按台账 URL 精确下载），把 `process.exit` 改为抛错以支持服务模式，再实现 `pdd-order-manager.js`：台账 JSON 原子持久化（tmp+rename、损坏自动备份重建）、状态机 `PENDING→DOWNLOADING→DONE/FAILED`、Node 内置 http 零新依赖 Web 服务（仅监听 127.0.0.1:8300）、任务互斥、前端 2 秒轮询。

开发中的连环修复：`probeCdpPort` 未导出致 health 500、TASK_BUSY 应回 409 却 500、POST /api/scan 阻塞等待任务完成违反 spec 的「立即返回 202」。

#### D2. 真实环境端到端验证（v1.4）

启动服务 → API/页面正常 → 触发单订单重新下载 → 29 秒完成 → 状态 DONE → 31 张唯一图落盘，全链路验证通过。

#### D3. 三个体验问题的修复（v1.5）

用户反馈「扫描点击后没反应」。AI 诊断发现任务已跑 172 秒无进展，根因是**全量扫描太慢（默认遍历 5000 账号、每账号最多翻 20 页消息）且扫描结束才写台账、前端期间不刷新**——不是按钮坏了，是没有任何反馈。修复为每个账号处理完实时写入台账 + 前端任务期间刷新表格 + 显示进度。

用户接着一次提出三件事：停止扫描、只扫新订单、下载报错 `(index):1 Uncaught SyntaxError: Unexpected end of input`。前两项 straightforward（`POST /api/task/cancel` + 每账号检查取消标志；台账已有订单号构建 Set 跳过 + 跳过消息翻页）。下载报错的根因很典型：**内联 `onclick="doFetch("...")"` 里 JSON.stringify 产生的双引号与 HTML 属性双引号冲突**，属性被截断成 `onclick="doFetch("`，点击时解析残缺脚本报错，任务从未启动过。修复用事件委托 + `data-order-no` 属性彻底消除引号冲突。

#### D4. 并行 Agent 协调

更新 spec 时发现文件里出现了 AI 记忆中不存在的「台账分页/一键下载」需求。用户解释是**另一个 Agent 正在做**。两个 Agent 改同一批 spec 文件已发生覆盖冲突（本 Agent 已实现的「实时落盘/停止扫描/事件委托」描述被对方重写丢失）。处理方式：只补回自己的功能描述、完整保留对方内容、在 tasks/checklist 里标注分页与一键下载归另一 Agent 不勾选，并提示对方「只追加不重写」。

### 阶段 E：管理界面完善与交付

#### E1. 分页 + 一键下载（v1.6）

用户：「给管理页面新增一个分页功能20个分页，然后再增加一个一键下载功能」。实现前端 `PAGE_SIZE=20` 分页器（页码越界自动收敛、轮询保持当前页）+ `POST /api/batch` 批量下载（batchTargets 选 PENDING+FAILED 订单逐单复用精确下载、零目标短路不连 CDP、可停止、完成回传结果摘要）。单测 29 条通过。此阶段再次确认环境缺陷：终端连 `process.exit(3)` 都显示退出码 0，测试验证改用 node 内 execFileSync 写报告文件。

#### E2. 停止按钮无反应（v1.7）

用户：「点击暂停没反应」。根因黑色幽默：`doStop()` 开头的 `if (busy) return;` 本意防并发，但**任务运行中 busy 恰好为 true，停止按钮永远被自己拦截**。修复为独立 `stopping` 防重入标志——「停止是控制已有任务而非启动新任务，本就应在运行中允许调用」。

#### E3. 打开目录的三连修复（v1.8 → v1.10）

用户要「给每个下载了的订单增加一个打开那个目录的按钮」。这个功能连续修了三轮，是全项目最曲折的 bug 链：

1. **v1.8 初版**：`POST /api/orders/:orderNo/open`（只接受台账内订单号防路径注入）+ Windows `explorer` 打开。API 三种情况验证通过。
2. **v1.9 误报失败**：用户反馈实际打开了但控制台报 `Command failed: explorer "..."`，且窗口静默不置前。根因：explorer 经 cmd 包装是 GUI 单实例程序，重复打开返回非零退出码被误判失败。改用 PowerShell `Shell.Application.Open`（COM 方式会激活窗口置前）+ spawn 后台运行。
3. **v1.10 完全没反应**：改完后用户反馈点击完全无反应。这次表面退出码 0、无报错，AI 用「命令内部写 marker 文件」的方式做四路对照诊断，证实 **spawn 带 `detached: true` 时 PowerShell 运行在无窗口站，COM 创建资源管理器窗口被静默抑制**——命令根本没执行。去掉 detached 保留 `stdio: 'ignore'` + `unref()` 后修复。

这条 bug 链沉淀为 lessons-learned §1：Windows 下 detached 子进程无法 COM/GUI 交互；排查「命令是否真的执行」要用进程内写 marker 文件，不能依赖 exit code / stdout。

#### E4. 自动清理过期目录（v1.11）

用户明确要求：「自动清理图片，点击按钮或每次启动时清理，会自动清理30天之外的目录，整个目录删掉，不是软删除，写完之后你可以mock一个过期的数据来测试」。实现 `cleanupExpired(30)`：遍历 output 下订单子目录，台账 `downloadedAt` 优先、无则回退目录 mtime，早于 30 天整个目录 `fs.rmSync` 硬删除 + 台账重置 PENDING；入口为启动自动清理 + 「🧹 清理过期目录」按钮。按用户要求做了 mock 真实验证（独立临时实例）：台账 60 天前订单与孤儿目录均被硬删除、5 天前目录保留、真实台账不误删。

#### E5. 订单号搜索（v1.12）

用户：「忘了，还有一个最重要的功能，就是搜索功能」——这句话本身就很 vibecoding。采用纯前端方案（复用轮询已有全量台账，模糊匹配忽略大小写、与分页联动、轮询期间保持搜索状态），零新增后端 API，改动最小。真实台账 69 单模拟验证全部符合预期。

#### E6. tasks/checklist 全量同步（v1.13）

用户要求「更新cheklist和tasks，全部都要检查一遍」。全库扫描确认所有 tasks/checklist 无未勾选项，补齐本会话新增功能的任务项与验收项，修正项目级 spec v0.4.0 和 4 个 subspec 的过时「提议」状态，重跑单测 30 条全绿。

#### E7. 打包单文件 exe（v1.14）

用户：「怎么把benchmark-collector打包成exe……我要发给客户了」。

**可行性预判**：运行时只有 playwright-core（纯 JS）+ jimp（纯 JS）+ Node 内置模块，CDP 连客户已装的浏览器不捆绑，HTML 内联无外部静态资源，无原生编译模块——非常适合打包。同时明确告知边界：客户机器仍需装并登录 Chrome。

**方案演进**：初选 `@yao-pkg/pkg`，但其必须从 GitHub release 下载 patched Node base，本环境 GitHub CDN（objects.githubusercontent.com）被重置，node 内建 fetch 和系统 curl 均失败（npmjs.org / nodejs.org 反而可达）。弃 pkg 改用 **Node 官方 SEA**：本地 node.exe 生成 blob 再注入，完全离线。

**SEA 三个坑**（沉淀为 lessons-learned §2）：

| 坑 | 现象 | 解法 |
|---|---|---|
| chromium-bidi 未安装 | esbuild 静态解析 require 报错 | `--external:chromium-bidi`（CDP 路径根本用不到） |
| SEA 嵌入脚本无 `require.resolve` | playwright-core `nodePlatform.js` 顶部 `require.resolve("../../../package.json")` 在模块加载期必执行，启动即崩 | esbuild 打包后字符串精确替换为 `process.cwd()`（该值仅影响堆栈前缀） |
| `useSnapshot: true` 的 undici bug | v22.14.0 生成 blob 报 `WebAssembly is not defined` | 回退非快照模式 |

最终 build-exe.mjs 四步流水线（esbuild 打单文件 CJS → 修补 require.resolve → 生成 blob → copy node.exe + postject 注入），产物 85.7MB，`npm run build:exe` 可复现。exe 实测启动成功、curl 返回管理页 HTML、全部依赖正常加载。

#### E8. 双击 exe 免命令（v1.15）

交付前用户实际试用，任务报 `CDP_CONNECT_FAILED: 端口 9222 不可用 (port-closed)`。排查发现两个根因：`findSystemChrome()` 只搜 Google Chrome 路径，用户机器装的是星愿，返回 null 后 `chrome-cdp.js` **静默退出**（这正是当初 A3 阶段就踩过的同一个坑）；管理服务不自动拉起浏览器，把「起调试浏览器 + 登录」的责任丢给了用户。

用户的不满很直接：「都打开exe了为什么还要输入命令，你不觉得很离谱吗」。修复分两步：findSystemChrome 补星愿路径；管理器新增 `ensureCdpBrowser()`——CDP 端口未监听时自动 spawn 浏览器（独立 profile）、轮询至就绪、打印「请登录拼多多」提示，`start()` 与 `--scan`/`--fetch` 模式都生效。重新打包 exe 实测：双击 → 自动拉起 Chrome → 9222 就绪 → 服务运行。

最后用户还有一层疑虑：「你自动拉起还是要用到npm啊」。AI 解释了关键概念：**exe 本身就是 Node 内核 + 程序代码打包在一起的**，运行时只调 Windows 自带的 powershell/cmd 和浏览器 exe，grep 确认无任何 node/npm 运行时调用。交付结论：只发一个 exe 文件，客户双击 + 装好 Chrome + 登录一次，全程零命令。

---

## 三、踩坑实录（按类别归并）

### 环境类

| 坑 | 影响 | 应对 |
|---|---|---|
| node 被解析为 PowerShell shim（node.ps1） | stdout/退出码捕获全不可靠，调试像盲盒 | 定位真实 node.exe；一律「输出重定向到文件」或 execFileSync 写报告文件 |
| GitHub release CDN 被重置 | pkg 无法下载 base 二进制 | 弃 pkg 改 Node SEA（完全离线） |
| winget / msiexec 被沙箱拦截 | Chrome 无法静默安装 | 交还用户手动安装，聚焦真正的问题 |
| PowerShell 保留变量 `$pid` 冲突 | 终止进程命令报错 | 换变量名 |

### 浏览器/页面类

| 坑 | 影响 | 应对 |
|---|---|---|
| findSystemChrome 只认 Chrome | 星愿用户浏览器拉不起来且静默退出 | 补星愿路径（此坑出现两次，第二次才根治） |
| 复用用户首页时 SPA 不渲染客服界面 | 找不到日期输入框/查询按钮 | 新建独立页面；后又一律 goto 刷新 + 轮询等待 |
| cleanup 无条件关页面 | 用户的商家界面被工具关掉 | CDP 模式不关闭任何页面 |
| detached 抑制 COM | 打开目录表面成功实则未执行 | 去掉 detached；marker 文件诊断法（lessons §1） |

### 数据/产品类

| 坑 | 影响 | 应对 |
|---|---|---|
| 订单号无独立字段 | 只能从文本正则提取 | 「订单编号:(\S+)」正则，真实样本验证 |
| 退款/未下单会话天然无订单号 | 图片无处归档 | 用户裁定：有图无订单=未下单跳过（NO_ORDER） |
| URL 去重失效 | 同图不同 URL 重复下载 | 订单内 MD5 去重 |
| MD5 去重失效 | 重传同图字节不同 | jimp dHash 感知哈希（sharp 不支持 BMP 被淘汰） |
| 扩展名按 URL 猜 | .jpeg 实为 WebP/BMP 打不开 | 文件头 magic bytes 判定 |

### 前端类

| 坑 | 影响 | 应对 |
|---|---|---|
| 内联 onclick 引号冲突 | 下载按钮从未成功触发过任务 | 事件委托 + data 属性 |
| doStop 被 busy 自拦截 | 停止按钮永远无反应 | 独立 stopping 标志 |
| 扫描结束才写台账 | 界面长时间零变化像死机 | 实时落盘 + 进度显示 |

---

## 四、vibecoding 方法论提炼

这个项目是一次比较完整的 vibecoding 样本，以下几点值得复用。

**1. 需求是逐轮「挤牙膏」式注入的，架构要接得住。** 用户从头到尾没有给过一份完整需求文档：先是「拉个开源项目」，再是「我是做打印照片的」，中途「忘了，还有一个最重要的功能」，临交付前「都打开exe了为什么还要输入命令」。项目能接住这种节奏，靠的是 A2 阶段先把「要什么/有什么/差什么」问清楚，以及 B3 阶段的层级 spec 体系让每个新需求都有明确的落点（判定模块 → 建 subspec → 文档先行 → 实施）。

**2. 用户的抱怨是最精准的 bug 报告。** 「点击暂停没反应」「会自动关闭商家界面」「你搞错了，我是针对这个bug」——每一句背后都是一个真实根因（busy 自拦截、cleanup 关页面、视觉去重时序）。vibecoding 中 AI 的核心职责之一是把口语化的现象描述转译成可诊断的技术问题，先拿证据定位根因，再动手修。

**3. 验证闭环是信任的来源。** 每个功能落地都伴随验证：单元测试从 16 条涨到 30 条；真实环境小规模跑（--max-accounts 8）确认后再全量；清理功能按用户要求 mock 过期数据实测；exe 打包后真实双击验证。环境不可靠（终端吞输出）时宁可换验证手段（写文件、marker 文件、execFileSync 报告），也不放弃验证本身。

**4. 文档先于代码，代码反哺文档。** 所有行为变更（未下单跳过、去重规则、错误码）都先改 spec 再改代码；实现中发现数据契约与 spec 不符（buyerUid 缺失）时回写 spec。决策日志 25 条让「为何这样定」全程可回溯，lessons-learned 把环境特有的坑变成可复用资产。

**5. 诚实面对失败和边界。** pkg 打包失败就明说失败原因换路线；sharp 不支持 BMP 就承认选型错误换 jimp；「主脚本文件意外丢失」如实标注非 agent 删除并按编辑历史重建；交付 exe 时明确告知「客户机器仍需装 Chrome，exe 不捆绑浏览器」。这种诚实避免了把风险藏到交付之后。

**6. 多 Agent 并行需要冲突纪律。** 两个 Agent 同时改 spec 发生了描述覆盖，事后靠「只补回自己的、完整保留对方的、标注归属」化解。教训是并行改动共享文档时应约定只追加不重写。

---

## 五、最终产出物清单

| 类别 | 产出 | 位置 |
|---|---|---|
| 采集下载核心 | pdd-image-downloader.js（三重去重/扩展名修正/未下单跳过/页面生命周期） | `scripts/` |
| 管理系统 | pdd-order-manager.js（台账/扫描/单订单下载/批量下载/分页/搜索/打开目录/清理/Web 界面） | `scripts/` |
| 单元测试 | 2 个测试文件，30 条用例 | `scripts/__tests__/` |
| 打包流水线 | build-exe.mjs（esbuild + SEA + postject，`npm run build:exe`） | `scripts/build-exe.mjs` |
| 交付产物 | pdd-order-manager.exe（约 85.7MB，免装 Node） | `dist-exe/` |
| Spec 体系 | 项目级 + 4 模块 + 7 subspec，36 文件 | `specs/` |
| 决策记录 | 决策日志 v0.1 ~ v1.15，25 条 | `决策日志.md` |
| 经验教训 | lessons-learned §1（detached/COM）、§2（SEA require.resolve） | `lessons-learned.md` |

**交付形态**：单文件 exe + 一句「装好 Chrome，双击它，登录一次」。客户全程零命令、零环境安装。
