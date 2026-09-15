# Goal Orchestration

让 Codex 在复杂任务中主动寻找适合子 Agent 的工作，协调分工并整合结果。

适合多模块开发、重构迁移，以及需要独立调查或审阅的任务。小改动可以直接交给 Codex，不必启用这个 skill。

## 安装与更新

在 Codex 中发送下面这句话，安装和更新都用它：

```text
请将 https://github.com/Yangyang96/goal-orchestration 仓库中的 goal-orchestration skill 安装或更新到我的 Codex。
```

## 使用

描述目标时加上 `$goal-orchestration`：

```text
用 $goal-orchestration 完成这次重构：把订单校验从接口层移到独立模块，保持现有 API 行为不变，并通过相关测试。
```

Codex 会寻找能并行推进的工作或有价值的独立审阅，安排子 Agent，并检查、整合返回的结果。已有工作跨会话续接时，会核对产物与进度，避免重复分派。

只有你显式调用时才会启用。是否分派取决于实际收益；拆分成本更高时，Codex 会说明原因并直接完成。

## 许可

[MIT](LICENSE)
