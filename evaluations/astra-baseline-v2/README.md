# Astra 三组基线 V2

**状态：基线实现和离线检查完成；真实模型实验未执行。**

2026-09-16，本次会话容器没有 Codex CLI、授权模型执行通道或可调用的远程 Codex 环境。实际 launch preflight 返回 `BLOCKED`；真实模型调用数为 **0**。不要把单元测试、参考实现或计划中的样本数当成 Astra 性能结果。

历史 `evaluations/astra-benchmark/` 与生产 Skill 不变。当前比较目标是 `1d0bbb11a6662982a7f471291197667bf08353ae` 中的 Skill；每次 campaign 仍按实际读取的文件 SHA-256 冻结，不以 Git HEAD 代替内容身份。

## 三组与偏好

| 组 | 唯一处理差异 | 子 Agent 工具 |
|---|---|---|
| A 原生默认 | 任务 + 公共约束；不加载 Skill、不额外请求委派 | 开启，与 B/C 相同 |
| B 原生可委派 | A + “必要时可将独立工作交给子 Agent，以收益是否超过协调开销为准。” | 开启 |
| C 当前 Skill | A + 显式调用冻结的当前 Skill；reference 按需读取 | 开启 |

“原生”是相同受控 Codex 环境下不加载该 Skill，不是无工具裸模型，也不等同于每个人完整桌面个性化配置。三组权限、内置约束、模型和推理档位相同。不禁用 A 的委派工具、不强制 B 委派、不按 Agent 数量评分。

公共偏好：正确性和保留用户修改优先，同时避免不必要 token 与等待。默认请求 `gpt-6-astra/xhigh`，对子模型/effort 设置同样默认值。请求配置一致不等于实际后端配置已经证明，仍需日志校准；不能伪称固定内部权重版本。

C 本轮**不先应用待验证优化**，否则无法回答当前版本的增益。优化候选应在独立 campaign 与未参与调参的任务上再与 B/C 比较，不能看成绩后改本轮 Skill。内容注入不测试安装、自动发现或 UI 默认提示。

## 六类任务

| task | 主要验证点 | 边界 |
|---|---|---|
| tiny | 小修复负对照，避免为了编排而编排 | 不把零委派作为硬性得分要求 |
| parallel | 两种解析器、SQLite 存储和 CLI 的接口集成、事务、并发 | 不是大型生产仓库 |
| dirty | 未提交的接口契约和用户草稿必须保留 | 不强迫使用 worktree |
| review | 金额分配与消费者的紧耦合修复；精确整数和大数 | 不是严格双盲/独立审阅认证 |
| handoff | 两次新进程，只继承文件；阶段二需求仅在阶段一出现；禁止提前实现 CLI | 正常交接，不是随机硬崩溃或真实子任务中途丢失 |
| stale | 已恢复 v1 草稿与新契约冲突，不能覆盖数据 | 预置旧产物，不是实时晚到结果注入 |

判卷器执行真实 API、CLI、SQLite 原子性/幂等性/并发检查，并检查 Git 状态与用户草稿字节。阶段结束后由新 Python 进程判卷，不把隐藏失败反馈给模型重试。阶段一完整执行但验收失败时仍执行阶段二，端到端样本保持失败。

机械验收不取代人工审阅：文档质量、测试有效性、额外澄清、重复探索、审阅独立性和语义范围仍需检查日志与产物。夹具、判卷器、参考实现由同一作者编写，独立审查未完成。多个任务共享 Ledgerkit 背景，不能当成六个独立的大型真实项目。

## 本次已执行的离线验证

```bash
cd evaluations/astra-baseline-v2
python3 -m unittest -v test_baseline
python3 runner.py selfcheck
```

**33 项 unittest 通过。** 六个初始缺陷样本均被拒绝；参考实现共七个阶段检查通过。变异测试检出用户输入丢失、提前完成阶段二、事务不回滚和旧契约覆盖数据。记账测试数字全部是合成单元数据，不是模型消费。

见 `LOCAL_VALIDATION.json`。这证明离线实现检查通过，不证明 Codex 集成已运行或 Skill 更有效。

## 运行前必须校准

在已有授权的 Codex 环境中验证：原生 spawn/接收/关闭子 Agent、子线程实际模型与 effort、工具权限、worktree 能力、完整主/子 usage 采集。禁止用嵌套 `codex exec` 冒充原生子 Agent，禁止只为 C 放宽权限。

使用专用 CODEX_HOME、`--ignore-user-config`、相同插件/记忆禁用配置，且检查有效指令是否仍有父目录、管理员或宿主注入。文件夹分开**不是硬读隔离**；正式强隔离试验需要独立容器/权限控制。不要使用有个人敏感文件的工作区。

`preflight` 只检查 CLI、必要参数、登录状态和明显的额外指令路径，不调用模型。`CLI_READY_RUNTIME_CALIBRATION_REQUIRED` 不代表运行时已校准。`run` 可产生功能与 CLI 时间记录，但不会自动认证性能结论。

正常登录即可；不要把凭据发到聊天、GitHub 或提交到 Git。脚本不安装 CLI、不复制 auth.json、不修改全局配置或已安装 Skill：

