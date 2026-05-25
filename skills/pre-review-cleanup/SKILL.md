---
name: pre-review-cleanup
description: >
  Scan the project for template placeholders, leftover scaffolding code,
  unnecessary boilerplate files, and stale configuration. Run this before
  code review to ensure no template artifacts ship to production. Triggers
  include "clean up template files", "pre-review cleanup", "remove boilerplate",
  "scaffolding cleanup", "clean before review".
---

# Skill: Pre-Review Cleanup

Scan the project for template artifacts, scaffold leftovers, and unnecessary
files before opening a PR. **Nothing is deleted without confirmation.**

---

## Scan Categories

### 1. Placeholder Patterns in Documents

Search all markdown files (CLAUDE.md, README.md, docs/*.md) for:

| Pattern | Example |
|---|---|
| `[PLACEHOLDER]` style brackets | `[PROJECT_NAME]`, `[REPO_URL]`, `[DATE]`, `[WHO]` |
| Unfilled template fields | `**Status:**` with generic value, empty `- [ ]` checkboxes |
| Template boilerplate text | "Replace all `[PLACEHOLDERS]` before committing" |

**Action:** List all found placeholders. Replace with real values or remove
the template stub.

### 2. Scaffold Boilerplate in Code

Search source files for comments and patterns that clearly belong to a template:

- Comments containing `replace this`, `override this`, `your actual`, `example`
- Routes returning `501 Not Implemented` or `raise HTTPException(status_code=501)`
- Functions with bodies that are just `pass`, `...`, or `raise NotImplementedError`
- Classes with names like `Engine`, `BaseService` that only contain a docstring
- Empty or near-empty service directories (e.g., `backend/src/services/` with
  only `__init__.py`)

**Action:** Present a table of findings. Ask the user which to implement,
replace, or delete.

### 3. Unused / Unnecessary Files

| File / Pattern | Why It Might Be Unnecessary |
|---|---|
| `docker/Dockerfile.cuda*` | Project doesn't need GPU containers |
| `docker/Dockerfile.rocm` | Project doesn't use AMD GPUs |
| `docker/Dockerfile.jetson` | Project doesn't target Jetson |
| `docker/compose.cuda.yml` | GPU compose overlay not needed |
| `docker/compose.rocm.yml` | GPU compose overlay not needed |
| `backend/src/models/user.py` | Starter User model may not fit the project |
| `backend/src/api/routes/auth.py` | Starter auth routes, may be unused |
| `backend/src/utils/security.py` | Starter JWT/bcrypt helpers, may be unused |
| Unused test fixtures | Tests for removed template features |
| `.github/workflows/` (bad CI) | CI config that doesn't match actual stack |

**Action:** Present each file with context. Ask before deleting.

### 4. Environment Configuration

- `.env.example` exists but no `.env` — suggest copying
- `.env` is checked into git — warn (should be in `.gitignore`)
- Missing required env vars defined in configs/*.yaml

**Action:** Present findings, suggest fixes.

### 5. Stale Configuration

- `backend/configs/default.yaml` — does the config match the actual project?
- `Makefile` targets that reference non-existent scripts
- `docker-compose.yml` services for components the project doesn't use

**Action:** Present findings, suggest edits.

---

## Output Format

At the end, produce a summary:

```markdown
## Pre-Review Cleanup Summary

### Items Resolved
- [x] Replaced `[PROJECT_NAME]` with "My Service" in CLAUDE.md
- [x] Deleted unused `docker/Dockerfile.cuda124` (CPU-only project)
- [x] Created `.env` from `.env.example`

### Needs Follow-Up
- [ ] `backend/src/core/engine.py` — `Engine.run()` body is still template text
- [ ] `backend/src/api/routes/auth.py` — 3 endpoints return 501

### Skipped (User Decision)
- `docker/Dockerfile.rocm` — kept for future AMD GPU support
```

After cleanup, recommend running `/review` for a full code review.