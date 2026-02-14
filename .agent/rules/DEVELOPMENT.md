---
trigger: local_development
---

# DEVELOPMENT.md - Local Project Operations

Local operating rules for `C:\Projetos_BI\BI_Solution`.

## Objectives
1. Keep changes local-first and reproducible.
2. Standardize agent/workflow usage.
3. Enforce validate-before-finish.

## Agent Routing Defaults
- Planning/discovery: `project-planner`, `explorer-agent`
- Backend/API: `backend-specialist`
- Frontend/UI: `frontend-specialist`
- Tests/quality: `test-engineer`, `qa-automation-engineer`
- Security/auth: `security-auditor`
- Multi-domain tasks: `orchestrator`

## Workflow Defaults
1. `/plan` before major multi-file work.
2. `/debug` for runtime failures.
3. `/enhance` for incremental changes.
4. `/test` before finalizing.
5. `/orchestrate` when 3+ domains are involved.

## Validation Gate (Mandatory)
Run before considering a task complete:
1. `python -m pytest -q` (or scoped pytest when agreed)
2. `cd frontend-solid && npx playwright test` for UI/runtime flows
3. `python .agent/scripts/checklist.py .` for consolidated checks

## Reporting
- Always report what was changed, what passed, and what is pending.
- If full suite fails due legacy/pre-existing constraints, state exact failing modules.
