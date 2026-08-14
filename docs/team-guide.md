# Team Collaboration Guide

This guide walks through how a team of engineers uses tapway-superpowers to work on the same repository in parallel — each person owning a different work package — from a single feature idea all the way to merged PRs.

---

## ⚙️ One-Time Setup (do this ONCE per machine)

Set these environment variables **once** in your shell profile (`~/.bashrc` or `~/.zshrc`). They persist across all repos and all sessions — you never re-export them per project.

```bash
# --- CodeMAX connection (one-time, persistent) ---
export CODEMAX_ENABLED=1                     # Turns on the CodeMAX/session hooks
export CODEMAX_API_URL="http://47.250.116.35:8125"   # CodeMAX panel
export CODEMAX_GBRAIN_MCP="http://47.250.116.35:8100" # gbrain wiki/knowledge
export CODEMAX_ADMIN_TOKEN="<admin-token>"   # kanban/admin auth
export GBRAIN_TOKEN="<gbrain-token>"         # brain/auth
export GITHUB_TOKEN="<github-token>"         # issue sync + poller

source ~/.bashrc   # (or ~/.zshrc)
```

> **Why once?** Exported environment variables are process-wide, not directory-scoped. They apply to every repo you open in that shell. A new terminal inherits them from the profile, so you never set them per-project unless you specifically want a different endpoint per repo.

> **Hermes users:** put the same values in `~/.hermes/.env` instead of the shell profile.

### How the coding agent pulls context from the shared brain (CodeMAX/gbrain)

When CodeMAX is enabled, the coding agent pulls task context by **connecting to the gbrain MCP server** (the `CODEMAX_GBRAIN_MCP` URL) and querying it. It uses the brain tools (`search`, `get_page`, `list_pages`) to load the requirement / blueprint / ADR that your work order traces to — so it knows *what* it's building and *why*, not just the repo-local code. Nothing to install per-project: connect your tool once.

> **Canonical connect steps live in the CodeMAX side** — `DEVELOPER_ONBOARDING.md`, Step 2 (get your `GBRAIN_TOKEN`, then register the gbrain MCP server: `claude mcp add` for Claude Code, `mcp_servers` in `config.yaml` for Hermes, `.vscode/mcp.json` for Cline/Roo), and Step 3 to verify. ℹ️ **CodeMAX is a private repo for ITMAX teams only (at the moment)** — CodeMAX users, follow `https://github.com/tapway/codemax/blob/master/docs/DEVELOPER_ONBOARDING.md`. For a quick reference, registering is one MCP server named `gbrain` pointed at `$CODEMAX_GBRAIN_MCP/mcp` with a bearer token, then `curl -s "$CODEMAX_API_URL/api/v1/brain/search?q=<topic>&limit=5" -H "Authorization: Bearer $GBRAIN_TOKEN"` should return matching pages.

### Enforcement: making the agent actually search the brain

