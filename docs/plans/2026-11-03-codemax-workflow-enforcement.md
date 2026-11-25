# CodeMAX Workflow Enforcement — Implementation Plan

> **For the implementer:** tasks are TDD (RED → GREEN → commit). Workstream A
> lives in `tapway/codemax` and has its own plan:
> `tapway/codemax:docs/plans/2026-11-03-workflow-enforcement-api.md`.
> This document owns the contracts, the threat model, and workstream B/C.

**Goal:** make the three workflow points — grounded brainstorm, issue in
CodeMAX, docs synced before PR — *enforced* in Claude Code, Hermes and Codex,
so no dev or PM can complete the loop without touching CodeMAX.

**Non-goals:** replacing the kanban, changing the draft-approval access model,
or enforcing on repositories that do not use CodeMAX (the public plugin must
keep working with the gates absent).

---

## 0. What was measured (baseline, 2026-11-03)

| Fact | Evidence |
|---|---|
| A fresh Hermes profile pulls real requirements/blueprints/ADRs from gbrain | live test: 9 slugs cited, 4 options, 10-task plan, issue #1 → card `t_60b925f7` |
| The plugin registered **zero** skills on stock Hermes | `Failed to load plugin 'tapway-superpowers': No module named 'yaml'` — fixed in 2.5.1 |
| The brainstorm gate is off by default | `TAPWAY_BRAINSTORM_GATE=0` → returns `{}` |
| The gate misses Hermes payloads | Hermes `{"tool_name","args"}` → `{}`; Claude `{"tool_input"}` → block |
| `brainstorming` Step 1.5 cannot run for a new joiner | no `catalog.yaml`/`constitution.md` on the host; `TAPWAY_SPECS_DIR` unset |
| Every GitHub issue becomes a card | `github_poll.py` / `routes_webhook.py` never read labels |
| Sync is optional and unverifiable | `pr` step 5b is conditional; no hook, no receipt, no CI check |
| Repo docs never reach the brain | `codemax sync run` mirrors `$CODEMAX_WIKI_DIR` only |

---

## 1. Contracts

These three artifacts are what the gates check. Everything else is
implementation.

### C1 — Grounding (brainstorm)

Each `## Option` section carries:

```markdown
**Grounding:** `wiki/platforms/samurai-v2/decisions/adr-samurai-v2-message-bus-selection`, `projects/samurai-v2/executor/epics/executor-epic-4_-deduplication-rate-limiting`
```

Rules:
- Every citation must resolve through gbrain `get_page` (authoritative) — not a
  local specs checkout, not a filename.
- `UNKNOWN (not retrieved: <what you tried>)` is accepted as an explicit hole.
- The doc carries a header block with `platform:`, `retrieved_at:`, and the
  `pack_digest` returned by `codemax context pack`.

### C2 — Issue (plan → GitHub → CodeMAX)

Plan frontmatter:

```yaml
---
issue: 123
repo: tapway/samurai-executor-reid
platform: samurai-v2
branch: feat/alert-dedup
---
```

Rules:
- The issue exists **after** planning, carries label `codemax`, and its body
  contains the plan.
- CodeMAX creates a card **only** for issues carrying the label.
- Code is not committed until the plan declares a linked issue.

### C3 — Sync receipt (docs → wiki → gbrain before PR)

`POST /api/v1/workflow/receipts` returns:

```json
{
  "repo": "tapway/samurai-executor-reid",
  "branch": "feat/alert-dedup",
  "head_sha": "495dfc8…",
  "issue": 123,
  "draft_pr": "https://github.com/tapway/tapway-brain/pull/98",
  "pages": ["wiki/platforms/samurai-v2/decisions/adr-…"],
  "digest": "sha256:…",
  "identity": "agent:dev-v2-backend-a",
  "created_at": "2026-11-03T10:00:00Z"
}
```

Rules:
- A receipt is issued **by the server** when it accepts a sync push; a local
  file is never proof.
- A receipt is valid only for the current `head_sha`; amending or rebasing
  invalidates it and requires a re-sync.
- Wiki writes are **batched per dev**: several tasks share one draft PR
  (`codemax/<identity>/batch-<YYYYMMDD>`), and each receipt points at that PR.
  The receipt stays per `repo/branch/head_sha`; only the wiki PR is shared.

---

## 2. Enforcement layers

