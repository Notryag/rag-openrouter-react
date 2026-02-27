# AI Prompt Template

Copy this template when asking AI to implement work in this repo.

```md
目标：
完成 BACKLOG 里的这项任务：<task name>

执行要求：
0. 先读取 AGENTS.md 和 docs/ARCHITECTURE_RULES.md
1. 先读取 docs/BACKLOG.md、docs/WORKLOG.md、docs/DECISIONS.md、docs/EVAL.md
2. 把对应任务改为 doing
3. 直接修改代码并完成最小可运行验证
4. 运行 python scripts/check_architecture.py
5. 更新 docs/WORKLOG.md（Goal/Change/Result/Risk/Next）
6. 如果有架构取舍，更新 docs/DECISIONS.md
7. 如果是 RAG 质量改动，更新 docs/EVAL.md
8. 最后给我：
   - 变更文件列表
   - 运行过的验证命令和结果
   - 建议的 git commit message（按 conventional commits）

约束：
- 不要做无关重构；新增代码必须按分层目录放置
- 失败时给出阻塞点和下一步可执行方案
```

## Quick Command Prompt

```md
按 docs/GIT_WORKFLOW.md 和 docs/ARCHITECTURE_RULES.md 执行今天第一项任务，完成后同步更新四个 docs 文件，并输出建议的提交命令。
```
