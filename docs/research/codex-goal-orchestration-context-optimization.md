# Goal Orchestration 的 Codex 上下文优化：以 Pi、`context-mode` 与 `rpiv-mono` 为参照

> 调研日期：2026-08-21
> 资料范围：仅使用两个官方 GitHub 仓库的 README、docs 与源码。
> 固定版本：[`context-mode@e47942d`](https://github.com/mksglu/context-mode/tree/e47942d41d79c35ecce13013c9e75122d8470705)，[`rpiv-mono@c2f66ba`](https://github.com/juicesharp/rpiv-mono/tree/c2f66ba60658f5131d4952b77d6793383ac50e93)。
> Codex runtime 兼容性注记更新于 2026-08-24。

## 结论先行

本研究的优化目标是运行在 **Codex** 上的 `goal-orchestration` skill。Pi 不是实施目标，而是设计参照：小核心、普通文件、按需扩展、不把特定工作流烙进 runtime。

这个 skill 最值得吸收的不是把两个项目整体装进来，而是四个很窄、可独立验证的契约：

1. **渐进加载编排规则。** 核心 `SKILL.md` 只做路由，只有对应触发条件出现时才加载 coordination、returns 等引用；现有实现已经走在正确方向。
2. **跨 Agent 只传 capsule、证据和指针。** 大输出外置的思想只应用于 skill 能控制的 subagent 返回与 durable artifact；Codex 主工具输出的统一截断属于宿主 runtime/extension，不塞进 skill。
3. **把 durable state 当硬预算 TOC。** `STATUS.md` 只保存 accepted evidence、blocker 和 exact next action；稳定目标与计划采用差分更新，不把 transcript 搬入状态文件。
4. **明确 new-Agent/continuation 边界。** 新任务、架构边界和独立 review 使用新 Agent，并在支持时请求最小历史；这不保证空上下文。同一任务的 repair 继续原 implementer，只发送新失败证据。

不建议吸收到 skill：`context-mode` 的 MCP/SQLite/多运行时执行器、`rpiv-pi` 的完整 workflow/agent suite，以及每轮固定回灌的 active memory。它们是 runtime 或产品能力，会让一个控制策略 skill 变成沉重的数据平台。

## 对照总览

| 机制 | 主要解决的问题 | 代价与边界 | 对 Codex skill 的处理 |
|---|---|---|---|
| `context-mode` 执行/抓取结果外置 | 原始命令、网页和 MCP 输出淹没上下文 | 统一主工具输出策略超出 skill 能力边界 | **只借鉴 pointer return；runtime 暂缓** |
| SQLite FTS5 + BM25/模糊检索 | 历史资料和会话细节无法按关键词找回 | 索引、WAL、多 writer 与清理复杂 | **不进入 skill** |
| session TOC / resume snapshot | compaction 后遗忘目标、文件和决策 | 必须有硬预算，不能复制 transcript | **映射为差分 `.agent/STATUS.md`** |
| `rpiv-pi` 隐藏 skills + 短指针 | 常驻技能菜单消耗 prompt | 需要明确的按需入口 | **强化现有 `Load Minimally`** |
| 路径范围 guidance 延迟注入 | 仓库规则常驻、重复注入 | 自动路径事件属于宿主能力 | **用三文件 capsule 近似，不新增注入器** |
| artifact handle + fresh stage | 多阶段工作互相污染上下文 | fresh 增加调用和重读成本 | **复用 bounded/pointer return 与新 reviewer 实例** |
| transcript replay todo | 小型任务状态在压缩后丢失 | 扫描历史会扩大隐式依赖 | **用显式小状态文件，不 replay transcript** |
| `/btw` 只读旁路问题 | 临时问题污染主会话 | 额外复制上下文调用模型 | **与编排 skill 无关** |

## Pi 的参照意义：约束设计，不作为实施目标

Pi 的设计哲学不是“什么都不做”，而是把核心保持为最小 terminal harness，把具体工作流交给 extension、skill 和普通文件；它明确不内置 MCP、subagent、plan mode、todo 与 background bash[README：定位](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/coding-agent/README.md#L15)，[README：哲学](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/coding-agent/README.md#L493)。对 Goal Orchestration 的约束是：skill 只表达控制策略，不在其内部重建 runtime。

Pi 自己已有三层 runtime 上下文保护，它们用于说明“机制应该落在哪一层”，不是要求在 Codex skill 中重做：

- 内建工具输出默认限制为 2,000 行或 50KB[`truncate.ts`](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/coding-agent/src/core/tools/truncate.ts#L5)；bash 超限时把完整输出保存在临时文件，只回传 head/tail 与路径[`bash.ts`](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/coding-agent/src/core/tools/bash.ts#L347)。这已经是 `context-mode` “外置 + 指针”的轻量版。
- compaction 默认保留最近 20k tokens、预留 16,384 tokens，摘要包含 Goal、Constraints、Progress、Decisions、Next Steps 与 Critical Context；送去摘要的单个 tool result 会先截到 2,000 字符[`compaction.md`](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/coding-agent/docs/compaction.md#L32)。
- extension 可在统一 `tool_result` hook 替换结果内容和 details，也可在请求 provider 前通过 `transformContext` 改写消息[`agent-session.ts`](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/coding-agent/src/core/agent-session.ts#L506)，[`agent-loop.ts`](https://github.com/earendil-works/pi/blob/5cd93f688aaab89dbb6dfa4aca535f21796ae185/packages/agent/src/agent-loop.ts#L288)。这说明在 Pi 里此类机制属于 extension，而非工作流说明文本。

这些实现说明 Pi 把 tool-result 改写和 compaction 留给 runtime/extension。Goal Orchestration 没有这些宿主 hook，也不应该模拟它们；它能控制的是自身引用加载、delegation capsule、subagent return、durable state 与 fresh/continuation 决策。

## 一、`context-mode`：把内容挡在主上下文之外

### 1. 它解决什么

项目对问题的定义很直接：MCP/命令原始输出会填满上下文，压缩又会丢掉先前工作的细节。其方案分三层：在子进程中聚合/筛选输出、把大内容写入 SQLite 并按需检索、把分析从“把原料倾倒给模型”改成“用代码只返回结论”[README：问题与方案](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/README.md#L32-L51)。

这不是单纯的摘要器，而是一个 **context firewall**：

- `ctx_execute` / `ctx_execute_file` 在进程外执行代码，只把 stdout 送回模型；项目明确鼓励在脚本内先筛选、聚合、去重[README：执行模型](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/README.md#L1176-L1184)。
- 内容超过阈值时存入索引，工具回复改为标题、短预览和可继续搜索的来源指针。源码阈值分别为 intent search 5,000 字符、普通大输出 102,400 字节[`server.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/server.ts#L1955-L2025)。
- session 中的文件、任务、计划、规则、用户提示、决策、git/error 等事件被捕获，用于压缩后的恢复[README：捕获分类](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/README.md#L1255-L1285)。

### 2. 检索架构与算法

底层不是 embedding/vector search，而是纯词法检索：

- SQLite 内建两张 FTS5 表：Porter stemming + `unicode61` 与 trigram[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L463-L504)。
- 两路结果通过 Reciprocal Rank Fusion 合并，`K=60`；查询还会经过 stopword 清理与 FTS 语法消毒[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L51-L125)，[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L1242-L1284)。
- 排名再加 title 命中、邻近词和相邻词组 boost；无结果或低质量时做 Levenshtein 拼写纠正，并有 256 项 LRU 缓存[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L1193-L1240)，[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L1286-L1388)。
- Markdown 按 H1-H4 标题切块，目标上限约 4KB；普通文本按空段或 20 行窗口切分，并带 2 行重叠[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L1644-L1763)，[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L1858-L1915)。
- `relevance` 只在当前 `ContentStore` 做 BM25；`timeline` 则把内容库、SessionDB、auto-memory 按时间合并，不是跨来源统一相关性排序[`unified.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/search/unified.ts#L61-L68)，[`unified.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/search/unified.ts#L91-L175)。

这套算法的优点是确定、便宜、可本地运行；边界是必须能提供合适词面，概念同义但不共享词面的内容仍可能漏召回。README 所说“代码块不拆”也有条件：超大 chunk 会进入按段落的硬拆逻辑，该逻辑不维护 fence 状态，所以超过 4KB 的 fenced code 仍可能在空行处分开[`store.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/store.ts#L1667-L1695)。

### 3. 持久化与压缩续航

README 描述的是项目级 SQLite cache、24 小时内容 TTL、14 天清理，并提供 Porter/trigram 并行检索与渐进限流[README：索引与搜索](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/README.md#L1186-L1231)。搜索防洪按 agent 维护滚动窗口：1–3 次正常，4–8 次收紧，9 次以上阻断；actor 桶最多 4,096 个[`flood-guard.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/search/flood-guard.ts#L1-L21)，[`flood-guard.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/search/flood-guard.ts#L49-L109)。

这里有一处必须以源码为准的冲突：README 声称 snapshot “≤2KB”且会按优先级丢弃内容[README：snapshot](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/README.md#L1288-L1305)；但当前 `snapshot.ts` 文件头明确说明 snapshot 已改为 TOC、完整数据留在 SessionDB、**zero truncation**，`maxBytes` 只为兼容保留且被忽略[`snapshot.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/session/snapshot.ts#L1-L14)，[`snapshot.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/session/snapshot.ts#L29-L33)。最终组装也确实拼接所有非空 section，没有 byte budget[`snapshot.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/session/snapshot.ts#L463-L471)。

当前 snapshot 的思路仍值得借鉴：只列最多 10 个活动文件并生成精确搜索提示，保留 active goal、最近 3 条各截到 400 Unicode 字符的用户消息，再列出“去哪里搜”的目录[`snapshot.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/session/snapshot.ts#L37-L60)，[`snapshot.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/session/snapshot.ts#L405-L459)，[`snapshot.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/session/snapshot.ts#L480-L576)。对 Goal Orchestration 的映射不是实现 snapshot，而是确保 `STATUS.md` 真正保持为硬预算恢复目录。

持久化还带来传统数据库运维问题。项目 ADR 记录过多进程/僵尸进程导致 WAL 超过 238MB、搜索挂起；最终选择 WAL、30 秒 busy timeout 和有界重试，但仍承认未来 zombie writer 会让 WAL 再膨胀[ADR 0001](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/docs/adr/0001-sessiondb-multi-writer.md#L9-L37)，[ADR 0001](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/docs/adr/0001-sessiondb-multi-writer.md#L55-L73)，[ADR 0001](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/docs/adr/0001-sessiondb-multi-writer.md#L95-L122)。这正是 Pi 第一阶段不应引入数据库的理由。

### 4. Pi 适配层的实际开销

`context-mode` 对 Pi 做了专门适配，因为当时 Pi 没有原生 MCP。bridge 会启动常驻子进程、先调用一次 `tools/list`，再把返回的工具逐个注册到 Pi；源码注释称，不桥接时约有 2.5k prompt token 的说明成本且没有实际工具[`mcp-bridge.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/adapters/pi/mcp-bridge.ts#L1-L22)。适配器为降低自身开销只注入较短的 Pi routing anchor，因为完整 routing 约 7KB[`extension.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/adapters/pi/extension.ts#L639-L663)。

它还会：

- 在真实模型轮次前才懒启动 bridge，并回收闲置 subagent[`extension.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/adapters/pi/extension.ts#L605-L635)。
- 每轮回灌高优先级 active memory，最多 50 条，估算上限约 500 tokens[`extension.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/adapters/pi/extension.ts#L665-L708)。
- 只注入一次 resume，并追加到 user context 以尽量保持 system prompt 前缀缓存[`extension.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/adapters/pi/extension.ts#L711-L749)。
- 在 compact 前生成 snapshot，并清理 7 天前的 session[`extension.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/adapters/pi/extension.ts#L825-L868)。

这些优化说明作者也在对抗自身架构的固定成本。包要求 Node ≥22.5，依赖 MCP SDK、`better-sqlite3`、Turndown、Zod 等，并包含 Pi/Claude/Gemini 等多适配面[`package.json`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/package.json#L61-L125)。对本 skill 来说，只复用“外置 + 指针”的返回契约，不复用整包。

安全边界也不能被“sandbox”这个名字掩盖。源码把执行工具标注为 destructive/open-world，执行器允许任意代码；普通执行的 stdout/stderr 合计硬上限默认 100MB，超出会杀进程[`server.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/server.ts#L1647-L1691)，[`executor.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/executor.ts#L231-L260)，[`executor.ts`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/src/executor.ts#L500-L557)。README 也说明只有 `execute_file` 做项目路径约束，通用 execute/batch 继承主机文件访问能力[README：安全模型](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/README.md#L1559-L1575)。因此它更像“子进程隔离 + 输出控制”，不是 OS 级安全沙箱。

官方 benchmark 报告 21 个场景中原始 376KB 降至 16.5KB（96%），结构化输出 98%、知识检索 82%[BENCHMARK](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/BENCHMARK.md#L6-L28)，[BENCHMARK](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/BENCHMARK.md#L30-L75)。这是项目自测，证明“回传字节”可以显著减少，但没有覆盖 Codex 编排的所有 subagent 调用、固定 skill 上下文、额外延迟或 accepted-work 正确率；不能直接等同于本 skill 的净收益。

## 二、`rpiv-mono`：把工作拆成可审查 artifact 与新上下文

### 1. 整体哲学与实际规模

`rpiv-mono` 明确把 driver 留在 loop 中，强调工作流可审查、fresh-context verification，并把 delegation strategy 视为仍在优化的问题[根 README](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/README.md#L52-L67)。它不是单一轻量库，而是约 15 个 package 的 monorepo，覆盖 Pi 组件、todo、advisor、workflow、btw 等[根 README](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/README.md#L7-L18)。`rpiv-pi` 自身不注册工具，但会组合多个 opt-in sibling package[`architecture.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/.rpiv/guidance/architecture.md#L7-L30)。

因此，“零自有工具”不等于零上下文或零依赖。`rpiv-pi` 声明 29 skills、15 subagents，阶段把 Markdown 写入 `.rpiv/artifacts`，并在 detached child sessions 中运行[`rpiv-pi README`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/README.md#L12-L18)。它更像为 Pi 建一个可组合的软件交付工作台，而不是极简 context manager。

### 2. 最值得 Pi 吸收：隐藏技能菜单与短指针

`rpiv-pi` 把 20/29 个 skills 标记为不可由模型直接发现，常驻上下文只注入约 120 token 的 pipeline pointer；官方文档估算节省约 3k tokens[`architecture.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/docs/architecture.md#L89-L95)。实际 pointer 是一段非常短的“何时使用 / 如何串联 / 从哪里找完整 skill”文本[`pipeline-pointer.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/pipeline-pointer.ts#L1-L16)，[`pipeline-pointer.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/pipeline-pointer.ts#L27-L47)。

这是所有候选机制里与 Pi 哲学最一致的一项：不改变模型行为主循环，只减少常驻元数据。对 Goal Orchestration 的直接映射是保持主 skill 短小、references 按触发加载；Codex 的全局 tool schema 不由这个 skill 管理。

### 3. 路径驱动 guidance 注入

当模型 read/edit/write 某个文件时，`rpiv-pi` 才从 repo root 沿目录向目标文件寻找 `AGENTS.md`、`CLAUDE.md` 或 shadow guidance；每层最多注入一个文件，注入内容对用户隐藏，并在进程内去重。compaction 后先延迟，等下一次真实 user turn 再合并注入[`architecture.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/docs/architecture.md#L52-L75)。git context 也只在仓库状态变化时重算[`architecture.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/docs/architecture.md#L77-L87)。

它表达了一个关键原则：**上下文应跟当前工作集走，而不是跟仓库总知识量走。** 本 skill 用 authoritative capsule 和最多三个文件指针表达工作集，不增加自动路径事件或索引器。

### 4. Artifact handle 与 fresh-stage workflow

`rpiv-workflow` 让每个 stage 在 detached session 中运行，stage 之间不直接搬运完整上下文，而是传 `Output`：artifact handle、可选结构化数据和 metadata；运行记录追加写入 `.rpiv/workflows/runs/<id>.jsonl`，可恢复、可审计[`rpiv-workflow README`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/README.md#L12-L18)，[`rpiv-workflow README`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/README.md#L42-L94)。默认 `sessionPolicy` 是 `fresh`；只有显式选择时才从持久化 session 继续[`run-stage.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/runner/run-stage.ts#L312-L369)。

handle 支持 filesystem、URL、opaque、inline，传给下游 prompt 时通常只投射为一行；inline handle 只暴露 byte count，不展开正文[`handle.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/handle.ts#L1-L38)，[`handle.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/handle.ts#L67-L84)。这是很好的接口形态：阶段边界传“句柄 + 契约”，而不是传全文。

但 fresh context 只降低单次活动窗口，不保证降低总成本：每个 stage 是一次新模型调用，还需要重读 artifact，未写入 artifact 的隐性上下文会丢失。持久化本身也有边界：JSONL 是 append-only system of record，schema v2 没有 migration，文件权限只依赖进程 umask；TypeScript workflow config 是可执行代码，需要被视为 trust boundary[`workflow-basics.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/docs/workflow-basics.md#L178-L199)，[`rpiv-workflow README`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-workflow/README.md#L96-L115)。

对 Goal Orchestration 的启发不是默认把每次工作都切成 pipeline，而是规定：**只有跨上下文返回或真实 durable boundary 才写 artifact；下一个上下文只接收指针和验收契约。**

### 5. Child lane、转录与 artifact 发现

`rpiv-pi` 的 lane 通过 detached child session 隔离任务，主进程保留 live session、最终 branch、工具定义、usage、session file 和待处理输入等状态[`run-lane-registry.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/run-lane-registry.ts#L90-L132)。如果 live session 不可用，会从完整 child JSONL 转录只读恢复；该机制 fail-soft，不承担写回[`lane-transcript-disk.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/lane-transcript-disk.ts#L1-L16)，[`lane-transcript-disk.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/lane-transcript-disk.ts#L30-L90)。

Artifact collector 不把产物全文重新塞回主上下文，而是扫描 transcript 找路径、读取 frontmatter 形成结构化数据；坏 YAML 也是 fail-soft[`artifact-collector.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/artifact-collector.ts#L1-L24)，[`artifact-collector.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-pi/extensions/rpiv-core/artifact-collector.ts#L44-L108)。这种“控制面只读 metadata，数据面留在文件”的分层值得保留；整个 lane orchestration 则不应成为 Pi 核心依赖。

### 6. `rpiv-todo`：从 transcript 重放小状态

`rpiv-todo` 不额外写数据库。每次 todo 工具调用返回一次完整 post-mutation snapshot，恢复时按当前 session branch 顺序扫描，最后一个匹配的 `toolResult` 即当前状态[`rpiv-todo README`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-todo/README.md#L46-L65)，[`replay.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-todo/state/replay.ts#L15-L37)。

它很好地利用了 Pi 已有 transcript 作为 event log，适合十几个以内的任务状态；但每次 mutation 都复制完整列表，tool result 累积成本近似“变更次数 × task 数”，不适合一般记忆库。Goal Orchestration 已有条件触发的小状态文件，无需依赖 transcript replay。

### 7. `rpiv-btw`：不污染主会话，但未必省总 token

`/btw` 用当前分支快照加独立 BTW history 发起一次只读 completion，`tools=[]`，不写主 transcript 和磁盘[`context-model.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-btw/docs/context-model.md#L6-L18)，[`context-model.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-btw/docs/context-model.md#L85-L95)。它保留原始 message 对象以利用 prompt prefix cache，并缓存 stable branch；跨 session 只保留最近 10 个问题提示[`context-model.md`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-btw/docs/context-model.md#L45-L71)。

预算算法默认 BTW history 8,192 tokens、为回答预留 16,384；先选择最新的最大后缀，再保持 turn/tool 原子性，必要时先把最老 tool result 替换为 stub，最后截最大文本块[`btw-budget.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-btw/btw-budget.ts#L24-L31)，[`btw-budget.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-btw/btw-budget.ts#L200-L225)，[`btw-budget.ts`](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/packages/rpiv-btw/btw-budget.ts#L228-L341)。

这能保护主对话的“上下文卫生”，但第一次调用尽量带完整当前分支，并使用同一主模型；因此它可能额外消费接近一遍当前上下文。适合作为显式用户功能，不宜计入核心“省 token”方案。

## 三、转译到 Codex skill 的边界

这三个参照项目混合了三种层级，必须先分开，否则会把 runtime 能力误写成 skill 责任。

| 层级 | Goal Orchestration 能否控制 | 本次处理 |
|---|---|---|
| Codex 宿主：tool schema、工具结果截断、compaction、prefix cache | 否 | 只记录为可选产品/extension 方向，不修改 skill |
| 编排控制：何时激活、加载哪些引用、何时新建或继续 Agent | 是 | 作为主要优化面 |
| 跨 Agent 数据面：capsule、direct return、pointer artifact、durable state | 是 | 收紧准入契约和更新时机 |

因此不应在这个仓库实现 `ToolResultPolicy`、SQLite 搜索、MCP bridge、自动路径 hook 或 transcript memory。它们即使有价值，也属于 Codex runtime、插件或另一个独立 extension。

Skill 层真正可以吸收的机制只有：

1. **Lazy metadata → 渐进引用加载。** 保持 `SKILL.md` 是短路由；只有并发写、跨上下文返回等触发出现时才加载对应 reference。
2. **Externalize + pointer → bounded/pointer return。** routine return 继续限长，只有直接返回放不下或可能跨 context 时才写唯一 inbox artifact；不把 pointer 变成默认路径。
3. **Session TOC → 差分 durable state。** `.agent/**` 只在 durable trigger 下出现，稳定的 goal/plan 不随每个 checkpoint 重写，`STATUS.md` 承担小型恢复目录。
4. **Fresh stage → new Agent / continue repair。** 新 Agent 用于新的 framing 和独立审查；是否减少父历史取决于 runtime，capsule 始终权威。focused repair 保留实现者的局部上下文，避免重读代码和重新 bootstrap。
5. **Working set → capsule 文件指针。** 不做自动 guidance 注入；由主 Agent 在 capsule 中显式选择最多三个当前任务真正需要的文件。

效果必须按 Codex 的完整执行成本衡量：accepted milestone 前主上下文增长、所有 subagent 返回和额外调用、旧证据重读次数、恢复正确率、墙钟时间。`context-mode` 的回传字节压缩率与 `rpiv` 的单 prompt 节省都只能作为方向性证据，不能直接当作本 skill 的净收益。

## 四、映射到当前 Goal Orchestration

当前仓库已经吸收了几项最重要的思想，而且实现得比两个参照项目更轻：

- 激活边界窄，普通任务不加载编排控制；引用文件也按触发条件渐进加载[`SKILL.md`](../../skills/goal-orchestration/SKILL.md#L13)。
- capsule 只带任务局部事实和最多三个文件指针，直接返回有字符/行数上限，跨上下文才启用 8 KiB pointer return[`unattended.md`](../../skills/goal-orchestration/references/unattended.md#L40)，[`returns.md`](../../skills/goal-orchestration/references/returns.md#L1)。
- durable work 才创建 `GOAL.md`、`PLAN.md`、`STATUS.md`；repair 复用原 implementer，只发送新失败证据；soft refresh 只在 accepted milestone 或真实暂停点评估[`unattended.md`](../../skills/goal-orchestration/references/unattended.md#L25)，[`unattended.md`](../../skills/goal-orchestration/references/unattended.md#L80)。
- 独立审查使用新 reviewer 实例并在支持时请求 `fork_turns=none`，但不承诺空上下文；实现修复保留同一 Agent 的局部工作记忆[`SKILL.md`](../../skills/goal-orchestration/SKILL.md#L53)。

因此这个仓库不需要新增 workflow engine、memory DB 或工具层。最值得做的是把现有规则补成一个更精确的 **context admission contract**。

### P0：先补可测基线，不先加机制

在现有 `evaluations/` 下维护小型任务样本，记录：主 Agent 输入增长、subagent 返回总字符、重新读取旧返回/日志次数、compaction 后恢复正确率、accepted milestone 的墙钟时间。目标指标是“每个 accepted milestone 的总上下文成本”，不是单次返回压缩率。

特别要保留 runtime probe 的版本差异：2026-08-20 的探针观察到 `none` 子任务含无关父上下文，2026-08-24 的对照则观察到 `none` 不可见父级用户轮次、`all` 可见。因此 `fork_turns=none` 只能作为当前接口请求，不能作为空上下文或隔离保证；authoritative capsule + artifact pointers 才是稳定契约[`runtime-surfaces.md`](../../evaluations/runtime-surfaces.md#L23)。

### P1：只改技能契约的三处窄优化

1. **差分 durable state。** 初始化时创建三份状态文件；之后 `GOAL.md` 仅在 outcome/constraints 变化时改，`PLAN.md` 仅在 milestone/dependency/ownership 变化时改，accepted wave 或暂停点通常只改 `STATUS.md`。当前“先一次性写三份”是合理 bootstrap，但不应被解释为每个 checkpoint 都重写稳定文件。
2. **证据带覆盖范围。** 将 return 的 `VALIDATION` 语义收紧为“命令/检查 + 覆盖的路径或 artifact + 结果”，不要求复制日志，也不默认计算内容 hash。这样主 Agent 能执行现有的 selective invalidation 规则，而不用重新读整份 diff 或旧返回。
3. **显式实例边界。** 任务、所有权、专业能力、架构/共享契约或独立 review 边界变化时使用新 Agent；相同任务和作用域的 focused repair/后续 wave 继续原 implementer。新实例只接收 capsule、代码路径和验收证据，不传前一 Agent transcript；是否真正减少父历史由 runtime 决定。

这三项不新增文件、工具或 Agent，也不会扩大隐式激活面。对应测试只需静态检查差分写入规则、evidence coverage 字段语义和 new/continue 分界。

### P2：只有出现真实跨上下文压力时才扩展 pointer

现有 `returns.md` 已足够处理 subagent 大返回。若评估显示主要成本来自 main Agent 自己的长测试日志、网页或大型 diff，再单独研究 Codex 宿主侧的 tool-result spooler：大输出落 session-local artifact，主上下文只收 head/tail、失败摘要和稳定指针。它应是可选 runtime/extension，不应进入 Goal Orchestration 的默认 skill 文本。

### 对当前仓库的建议优先级

| 优先级 | 方向 | 预期收益 | 新复杂度 |
|---|---|---|---|
| P0 | 建立 accepted-milestone 净上下文基线 | 防止为宣传压缩率优化 | 仅评估资料 |
| P1 | 差分状态写入 | 少写、少重读、稳定事实不抖动 | 一条规则 + 静态测试 |
| P1 | evidence coverage 契约 | 更准确地复用/失效验证证据 | 小幅 return schema 调整 |
| P1 | new Agent / continue repair 不变量 | 隔开任务 framing，同时保留修复局部性 | 文档与测试 |
| P2 | 可选 tool-result spooler | 处理主 Agent 大输出 | 独立扩展；不进 skill 核心 |
| 暂缓 | FTS/memory DB、完整 workflow、todo/lanes | 当前没有收益证据 | 高 |

最终落点应保持现有架构：Goal Orchestration 是 **控制策略层**，不成为数据平台。它只规定哪些事实准入 capsule、哪些事实留在文件/代码、何时新建或继续 Agent；历史可见性和真正的大输出外置留给宿主 runtime 或可选扩展。

## 五、明确不建议照搬的设计

- **在 skill 中把普通 shell/curl 全局改道到 context 工具。** 这是宿主 runtime/extension 的职责，也会扩大本 skill 的隐式能力面。
- **每轮无条件回灌约 500 tokens active memory。** 对短任务是纯税；本 skill 已有条件 durable state，不再增加常驻 memory 注入。
- **把 11 个 context 工具、7KB routing 和 MCP 子进程加入 skill。** Codex 已提供原生工具与 Agent 能力；skill 只约束它们的使用和跨 Agent 数据契约。
- **把 29 skills、15 agents 和完整 workflow suite 变成激活后的默认路径。** 它优化复杂交付流程，但会破坏当前“只按具体风险增加控制”的激活边界。
- **把历史控制请求当作 token reduction 或隔离。** 它的实际行为随 runtime 变化；必须把所有 child/stage 调用计入总成本，并让 capsule 独立成立。
- **把 `STATUS.md` 当摘要仓库。** 它应是有硬预算的恢复目录，原始事实留在代码、验证产物或外置 return；否则恢复状态本身会膨胀。

## 六、验收建议

选择一组真实 Codex 编排任务，至少覆盖：普通 focused work（应不激活）、单个 bounded subagent（应走原生能力）、durable multi-wave repair、并发写隔离、高风险 review/repair、跨 context pointer return 与 compaction 后恢复。对照当前 skill 和 P1 契约版本，验证：

1. 每个 accepted milestone 的主上下文增长与 subagent 返回总量是否下降；
2. Agent 调用数和完成延迟是否没有不合理增加；
3. capsule 能否精确保留约束、作用域、验收和最多三个必要文件；
4. compaction、resume、repair 与跨上下文 return 后能否恢复正确下一步；
5. evidence coverage 能否避免无效重跑，同时在相关输入变化后正确失效；
6. focused work 和简单 delegation 是否继续走原生 Codex，不被 skill 误激活。

## 七、许可注意

`context-mode` 的 `package.json` 标注 Elastic License 2.0[`package.json`](https://github.com/mksglu/context-mode/blob/e47942d41d79c35ecce13013c9e75122d8470705/package.json#L1-L7)；`rpiv-mono` 根 README 标注 MIT[根 README](https://github.com/juicesharp/rpiv-mono/blob/c2f66ba60658f5131d4952b77d6793383ac50e93/README.md#L104-L108)。可以借鉴设计思想，但若要复制 `context-mode` 源码，应先审查许可兼容性；本次对 Goal Orchestration 只转译契约，不复制实现。

## 最终判断

两个项目给出的共同方向不是“让模型记住更多”，而是：

> **常驻上下文只保留控制面；大内容、阶段产物和历史事实留在可寻址的数据面。**

`context-mode` 展示了数据面外置与词法找回的上限，也暴露了 MCP、数据库、多 writer 与执行器带来的重量；`rpiv-mono` 展示了 lazy metadata、artifact contract 和 fresh context 的工程组织方式，也暴露了多 package、多 agent 与额外模型调用的总成本。

对 Goal Orchestration 最合适的版本仍是一个薄控制策略：**按触发加载 references、跨 Agent 只传 bounded/pointer return、durable state 差分更新、new Agent 与 continue repair 明确分界**。工具结果截断、FTS、memory、workflow engine 与 BTW 都不进入这个 skill。这样才真正继承 Pi “小、透明、可组合”的设计哲学，同时适配 Codex 的可变 Agent 接口。