| Layer | Mechanism | Bypassable by | Authority |
|---|---|---|---|
| L1 in-session | Claude `PreToolUse`, Codex `PreToolUse`, Hermes `pre_tool_call` | `--yolo` does not skip it; editing the hook does | fast feedback |
| L2 git | `pre-commit` / `pre-push` installed by `install.sh` | `--no-verify` | local |
| L3 CI | reusable `codemax-workflow-gate.yml` | repo admin only (logged) | **authoritative for PRs** |
| L4 server | label filter, receipt store, token identity | nobody with a dev token | **authoritative for data** |

Design rule: **the local gate is a convenience; the CI check and the server
state are the facts.** A passing local run never substitutes for L3/L4.

### Per-IDE wiring

| IDE | Hook surface | Ships in |
|---|---|---|
| Claude Code | `.claude-plugin` → `hooks/hooks.json` `PreToolUse` | plugin (`${CLAUDE_PLUGIN_ROOT}`) |
| Hermes | `ctx.register_hook("pre_tool_call", cb)` (fail-closed) | `hermes/plugin/__init__.py` |
| Codex | `.codex/hooks.json` `PreToolUse` (trust prompt) | `codex/install.sh` + template |
| Any (PM, chat) | server-side checks on issue/label + receipt | CodeMAX |

---

## 3. Threat model — loophole → closure → proof

| # | Loophole | Closure | Proof (test) |
|---|---|---|---|
| 1 | Gate disabled by default | gate runs whenever `CODEMAX_ENABLED=1`; `TAPWAY_BRAINSTORM_GATE` kept only as an explicit opt-out for public users | `test_gate_enabled_by_codemax` |
| 2 | Hermes payload shape ignored | one adapter normalises `tool_input.*`, `args.*`, bare `path/command` | `test_payload_shapes` × 6 |
| 3 | No hooks in Hermes at all | plugin registers `pre_tool_call`, fail-closed on timeout | `test_plugin_registers_hooks` |
| 4 | Specs repo required | context pack reads gbrain; no local clone | `test_pack_from_gbrain` |
| 5 | Fabricated citations | `codemax context check` resolves every slug via `get_page` | `test_unresolved_citation_fails` |
| 6 | Agent never loads the skill | gates fire on tool calls, not on skill invocation | e2e: write without skill → blocked |
| 7 | Doc written outside `docs/brainstorming/` | CI requires a `docs/brainstorming/*.md` file on `feat/*` PRs | `test_ci_requires_brainstorm_doc` |
| 8 | No issue before code | pre-commit blocks staged `src/**` until plan has `issue:` + label | `test_commit_without_issue_blocked` |
| 9 | `codemax` label decorative | webhook + poller filter on `CODEMAX_ISSUE_LABEL` | `test_unlabeled_issue_ignored` |
| 10 | Server down = silent bypass | fail-closed when enabled; `CODEMAX_OFFLINE_OK=1` logs a waiver, CI still blocks | `test_offline_fails_closed` |
| 11 | Sync skipped before PR | `gh pr create` gate + CI receipt check | `test_pr_without_receipt_blocked` |
| 12 | Hand-written local receipt | receipt is server-issued and bound to `head_sha` | `test_local_receipt_rejected` |
| 13 | Sync then amend commit | verify compares `head_sha`, not branch | `test_amend_invalidates_receipt` |
| 14 | Repo docs never reach the wiki | `codemax sync push` writes a draft PR to `tapway-brain` | `test_sync_push_opens_draft` |
| 15 | Dev token cannot write the brain | push creates a draft PR; admin merge → gbrain sync | `test_push_uses_draft_path` |
| 16 | `--yolo` / auto-approve skips gates | Hermes `pre_tool_call` is a policy hook, not an approval | e2e with `--yolo` |
| 17 | Editing the hook locally | CI re-runs the same check from the plugin's pinned ref | `test_ci_uses_pinned_gate` |
| 18 | Direct `git push` / API PR | branch protection requires the CI check | repo config (manual step) |
| 19 | Admin force-merge | required check cannot be bypassed without admin; bypass is auditable | runbook |
| 20 | PM docs-only work skips the workflow | docs-only work needs **no code PR**, but still creates the post-plan issue and still syncs the wiki (C3); the sync push *is* the deliverable | `test_docs_only_requires_issue_and_sync` |

---

## 4. Workstream B — `tapway-superpowers`

### B1. Normalise hook payloads (single adapter)

**Files:** create `hooks/lib/payload.py`, `tests/test_hook_payload.py`

**Step 1 — failing test** (table-driven):

