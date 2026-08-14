---
name: codemax-gbrain
description: >-
  Fold the shared gbrain brain into the normal dev loop: pull the requirement,
  blueprint, and ADR traced from the branch's GitHub issue at task start, and
  push updated living-docs to gbrain (via codemax sync) at task end — so
  context is always present without manually querying gbrain. Triggers include
  "pick up a task", "start this task", "sync docs to gbrain", "what context
  exists for this branch", "codemax", "gbrain", and any task whose branch has a
  GitHub issue or references a requirement, blueprint, or ADR.
---

# Skill: CodeMAX / gbrain Workflow

> **Optional.** This skill only applies if your team runs a CodeMAX instance /
> exposes a shared gbrain brain. If you don't use CodeMAX, skip it entirely —
> it changes nothing and nothing breaks. Enable the session-start integration
> by setting `CODEMAX_ENABLED=1` and the `CODEMAX_WIKI_DIR` / `CODEMAX_GBRAIN_DIR`
> paths to your own deployment.

**When to invoke:** At the start of a task whose branch has a GitHub issue
(the `writing-plans` skill creates one after `/plan`, labeled `codemax`, body =
the plan), or that references a requirement, blueprint, or ADR — to pull the
traced context into the session. And at the end of a task, before `/pr`, to push
updated living-docs back to gbrain. Also invoke on any explicit "sync" or
"query gbrain" request.

---

## Mental model

gbrain is a **source of truth**, not a workflow tool. You do NOT query it
continuously. You touch it at exactly two points:

1. **Pull** — at task start, load the requirement/blueprint/ADR the branch's
   GitHub issue traces to, so you have the real context in-flow.
2. **Push** — at task end, update the living-doc status and run `codemax sync`
   so the brain reflects what was actually built.

Everything in between is normal dev work in the repo (CLAUDE.md carries the
standing contract; living-docs carry the product state).

---

## Pull — at task start

The entry point is the **GitHub issue for this branch** — the session-start
hook detects it (same lookup as `create-issue.sh`), and the issue body holds the
plan that traces to requirement / blueprint / ADR pages in the living-docs wiki:

```bash
# 1. Find the issue for this branch (label codemax, branch in the body)
gh issue list --repo "$REPO" --search "label:codemax in:body ${BRANCH}" \
  --json number,title,body --jq '.[0]'

# 2. Read the plan in the issue body, then the requirement/blueprint/ADR pages
#    it references — they're linked pages in wiki/platforms/<name>/:
#    grep -rl "requirement\|blueprint\|ADR" wiki/platforms/<name>/ 2>/dev/null
```

If there's no issue for the branch yet (plan not written), or the plan has no
traced context, say so and proceed with what's in the repo — do not fabricate a
requirement.

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
# Update the living-doc status (task → done, etc.) in the repo
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
- **The task status moves** `todo → in_progress → review → done` as you
  progress, and this is reflected in the living doc before sync.
- **Static docs live in CLAUDE.md / AGENTS.md**; only *product state* lives in
  living-docs → gbrain. Don't sync the standing contract.

---

## Verification

- [ ] At task start: pulled the requirement/blueprint/ADR the branch's issue traces to
- [ ] At task end: task status updated in the living doc
- [ ] `codemax sync run` executed and pages appear in gbrain
- [ ] No fabricated context; missing context surfaced to the human
- [ ] Structural changes opened as a PR, not pushed to main