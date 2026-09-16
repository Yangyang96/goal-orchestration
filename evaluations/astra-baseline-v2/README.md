# Astra 三组基线 V2

**状态：实现与离线检查完成；真实模型对照未执行。**

2026-09-16 当前执行容器没有 Codex CLI 或可用登录态，预检查返回 `BLOCKED`，
真实模型调用数为 **0**。本目录的参考实现和合成记账数据绝不是 Astra 成绩。
生产 Skill 与历史 `evaluations/astra-benchmark/` 不变。

## 比较对象

| 组 | 处理差异 | 子 Agent 工具 |
|---|---|---|
| A 原生默认 | 公共实验约束 + 业务任务，不加载 Skill、不额外提示委派 | 开启，与 B/C 相同 |
| B 原生可委派 | A + “必要时可将独立工作交给子 Agent，以收益是否超过协调开销为准。” | 开启 |
| C 当前 Skill | A + 显式调用冻结的当前 Skill；reference 按需读取 | 开启 |

A 是受控的同一 Codex 环境中的默认执行，不是没有工具的裸模型，也不是用户桌面
全部个性化设置的精确复刻。公共约束、权限、模型和推理档位完全相同，不强制任何
一组委派。配置请求相同不等于后端生效已证明，仍需校准/运行时审阅。

默认请求 `gpt-6-astra/xhigh`，父/子相同。生产快照来自
`1d0bbb11a6662982a7f471291197667bf08353ae`；campaign 按实际读取的 Skill 内容
SHA-256 冻结，包括未提交修改，因此不要只用 Git HEAD 识别被测版本。
C 当前版本先不改；优化候选后续用 `plan --skill OTHER_DIR` 建立独立 campaign，
保留原生 B/当前 C 对照，并用未用于调参的任务复验，不能边看成绩边改本轮输入。

## 场景与优化偏好

| 场景 | 当前可验证内容 | 不要据此宣称 |
|---|---|---|
| tiny | 简单开关解析修复，观察额外编排开销 | 零委派才算通过 |
| parallel | CSV/JSONL、SQLite 原子导入/并发、CLI 跨模块整合 | 已测试大型生产系统 |
| dirty | 未提交接口契约与用户草稿保留，避免遗漏真实输入 | 强制 worktree 或已证实硬隔离 |
| review | 紧耦合计算与消费接口，精确整数、平局规则、>2**53 边界 | 严格双盲/独立模型审阅 |
| handoff | 两个全新进程仅继承文件，第二阶段接口仅在第一阶段告知，禁止提前实现 | 随机崩溃、数日运行、真实在途子任务恢复 |
| stale | 预置旧版本草稿与当前契约冲突，防止错误覆盖已有数据 | 实时晚到子 Agent 产物注入 |

正确性、保留用户修改优先，随后分别比较总 token 与端到端等待。更快但 token
更多应称“资源换时间”，不能说两项都改善。Agent 数量、写了多少状态文件、
遵循了多少 Skill 术语均不计分。

判卷使用真实 API、CLI、SQLite 和 Git。初始缺陷必须失败，参考实现必须通过。
阶段一验收失败、进程正常结束时仍执行阶段二，但端到端结果保留失败；不向模型
反馈隐藏判卷结果重试。任务源码没有隐藏判卷器或参考实现。

边界：夹具、参考实现、判卷器由同一作者制作，尚未独立审查。部分场景共享
Ledgerkit 背景，样本相关，规模较小。机械通过不等于文档/自写测试质量、语义范围、
澄清必要性或独立审阅已通过；这些需另审日志和产物。参考实现自检不是完备性证明。

## 实际完成的离线检查

```bash
cd evaluations/astra-baseline-v2
python3 -m unittest -v test_baseline
python3 runner.py selfcheck
```

33 项 unittest 通过。6 个初始缺陷样本均失败，6 个参考实现共 7 个阶段检查通过。
另检查了缓存不重复计数、缺少子线程用量、模型/effort 漂移、事件绑定、事务回滚
变异、用户输入丢失、提前实现阶段二、旧契约覆盖等。控制器合成单元测试的结果
只存在于临时目录，不进入正式 comparison。详见 `LOCAL_VALIDATION.json` 与日志。

## 运行条件和校准

本工具不安装 CLI、不复制凭据、不改已安装 Skill 或全局配置。使用正常授权的
Codex 登录。不要把 auth.json、API key、登录 token 放进聊天或提交仓库。

```bash
CODEX_HOME="$HOME/.codex-goal-benchmark" codex login
python3 evaluations/astra-baseline-v2/runner.py preflight \
  --codex-home "$HOME/.codex-goal-benchmark"
```

专用 home 不应含额外 AGENTS、Skill、自定义 Agent 或 hooks。runner 使用
`--ignore-user-config`，禁用额外插件/记忆，但并不能证明管理员约束、父目录指令、
宿主注入都已隔离。运行前校准必须确认：真实原生 spawn/return/close 能用，父/子
模型与 effort 的有效设置一致，权限和 Git/worktree 路径一致，全部子线程终结。
不要把参数被接受当成生效证明，也不要用嵌套 CLI 模拟原生子 Agent。