```python
CASES = [
    ({"tool_input": {"file_path": "docs/brainstorming/x.md", "content": "..."}}, "docs/brainstorming/x.md"),
    ({"tool_name": "write_file", "args": {"path": "docs/brainstorming/x.md"}}, "docs/brainstorming/x.md"),
    ({"file_path": "docs/brainstorming/x.md"}, "docs/brainstorming/x.md"),
    ({"tool_name": "terminal", "args": {"command": "cat > docs/brainstorming/x.md <<EOF"}}, "docs/brainstorming/x.md"),
]
```

**Step 3 — implement** `normalise(payload) -> {paths, content, command, tool}`.

**Step 4:** `pytest tests/test_hook_payload.py -v` → 4 passed.

### B2. Fix the brainstorm gate to use the adapter

**Files:** `hooks/pre-brainstorm-ground/pre-brainstorm-ground-lib.sh`, `tests/test_brainstorm_gate.sh`

- Source `hooks/lib/payload.py` (via `python3`) instead of hand-reading `tool_input`.
- Gate every path matching `docs/brainstorming/*.md`.
- Exit `{"decision":"block","reason":…}` for Claude/Codex; `{"action":"block"}` for Hermes (emit both keys — both runtimes accept their own).

**Test:** run with the three payload shapes; all block on ungrounded text.

### B3. Enable by default under CodeMAX

**Files:** `hooks/pre-brainstorm-ground/pre-brainstorm-ground.sh`

Replace the `TAPWAY_BRAINSTORM_GATE` default with:

```sh
if [ "${CODEMAX_ENABLED:-0}" != "1" ] && [ "${TAPWAY_BRAINSTORM_GATE:-0}" != "1" ]; then
  printf '{}\n'; exit 0
fi
```

**Test:** `CODEMAX_ENABLED=1` + ungrounded doc → block; unset → allow.

### B4. Gate the issue contract

**Files:** create `hooks/pre-commit-issue/pre-commit-issue.sh`, `tests/test_issue_gate.sh`

Rules: if `git diff --cached --name-only` matches `^(src|app|lib)/`, then:
1. the branch has a plan (`docs/plans/*.md`) whose frontmatter has `issue: <n>`;
2. `gh issue view <n> --json labels` includes `codemax`.

Fail with the exact remediation command.

### B5. Gate PR creation on the receipt

**Files:** create `hooks/pre-pr-sync/pre-pr-sync.sh`, `tests/test_pr_gate.sh`

On a Bash tool call whose command matches `gh pr create`:
1. derive `repo` / `branch` / `head_sha`;
2. `curl -fsS "$CODEMAX_URL/api/v1/workflow/verify?repo=…&branch=…&commit=…" -H "Authorization: Bearer $TOKEN"`;
3. `valid:false` → block with "run `codemax sync push …`".

### B6. Hermes plugin registers the gates

**Files:** `hermes/plugin/__init__.py`, `tests/test_hermes_plugin.py`

```python
def register(ctx):
    ...  # skills
    from hooks import gate  # vendored copy under hermes/plugin/gate.py
    ctx.register_hook("pre_tool_call", gate.pre_tool_call)
```

`gate.pre_tool_call(tool_name, args, **_)` returns `{"action": "block", "reason": …}`
or `None`. Fail-closed: any exception → block with the traceback summary.

**Test:** register into a real `PluginContext` and assert `hooks_registered`
contains `pre_tool_call`; invoke with an ungrounded write → block.

### B7. Claude + Codex hook manifests

**Files:** `hooks/hooks.json`, `codex/hooks.json.template`

Add matchers:

| Event | Matcher | Script |
|---|---|---|
| PreToolUse | `Write|Edit` | `pre-brainstorm-ground.sh` |
| PreToolUse | `Bash` | `pre-commit-issue.sh` (`if: git commit`) |
| PreToolUse | `Bash` | `pre-pr-sync.sh` (`if: gh pr create`) |

**Test:** `tests/test_hooks_manifest.py` asserts every script referenced exists
and is executable, in both manifests.

### B8. Skills encode the new contracts

- `skills/brainstorming/SKILL.md` + mirror: Step 1.5 becomes
  `codemax context pack --platform <p>` then `codemax context check --doc <d>`;
  cite gbrain slugs; keep the UNKNOWN rule.
- `skills/writing-plans/SKILL.md`: the issue step writes `issue:` into the plan
  frontmatter and calls `codemax task create`.
- `skills/pr/SKILL.md`: Step 5b becomes mandatory `codemax sync push` +
  `codemax sync verify`; remove "optional".
