---
name: codemax-gbrain
description: >-
  Fold the shared gbrain brain into the normal dev loop: pull the requirement,
  blueprint, and ADR that a work order traces to at task start, and push updated
  living-docs to gbrain (via codemax sync) at task end — so context is always
  present without manually querying gbrain. Triggers include "pick up a work
  order", "start this task", "sync docs to gbrain", "what context exists for WO-*",
  "codemax", "gbrain", and any task that references a WO-*, requirement, or blueprint.
---

# Skill: CodeMAX / gbrain Workflow

> **Optional.** This skill only applies if your team runs a CodeMAX instance /
> exposes a shared gbrain brain. If you don't use CodeMAX, skip it entirely —
> it changes nothing and nothing breaks. Enable the session-start integration
> by setting `CODEMAX_ENABLED=1` and the `CODEMAX_WIKI_DIR` / `CODEMAX_GBRAIN_DIR`
> paths to your own deployment.

**When to invoke:** At the start of a task that references a work order
(`WO-*`), requirement, or blueprint — to pull the traced context into the
session. And at the end of a task, before `/pr`, to push updated living-docs
back to gbrain. Also invoke on any explicit "sync" or "query gbrain" request.

---

## Mental model

gbrain is a **source of truth**, not a workflow tool. You do NOT query it
continuously. You touch it at exactly two points:

1. **Pull** — at task start, load the requirement/blueprint/ADR the work order
   traces to, so you have the real context in-flow.
2. **Push** — at task end, update the living-doc status and run `codemax sync`
   so the brain reflects what was actually built.

Everything in between is normal dev work in the repo (CLAUDE.md carries the
standing contract; living-docs carry the product state).

---

## Pull — at task start

When picking up a work order, get its traced context from gbrain:

```bash
# 1. Find the work order in the living-docs repo
#    (living-docs live in the repo, usually wiki/platforms/<platform>/work-orders/)
grep -rl "WO-<id>" wiki/ 2>/dev/null

# 2. Read the requirement + blueprint it traces to (they're linked pages)
#    Read the work-order file to see its "Traces to:" line, then read those
#    linked pages for the full context.

# 3. Alternatively, query gbrain directly via MCP (if registered):
#    claude mcp get gbrain   → confirm it's connected
```

If the work order references gbrain/MCP for context, use the registered MCP
server (see the `gbrain` MCP server from `claude mcp list`). If the work order
doesn't exist or has no traced context, say so and proceed with what's in the
repo — do not fabricate a requirement.

**Rule:** Pull context once, use it in-flow. Do not keep re-querying gbrain
during the task.

---

## Push — at task end (before /pr)

**Route before you sync.** Before pushing docs to gbrain, decide which of the
docs this task produced belong in the wiki/brain vs. the repo's own docs (see
the `writing-plans` **7c. Route the docs the plan produces** step and the brain
wiki's `CONTRIBUTING.md` "Wiki vs. repo docs" section). Sync only the
wiki-worthy ones; repo-locked docs (README/ARCHITECTURE/API) stay in the repo
and are not pushed here.

**Read-only / no CodeMAX?** If the wiki isn't writable (or CodeMAX is off),
still route the docs but do **not** push to gbrain — update the repo docs and
move on; a blocked wiki write must never block the pipeline.

When the work is done and you're about to open a PR, sync the living docs back
to gbrain so the brain stays current:

```bash
# Update the living-doc status (work order → done, etc.) in the repo
# then sync the wiki ↔ gbrain lockstep (use your deployed wiki dirs):
codemax sync run --wiki-dir "$CODEMAX_WIKI_DIR" --gbrain-dir "$CODEMAX_GBRAIN_DIR"
```

Verify the sync landed:

```bash
codemax sync run --wiki-dir "$CODEMAX_WIKI_DIR" --gbrain-dir "$CODEMAX_GBRAIN_DIR"   # re-run, idempotent
gbrain list -n 5   # confirm recent pages appear
```

If `codemax` is not installed, fall back to the gbrain MCP `put_page` tool (if
the server is registered) or note that sync must be run by someone with the CLI.

---

## Rules

- **Pull once, push once.** Don't query gbrain continuously mid-task.
- **Never fabricate a requirement/blueprint.** If the traced context is missing,
  say so and ask the human — don't invent one.
- **Living docs are a shared repo.** Structural changes (new requirements,
  blueprints, ADRs) land on a feature branch as a PR, not directly on `main`.
- **The work order status moves** `todo → in_progress → review → done` as you
  progress, and this is reflected in the living doc before sync.
- **Static docs live in CLAUDE.md / AGENTS.md**; only *product state* lives in
  living-docs → gbrain. Don't sync the standing contract.

---

## Verification

- [ ] At task start: pulled the requirement/blueprint/ADR the WO traces to
- [ ] At task end: work-order status updated in the living doc
- [ ] `codemax sync run` executed and pages appear in gbrain
- [ ] No fabricated context; missing context surfaced to the human
- [ ] Structural changes opened as a PR, not pushed to main