`preflight` 只检查 CLI、参数、登录状态和明显的额外指令，不调用模型；
`CLI_READY_NOT_RUNTIME_CERTIFIED` 不是运行时认证。`run` 能收集功能与 CLI
耗时记录，但不会自动宣布性能胜负。校准的费用/耗时另列，不混入执行样本。

模型与判卷器路径分开，**不是硬读取隔离或安全沙箱**。用户级同一文件系统仍可能
可读。正式强隔离需要专用容器/用户权限和独立 evaluator。模型生成的代码会在
本机运行，判卷环境不传凭据变量但仍可能读用户文件；请使用无其他敏感数据的评估
环境。现有平台沙箱/审批始终保留，不绕过，不单独给 C 放宽权限。

## 先 smoke，再完整 pilot

`plan` 不调用模型；`run` 会真实消耗账号额度。先做 3 类 × 3 组 × 1 次：
**9 个端到端样本，12 次父进程执行**，子 Agent 调用另外计入。

```bash
python3 evaluations/astra-baseline-v2/runner.py plan \
  --output /tmp/goal-astra-smoke-v2 \
  --tasks tiny parallel handoff --repeats 1
python3 evaluations/astra-baseline-v2/runner.py run \
  --output /tmp/goal-astra-smoke-v2 \
  --codex-home "$HOME/.codex-goal-benchmark"
```

smoke 与采集校准通过后，在**新目录**做 6 类 × 3 组 × 3 次：
**54 个端到端样本，63 次父进程执行**。这只是计划规模，不是已完成样本。

```bash
python3 evaluations/astra-baseline-v2/runner.py plan \
  --output /tmp/goal-astra-pilot-v2 --repeats 3
python3 evaluations/astra-baseline-v2/runner.py run \
  --output /tmp/goal-astra-pilot-v2 \
  --codex-home "$HOME/.codex-goal-benchmark"
python3 evaluations/astra-baseline-v2/runner.py report \
  --output /tmp/goal-astra-pilot-v2
```

顶层样本串行，内部可并行；每三轮同一任务每组各占一次执行顺序位置。固定随机
种子只固定调度，不声称固定模型采样。新工作目录、新进程、不传入其他组历史。
每父进程默认 900 秒；可在冻结前统一调整 `--timeout`。超时终止本地进程组，
不能保证未知远程孤儿任务已停止。尚无已校准的全 Agent 硬 token/货币预算闸门。

开始后不覆盖、不挑选性重跑；失败/中断保留。继续研究时另建 campaign 并报告
原来的失败，不把它们隐藏。不会自动恢复或重跑已开始的 campaign。

## Token 采集：明确区分已实现与缺口

**已实现：原始 CLI 事件保存与严格全 Agent 请求账本汇总。尚未实现/校准：
本机具体 Codex 版本的完整主/子请求级 usage 导出适配器。**

仅有 `turn.completed.usage` 时，总 token 记为 `null/UNKNOWN`，不是 0。无法确认
父线程用量是否已经聚合子线程时，不直接相加，也不按 Agent 数估算。

可信运行时 exporter 可向每阶段的 `usage-ledger.json` 写入 `goal-usage-v1`。
示例结构见 `test_baseline.py::ledger()`，其中数字仅供记账单元测试。正式导出
必须来自运行时，而非模型估算或自报。其 binding 还须完整绑定：

```json
{
  "run_id": "001",
  "phase": 1,
  "prompt_sha256": "actual digest of phase prompt.txt",
  "events_sha256": "actual digest of phase events.jsonl",
  "root_threads": ["actual CLI root thread id"],
  "cli_version": "actual campaign preflight CLI version"
}
```

账本含完整线程树、每线程有效 model/effort/终止状态、完整 request-id 清单，以及
每请求**自身增量** input/cached-input/output。input 已含缓存；output 不再重复加
reasoning。相同 request 重复导出只计一次；冲突、跨阶段/样本重用、缺项、模型
漂移、未终结、未校准都拒绝生成完整总数。

coverage 的声明与 evidence SHA **不能自证真实**；必须独立审阅 exporter 和原始
校准证据。`COMPLETE_EXPORTED` 只表示声明通过结构检查，不是运行时真实性认证。
本实现不猜费用、不换算订阅额度、不把缺失子 Agent 费用隐藏成节省。

## 报告解读

`comparison.json` 逐任务/组给出计划数、记录数、机械通过数、CLI 耗时中位数，
及完整用量才有的 token 中位数。未运行是 NOT_RUN，不当成模型失败；缺失 token
是 null，不为部分采集排名。保留失败的真实开销，不仅比较成功样本。

CLI 时间是父进程端到端观察值，handoff 为两阶段之和，不含判卷/搭建；不是 CPU
时间，也未认证所有子线程都已静止。质量、时间、token 各自报告，不自动输出综合
winner；C 只优于 A 未优于 B，可能只是委派提示作用，C 优于 B 才支持额外规则增益。
三次重复不足以声称统计显著、等效或全场景获益。

在真实对照完成前，**原来的性能结论不因这次离线检查而改变**。

官方接口依据（2026-09-16 核对，后续版本仍需校准）：
[Non-interactive](https://developers.openai.com/codex/noninteractive)、
[Subagents](https://developers.openai.com/codex/subagents)、
[Configuration](https://developers.openai.com/codex/config-reference)、
[Authentication](https://developers.openai.com/codex/auth)。