```bash
CODEX_HOME="$HOME/.codex-goal-benchmark" codex login
python3 evaluations/astra-baseline-v2/runner.py preflight \
  --codex-home "$HOME/.codex-goal-benchmark"
```

专用 home 不应含其他 AGENTS.md、skills、agents 或 hooks。身份状态以 `codex login status` 为准，不保存凭据正文。CLI/宿主变化后要重新校准。

## 先小批验证，再完整 pilot

小批 smoke：3 类 × 3 组 × 1 次 = **9 个端到端样本、12 次父进程执行**；子 Agent 调用另计。以下 `plan` 不调用模型，`run` 会消耗实际账号额度。

```bash
python3 evaluations/astra-baseline-v2/runner.py plan \
  --output /tmp/goal-astra-smoke-v2 \
  --tasks tiny parallel handoff --repeats 1 \
  --model gpt-6-astra --effort xhigh
python3 evaluations/astra-baseline-v2/runner.py run \
  --output /tmp/goal-astra-smoke-v2 \
  --codex-home "$HOME/.codex-goal-benchmark"
```

smoke 验证执行/隔离/遥测后，在**新目录**创建完整 pilot：6 类 × 3 组 × 3 次 = **54 个端到端样本、63 次父进程执行**。这些是计划数，不是已完成数。

```bash
python3 evaluations/astra-baseline-v2/runner.py plan \
  --output /tmp/goal-astra-pilot-v2 --repeats 3 \
  --model gpt-6-astra --effort xhigh
python3 evaluations/astra-baseline-v2/runner.py run \
  --output /tmp/goal-astra-pilot-v2 \
  --codex-home "$HOME/.codex-goal-benchmark"
python3 evaluations/astra-baseline-v2/runner.py report \
  --output /tmp/goal-astra-pilot-v2
```

顶层样本串行，内部可并行。每三轮每组在同一任务中各占一次执行顺序位置，固定排序种子不是模型采样种子。新工作树、新进程，不传入其他组聊天。

每阶段默认 900 秒，冻结前可统一设 `--timeout`。**尚无已验证的全 Agent 硬 token/货币预算闸门**，不要在额度未知时直接启动大批。超时终止本地进程组，不宣称能停止未知宿主的远程孤儿任务。

不覆盖、不挑选性重跑，不抹掉失败。Ctrl-C/失败保留记录；重新执行建立新 campaign。冻结文件变化会拒绝运行。校准、搭建和判卷开销与模型试验分开记录。

## 总 token：账本已实现，运行时 exporter 尚未完成

**已实现：原始 CLI 事件保留和严格请求级汇总器。尚未实现/校准：当前 Codex 宿主完整主/子 request usage 导出适配器。** 仅有 `turn.completed.usage` 时总 token 为 `null`，不是 0，更不是“节省”。

经审阅校准的可信运行时 exporter 可在每个 `phase-N/usage-ledger.json` 写入 `goal-usage-v1`，结构参见 `test_baseline.py::example_ledger()`。示例数字只用于单元测试，绝不能复制成正式结果。账本不得来自模型自估。

正式账本还必须附匹配该次执行的 binding：

```json
{
  "prompt_sha256": "SHA-256 of phase prompt.txt",
  "events_sha256": "SHA-256 of phase events.jsonl",
  "root_thread_ids": ["actual CLI root thread id"],
  "cli_version": "actual preflight CLI version"
}
```

账本包含完整线程树、每线程模型/effort/终止状态、请求 ID 清单、每个请求自己的 input/cached-input/output 增量。父线程已聚合子线程时不得重复相加；重复相同请求仅算一次，冲突、跨阶段/样本复用、缺子线程、未终止、漂移或未知 scope 均拒绝完整记账。缓存输入是 input 子集；reasoning 不重复加入 output。

coverage 声明与 evidence hash 不是自证：还需 exporter 源码、原始记录、宿主版本及校准证据。`COMPLETE_EXPORTED` 只代表导出声明通过结构检查。`telemetry.money()` 仅按明确给定单价计算输入/缓存/输出 token 项，不猜价格、不包含其他费用、不映射订阅额度。

## 判定

先看各任务验收和人工审阅，再看包含失败的全部样本资源；不同完成量不能当成同工作量效率比较。报告分任务/组给出样本数、通过数、CLI 耗时中位数、以及完整采集后才有的 token 中位数。

CLI 时间是父进程观察值，handoff 为两阶段之和，不自动等于全部子线程静止的墙钟时间。孤儿或未结束子任务需额外核对。没有完整用量不输出成本赢家。

C 只优于 A、不优于 B，可能主要是委派提示作用；C 优于 B 才支持额外规则增益；C 更快但 token 更多是资源换时间。三次重复仍是小样本探索，不作统计显著、等效或全场景提升声明。

**真实模型实测完成前，原有性能结论不因离线检查而改变。**

## 官方接口依据（2026-09-16 查阅）

- [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive)
- [Subagents](https://developers.openai.com/codex/subagents)
- [Configuration reference](https://developers.openai.com/codex/config-reference)
- [Authentication](https://developers.openai.com/codex/auth)
