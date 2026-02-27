# Git Workflow

## Daily Flow

1. Pull latest changes.
2. Pick one task from `docs/BACKLOG.md` and set it to `doing`.
3. Follow `docs/ARCHITECTURE_RULES.md` for file placement and size guardrails.
4. Commit in small chunks (one logical change per commit).
5. Mark task `done` only after verification.

## Command Cheatsheet

```bash
git status
git add -p
git commit -m "feat(backend): add request id middleware"
git log --oneline --decorate -20
```

## Commit Format

Use:

`<type>(<scope>): <summary>`

Examples:
- `feat(frontend): redesign answer panel`
- `fix(backend): update langchain import path`
- `chore(docs): add eval tracking template`

Types:
- `feat` new feature
- `fix` bug fix
- `refactor` structure change without behavior change
- `chore` tooling/docs/housekeeping
- `test` add or update tests

## Definition of Done

- Code updated
- Basic run/build check passed
- `python scripts/check_architecture.py` passed
- `docs/WORKLOG.md` updated
- `docs/BACKLOG.md` status updated
- `docs/DECISIONS.md` updated when architecture direction changes
- If task touched workflow/rules, sync `docs/GIT_WORKFLOW.md` and `docs/ARCHITECTURE_RULES.md`
