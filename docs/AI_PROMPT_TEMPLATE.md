# AI Prompt Template

Copy this template when asking AI to implement work in this repo.

```md
目标：
完成 BACKLOG 里的这项任务：<task name>

执行要求：
0. 必读：先读取 AGENTS.md 和 docs/ARCHITECTURE_RULES.md
1. 先读取 docs/BACKLOG.md，定位今天要做的那一项
2. 其他文档按需读取，不要默认全量展开：
   - docs/WORKLOG.md：只看最近 1-3 条相关记录
   - docs/DECISIONS.md：只看与当前任务相关的 ADR
   - docs/EVAL.md：仅在涉及 RAG 质量、检索、生成链路、模型切换时读取
3. 把对应任务改为 doing（如果它原本不是 done）
4. 直接修改代码并完成最小可运行验证
5. 运行 python scripts/check_architecture.py
6. 更新 docs/WORKLOG.md（Goal/Change/Result/Risk/Next）
7. 如果有新的架构取舍或约束变化，更新 docs/DECISIONS.md
8. 如果是 RAG 质量改动，更新 docs/EVAL.md
9. 完成后把 BACKLOG 状态改为 done
10. 最后给我：
   - 变更文件列表
   - 运行过的验证命令和结果
   - 建议的 git commit message（按 conventional commits）

约束：
- 不要做无关重构；新增代码必须按分层目录放置
- 优先最小上下文：先搜索定位，再读取必要文件或必要片段
- 不要为了“保险”一次性读取所有 docs
- 失败时给出阻塞点和下一步可执行方案
```

## Minimal Task Prompt

```md
按 AGENTS.md 与 docs/ARCHITECTURE_RULES.md 执行 BACKLOG 中今天第一项任务。

要求：
- 先只读必要文档；其余 docs 按需读取，不要全量加载
- 完成代码修改与最小验证
- 运行 python scripts/check_architecture.py
- 同步更新相关 docs（至少 BACKLOG、WORKLOG；其余按需）
- 输出变更文件、验证结果、建议提交命令
```

## Quick Command Prompt

```md
按 docs/GIT_WORKFLOW.md 和 docs/ARCHITECTURE_RULES.md 执行今天第一项任务，完成后同步更新四个 docs 文件，并输出建议的提交命令。
```