The `codemax-gbrain` skill tells the agent to pull context, and the session-start hook *hints* at it — but both are advisory. An agent can skip the brain and work from repo-local context alone. If you want context-pull **enforced** rather than requested, there are two binding hooks (both available in Hermes' shell-hook system in `~/.hermes/config.yaml`):

1. **`pre_llm_call` — inject the search results directly into the prompt.** This is the strongest guarantee: the hook queries gbrain for the WO-* context and returns `{"context": "<brain snippet>"}`, so the search results are *physically in front of the model* on every turn — it cannot omit them.
2. **`pre_tool_call` — block work until the brain was searched.** When a `WO-*` is present, a `pre_tool_call` gate refuses the first code-editing tool call unless the session already pulled brain context, forcing the agent to do the lookup first.

Either way the agent is instructed to **"search the brain"** before implementing — via the injected context (enforced) or via the `codemax-gbrain` skill (advisory fallback when no hook wiring exists).

### What the session-start hook does automatically

When you open Claude Code (or start a Hermes session) in a repo, the **SessionStart hook fires automatically** — you don't invoke it and you don't say anything special. It:

1. Prints the current branch, last commits, and git status
2. Checks for open TODOs in `CLAUDE.md`
3. **If `CODEMAX_ENABLED=1`:** detects the work order (WO-*) from the branch or `CLAUDE.md` and tells you gbrain context is available
4. **If you're on a feature branch (with `gh` installed):** checks for a GitHub issue for that branch, and reports the number if one exists. The actual issue is created later — after the brainstorming/plan step, hydrated with the plan content (see the Writing Plans skill).

So the flow is: **open the repo → the hook does the bookkeeping → just start talking about your task.** No special incantation needed.

---

## 🚀 The Direct Workflow (start here)

This is the day-to-day flow for a single engineer turning a feature idea into a merged PR. It's fully **conversational** — you tell the agent what you want, and it drives the plan → GitHub issue → execution pipeline for you.

```
Start (hook detects)
   │
   ▼
Brainstorm / Interview  →  plan written (docs/plans/*.md)
   │
   ▼
Create GitHub issue from plan   ←  the key step (after plan, before code)
   │                         mirrors to CodeMAX kanban via webhook
   ▼
Execute (tdd / autoship)  →  progress updates pushed to issue
   │
   ▼
/pr  →  PR merged, issue marked done, kanban card = done
```

### Step-by-step

1. **Open the repo and start a session** (Claude Code or Hermes). The hook prints your branch and tells you if a GitHub issue already exists. Nothing to do — just start talking.

2. **Brainstorm / get interviewed.** Talk it out conversationally:
   > "I want to add JWT auth. Let me brainstorm the approach."
   
   The agent explores options and saves the output to `docs/brainstorming/[topic].md`.

3. **Write the plan.** The agent produces `docs/plans/[feature].md` (+ checklist) and commits it. **This is the key step** — the plan is what becomes the GitHub issue.

4. **Create the GitHub issue (automatic, after the plan).** Right after the plan is committed and *before* any code runs, the agent creates the GitHub issue — with the full plan as the body. This is what the CodeMAX kanban mirrors. You don't need to ask; the writing-plans skill does it automatically (or via `create-issue.sh`).

5. **Execute.** `tdd` / `autoship` implement the plan. Every step pushes a progress update to the GitHub issue (`in_progress → review`), which the webhook mirrors to the kanban board.

6. **Open the PR.** `/pr` builds the PR, updates the issue to `done`, and the kanban card reflects `done`.

### The two key timing rules

| Rule | Why |
|---|---|
| **Issue is created AFTER the plan, BEFORE execution** | An issue created at session start (from just the branch name) is an empty, worthless ticket. Wait until the plan has real content. |
| **The hook never creates issues on its own** | The SessionStart hook only *detects* existing issues. Creation is always driven by the plan step. |

### What you actually say (zero ceremony)

```text
# Just be conversational:
"Let's build JWT auth for next-app. Start with brainstorming."
# → agent brainstorms, writes plan, creates the GitHub issue, then implements
```

No special commands, no remembering to "create the issue." The agent handles it at the right time.

---

## The Mental Model

Each feature is split into **work packages by discipline** (Backend, Frontend, DevOps, QA). Each engineer:

- Owns one package
- Works in an **isolated git worktree** (a separate directory, same repo)
- Implements with `/autoship` or `/tdd`, then exits through `/pr`
- Never touches `main` directly

The plan and checklist live in `docs/` and are committed immediately — they are the shared coordination layer. There are no Slack threads saying "what are you working on" — the checklist is the answer.

```
main repo/
  docs/
    brainstorming/user-auth.md    ← why we chose this approach
    plans/user-auth.md            ← what we're building
    checklists/user-auth.md       ← who owns what, current status
  backend/...
  frontend/...

../samurai-user-auth-backend/     ← Bob's worktree
../samurai-user-auth-frontend/    ← Charlie's worktree
../samurai-user-auth-devops/      ← Alice's worktree
```

---

## The Scenario

**Feature:** JWT-based user authentication — login endpoint, token refresh, and a protected route in the frontend.

**Team:**
- **Alice** — Tech Lead. Runs brainstorming and planning, then picks up the DevOps package.
- **Bob** — Backend engineer. Takes the Backend package.
- **Charlie** — Frontend engineer. Takes the Frontend package.

They all work in parallel after the plan is committed.

---

## Phase 1 — Alice: Brainstorm and Plan (once per feature)

Alice does this alone. It takes about 15 minutes.

### Step 1: Brainstorm

Alice opens Claude Code in the main repo and runs:

```
/brainstorming

I want to add JWT authentication to our FastAPI + Next.js app.
Users should be able to log in, get a token, refresh it, and access
protected routes. What are the options?
```

Claude explores approaches (session cookies vs JWT, where to store tokens, refresh strategy). Alice picks the approach. The output is saved automatically:

```bash
docs/brainstorming/user-auth-jwt.md
# committed automatically by the skill
```

### Step 2: Write the Plan

```
/plan

Based on the brainstorming above, write an implementation plan for
JWT auth. Backend: FastAPI. Frontend: Next.js 14. Include test criteria
for every task and break it into Backend, Frontend, and DevOps packages.
```

Claude generates `docs/plans/user-auth.md` (the full task breakdown) and `docs/checklists/user-auth-checklist.md` (the work package table). Both are committed and pushed.

The checklist looks like this after Alice's work:

```markdown
# Work Package Checklist: User Auth (JWT)
**Plan:** docs/plans/user-auth.md
**Branch:** feat/user-auth
**Status:** 🔴 Not started

---

## 🔧 Backend (Python FastAPI)
**Assignee:** _(unassigned)_
- [ ] Task 1: Create `UserService.authenticate(email, password) → AuthToken`
- [ ] Task 2: Create `POST /auth/login` endpoint
- [ ] Task 3: Create `POST /auth/refresh` endpoint
- [ ] Task 4: Add `get_current_user` dependency for protected routes

## 🎨 Frontend (Next.js / TypeScript)
**Assignee:** _(unassigned)_
- [ ] Task 5: Create `authService.login(email, password)` client
- [ ] Task 6: Create `LoginForm` component with validation
- [ ] Task 7: Add auth token to API request headers
- [ ] Task 8: Protect `/dashboard` route — redirect to login if no token

## 🚀 DevOps / Infrastructure
**Assignee:** _(unassigned)_
- [ ] Task 9: Add `JWT_SECRET` to `.env.example` and deployment config
- [ ] Task 10: Add auth endpoint smoke test to CI pipeline

## 🧪 QA / Integration
**Assignee:** _(unassigned)_
- [ ] Task 11: Write E2E login flow test (Playwright)
```

### Step 3: Notify the Team

Alice shares the checklist link in Slack:
> "Auth plan is done: `docs/checklists/user-auth-checklist.md` — grab a package and self-assign."

---

## Phase 2 — Parallel Work (Bob, Charlie, Alice simultaneously)

All three work at the same time. Their worktrees are completely independent.

---

### Bob — Backend Package

**Bob opens Claude Code in the main repo and claims his package:**

```bash
# In the main repo
git pull origin main
```

Bob edits `docs/checklists/user-auth-checklist.md`:
```markdown
## 🔧 Backend (Python FastAPI)
**Assignee:** @bob   **Status:** 🟡 In progress
```

```bash
git add docs/checklists/user-auth-checklist.md
git commit -m "chore: self-assign backend work package for user-auth"
git push origin main
```

**Bob creates his worktree:**

```bash
git worktree add -b feat/user-auth-backend ../samurai-user-auth-backend origin/main
cd ../samurai-user-auth-backend
claude
```

**Bob tells Claude:**

```
I'm picking up the Backend work package for the user-auth feature.
My tasks are in docs/checklists/user-auth-checklist.md (Tasks 1–4).
The plan is at docs/plans/user-auth.md.
Implement it with autopilot.
```

Claude reads the plan, validates every task (exact file paths, verifiable criteria), then runs the full loop automatically:

```
## Autoship Status: User Auth — Backend
| Task | Status | Commit |
|---|---|---|
| Task 1: UserService.authenticate() | 🔄 In progress | — |
| Task 2: POST /auth/login | ⏳ Pending | — |
| Task 3: POST /auth/refresh | ⏳ Pending | — |
| Task 4: get_current_user dependency | ⏳ Pending | — |
```

~25 minutes later, Bob sees:

```
## Autoship Complete ✅
Tasks completed: 4/4
Running: /simplify → /review → /pr ...

PR #14 opened: feat(auth): add JWT login, refresh, and auth dependency
```

Bob's done. He didn't write a single line of code manually.

---

### Charlie — Frontend Package

**Charlie is working at the same time as Bob, in a different directory.**

Charlie opens the main repo, claims the frontend package:

```bash
git pull origin main
```

Edits `docs/checklists/user-auth-checklist.md`:
```markdown
## 🎨 Frontend (Next.js / TypeScript)
**Assignee:** @charlie   **Status:** 🟡 In progress
```

```bash
git add docs/checklists/user-auth-checklist.md
git commit -m "chore: self-assign frontend work package for user-auth"
git push origin main
```

**Creates worktree:**

```bash
git worktree add -b feat/user-auth-frontend ../samurai-user-auth-frontend origin/main
cd ../samurai-user-auth-frontend
claude
```

**Charlie tells Claude:**

```
I'm picking up the Frontend work package for user-auth.
Tasks 5–8 from docs/checklists/user-auth-checklist.md.
Implement it with autopilot.
```

> **Note:** Charlie's frontend tasks (Tasks 5–8) don't touch any of Bob's backend files. There's no conflict — they're working on completely different parts of the codebase.

Charlie's autoship runs independently. The only thing Charlie needs from Bob is the API contract (the endpoint shape), which was documented in the plan. If the backend isn't merged yet, Charlie can mock the API call and note it in the PR.

~30 minutes later, PR #15 opens:
```
feat(auth): add login form, auth service client, and dashboard route protection
```

---

### Alice — DevOps Package

Alice works in the same main repo where she ran the plan (or opens a new worktree):

```bash
git worktree add -b feat/user-auth-devops ../samurai-user-auth-devops origin/main
cd ../samurai-user-auth-devops
claude
```

```
I'm picking up the DevOps package for user-auth.
Tasks 9–10 from docs/checklists/user-auth-checklist.md.
Let's start implementing.
```

Alice's tasks are config changes (`JWT_SECRET` in `.env.example`, CI smoke test) — quick and safe to run in parallel with Bob and Charlie since they touch different files entirely.

Alice uses manual `/tdd` since it's only 2 tasks:

```
/tdd
```

When done:
```
/simplify
/review
/pr
```

PR #16 opens:
```
chore(infra): add JWT_SECRET to env config and auth smoke test to CI
```

---

## Phase 3 — Code Review and Merge

Now there are three open PRs: #14 (backend), #15 (frontend), #16 (devops).

**Suggested merge order:**
1. **PR #16 (DevOps)** first — no dependencies, unblocks CI for the others
2. **PR #14 (Backend)** second — frontend needs the API to be in `main` for final integration testing
3. **PR #15 (Frontend)** last — after backend is merged, Charlie rebases and verifies the real API works

Code review is done inside the AI agent (not in GitHub CI). Each PR is already self-reviewed by its implementing agent (`/simplify → /review → /pr`) before it's opened, so reviewers get a clean, simplified diff. Teammates review on GitHub in the normal way.

### What if Frontend PR needs rebasing after Backend merges?

Charlie runs this inside the frontend worktree:

```bash
# in ../samurai-user-auth-frontend
git fetch origin
git rebase origin/main
```

If conflicts appear:

```
claude "resolve the conflict — preserve Charlie's auth header injection and Bob's token endpoint URL from main"
```

Then push the resolved branch:

```bash
git push --force-with-lease
```

---

## The Checklist at the End

After all three PRs merge, the checklist shows the full picture:

```markdown
# Work Package Checklist: User Auth (JWT)
**Status:** 🟢 Done

## 🔧 Backend
**Assignee:** @bob   **PR:** #14   **Status:** 🟢
- [x] Task 1: UserService.authenticate()
- [x] Task 2: POST /auth/login
- [x] Task 3: POST /auth/refresh
- [x] Task 4: get_current_user dependency

## 🎨 Frontend
**Assignee:** @charlie   **PR:** #15   **Status:** 🟢
- [x] Task 5: authService.login() client
- [x] Task 6: LoginForm component
- [x] Task 7: Auth token in API headers
- [x] Task 8: Protected /dashboard route

## 🚀 DevOps
**Assignee:** @alice   **PR:** #16   **Status:** 🟢
- [x] Task 9: JWT_SECRET in .env.example
- [x] Task 10: CI smoke test
```

---

## Common Scenarios

### "I want to claim a package but the checklist hasn't been pushed yet"

Ask the tech lead to push the plan first. The checklist must be in `main` before anyone creates a worktree — otherwise you're branching off stale state.

### "My package depends on Bob's — do I wait?"

Partially. You can:
- Implement everything up to the integration point using a **mock** of Bob's API
- Note the mock in your PR: `// TODO: replace mock once PR #14 merges`
- After #14 merges, rebase your branch, swap the mock for the real call, and push

### "Two people accidentally touched the same file"

This is a conflict to resolve at rebase time. Run inside your worktree:

```bash
git fetch origin && git rebase origin/main
# if conflict:
claude "resolve conflict in frontend/src/app/layout.tsx — keep both the auth header from my branch and the nav changes from main"
git add frontend/src/app/layout.tsx
git rebase --continue
git push --force-with-lease
```

### "I finished early and want to pick up someone else's package"

Only do this if the original assignee has explicitly dropped it (updated checklist to 🔴 and unassigned themselves). Don't work on a 🟡 package that belongs to someone else — two people on the same branch causes conflicts.

### "I want to review a teammate's PR without running Claude Code"

Just review it on GitHub normally. The implementing agent has already self-reviewed the diff before the PR was opened, so the code reaching GitHub is simplified and reviewed — no GitHub Actions review or `@claude` tagging is involved.

### "The plan was wrong — a task needs to change mid-implementation"

1. Update `docs/plans/user-auth.md` with the corrected task
2. Commit the plan change: `git commit -m "docs: correct task 3 — refresh token should be stored in httpOnly cookie not localStorage"`
3. Continue implementation

The plan is a living document during implementation, not a contract.

---

## Quick Reference

### Tech Lead (once per feature)
```bash
# In main repo, Claude Code open
/brainstorming    # → docs/brainstorming/[topic].md
/plan             # → docs/plans/[feature].md + docs/checklists/[feature]-checklist.md
# then notify team
```

### Each Team Member (per package)
```bash
# 1. Claim your package
git pull origin main
# edit docs/checklists/[feature]-checklist.md — set your name + 🟡
git add docs/checklists/ && git commit -m "chore: self-assign [package]" && git push

# 2. Create worktree
git worktree add -b feat/[feature]-[package] ../[project]-[package] origin/main
cd ../[project]-[package] && claude

# 3. Tell Claude (autopilot mode)
"I'm picking up the [Backend/Frontend/DevOps/QA] work package for [feature].
 Tasks N–M in docs/checklists/[feature]-checklist.md. Implement it with autopilot."

# 4. Manual mode (step by step)
/tdd              # implement each task
/simplify         # reduce complexity
/review           # self code-review
/pr               # push + open PR + update checklist

# 5. Cleanup after merge
cd ../[main-repo]
git worktree remove ../[project]-[package]
git worktree prune
```

### Merge Order Rule
DevOps → Backend → Frontend (most to least likely to be depended upon)

---

## Why This Works

| Problem | How the workflow solves it |
|---|---|
| "What is everyone working on?" | Checklist in `docs/checklists/` — always current |
| "Why did we build it this way?" | Brainstorming output in `docs/brainstorming/` |
| "The PR has no context" | `/pr` generates a structured body with summary, test plan, files changed |
| "I accidentally broke main" | Hooks block direct commits to `main`; `/pr` runs tests before push |
| "Two people conflicted on the same file" | Worktrees isolate branches; rebase with intent-aware conflict resolution |
| "The PR is messy / overcomplicated" | `/simplify` runs before every PR |
| "I don't know if this actually works" | `/verification` and `/verify` run the app before declaring done |