- `skills/codemax-gbrain/SKILL.md`: replace `platform-context build --specs-dir`
  and the `sync run` recipe with the new commands.

**Test:** `tests/test_skill_contracts.py` asserts the commands appear and the
old `--specs-dir` path is gone from the three skills.

### B9. Installer wires everything

**Files:** `hermes/install.sh`, `codex/install.sh`, `scripts/install-git-hooks.sh`

- Hermes: nothing extra (plugin hooks), but print the two config keys.
- Codex: copy `hooks.json.template` → `.codex/hooks.json`.
- Git: install `pre-commit`/`pre-push` wrappers into `.git/hooks`.

### B10. Reusable CI gate

**Files:** create `.github/workflows/codemax-workflow-gate.yml`

`workflow_call` job, inputs `platform`, `require-issue`:

1. checkout with `fetch-depth: 0`;
2. install the gate from the pinned plugin tag (`v2.5.2`+);
3. run `context check` over `docs/brainstorming/*.md`;
4. require an issue reference in the PR body and label;
5. `sync verify` against `CODEMAX_URL` using a repo secret.

Consuming repos add 8 lines; document in `docs/WORKFLOWS.md`.

### B11. Docs

`README.md`, `docs/WORKFLOWS.md`, `docs/DEPLOYMENT.md`, `hermes/README.md`,
and the brain page `wiki/HOW-DEVS-USE-CODEMAX.md` (one canonical page, link to
it — do not duplicate).

### B12. E2E harness

**Files:** `tests/e2e/test_workflow_gate.py`

Matrix: {Claude, Hermes, Codex} × {grounded, ungrounded} × {issue present,
missing} × {receipt valid, invalid}. The Hermes arm runs the real profile from
`tests/e2e/fixtures/` (the `saiful-demo` recipe) and asserts the agent is
blocked on each violation.

---

## 5. Workstream C — rollout

| Phase | Action | Exit criterion |
|---|---|---|
| C0 | ship 2.5.1 (plugin loads on stock Hermes) | `skills_list` returns 31 |
| C1 | codemax: receipts + context pack + label filter, flag off | tests green, no behaviour change |
| C2 | tapway-superpowers 2.6.0: gates on when `CODEMAX_ENABLED=1` | E2E matrix green |
| C3 | pilot on **all 7 `city-*` repos** (`city-guard`, `city-help-2.0`, `city-maestro`, `city-matrix`, `city-nexus`, `city-os-mobile`, `city-terra`) | 5 real PRs across ≥3 of them pass the gate |
| C4 | enable CI check as **required** on all 25 registry repos | branch protection updated |
| C5 | remove the `--specs-dir` path and the opt-out for Tapway profiles | docs updated |

Rollback: `CODEMAX_ENABLED=0` disables L1/L2 locally; CI check can be removed
from branch protection without touching code.

---

## 6. Acceptance criteria

- [ ] A brainstorm doc with an invented slug is blocked locally **and** in CI.
- [ ] A commit touching `src/` without a `codemax`-labelled issue is blocked.
- [ ] A PR without a server-issued receipt for its `head_sha` is blocked.
- [ ] An issue without the label creates no card; with it, a card appears.
- [ ] All three IDEs produce the same decision for the same violation.
- [ ] With `CODEMAX_ENABLED=0` (public users) every gate is a no-op.
- [ ] The server rejects a receipt whose `head_sha` is not the PR head.

---

## 7. Decisions (2026-11-03)

1. **Docs-only work (PMs):** no code PR required. The post-plan step still
   creates the GitHub issue (label `codemax`) → CodeMAX card, and the work ends
   with a wiki sync (C3) rather than a code PR. The issue gate therefore applies
   to **every** planned task, not just `src/**` changes.
2. **Brain writes are batched:** one draft PR per dev per day
   (`codemax/<identity>/batch-<YYYYMMDD>`), accumulating several tasks. Receipts
   stay per `repo/branch/head_sha` and reference the shared batch PR.
3. **Offline waiver stays:** `CODEMAX_OFFLINE_OK=1` allows local work during an
   outage; the waiver is journaled and CI (L3) still blocks the merge.
4. **The panel proxies wiki writes:** dev tokens stay **read-only**. The panel
   performs the git write with its own admin token and records the dev's
   identity from the request token (`whoami`). No new token scope.
5. **Pilot:** all 7 `city-*` repos — `city-guard`, `city-help-2.0`,
   `city-maestro`, `city-matrix`, `city-nexus`, `city-os-mobile`, `city-terra`.