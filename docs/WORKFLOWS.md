# Workflows — Tapway Superpowers

One section per significant workflow. These are the flows a developer (or agent)
goes through when using the plugin, plus the flows the plugin itself runs.

## Workflow: Solo Feature Build (Individual Mode)

**Trigger:** Developer asks the agent to implement a feature or fix a bug
**Actor:** Developer + coding agent

```mermaid
sequenceDiagram
  actor Dev
  participant Agent
  participant Subagents as TDD Subagents
  participant Hooks as Guardrail Hooks
  participant CI

  Dev->>Agent: "implement X"
  Agent->>Agent: interview / brainstorming (if underspecified)
  Agent->>Agent: writing-plans → docs/plans/X.md
  loop each task
    Agent->>Subagents: Test Writer (RED)
    Subagents-->>Agent: failing test
    Agent->>Agent: RED gate ✔
    Agent->>Subagents: Implementer (GREEN+REFACTOR)
    Subagents-->>Agent: green tests + commit
    Hooks->>Hooks: pre-commit-gate / dependency-audit / secrets (exit 2 blocks)
  end
  Agent->>Agent: e2e-playwright (frontend+backend, conditional)
  Agent->>Agent: simplify → three-tier review
  Agent->>CI: /pr → push → pull request
  CI->>CI: quality.yml + playwright.yml gates
  CI-->>Dev: green checks / merge
```

**Description:**
The agent runs the strict pipeline in order — interview → brainstorm → plan →
TDD → E2E → simplify → review → PR. Hooks fire at tool-use time: a commit that
fails lint/format/typecheck/coverage, or that contains a critical dependency
vulnerability, is blocked before it happens (`exit 2` on PreToolUse).

**Edge Cases / Failure Modes:**
- Task fails twice → coordinator pauses and reports the blocker instead of pushing on.
- `/review` finds Critical issues → fixed before the PR opens.
- E2E gate skips when only docs/config changed (conditional file detection).
- A commit with failing quality gates → blocked by the hook; agent fixes and re-commits.

## Workflow: Automated Ship (autoship)

**Trigger:** "implement it with autopilot" / "ship and deploy"
**Actor:** Developer + autoship coordinator

```mermaid
sequenceDiagram
  actor Dev
  participant Coord as autoship coordinator
  participant Loop as Task loop (TDD subagents)
  participant Docs as repo-docs
  participant CI

  Dev->>Coord: autoship [deploy mode]
  Coord->>Coord: plan health check
  Loop->>Loop: per task: RED→GREEN→review
  Coord->>Docs: update docs (mandatory)
  alt deploy mode
    Coord->>Coord: detect deploy method → deploy to staging
    Coord->>Coord: health-check loop (60s)
    Coord->>Coord: run integration + E2E suites
  end
  Coord->>CI: open PR with evidence
  CI-->>Dev: gate results
```

**Description:**
Autoship runs the whole plan-to-PR loop without human intervention. Deploy mode
adds: deploy to staging, health check, and integration/E2E execution before the
PR opens — never a PR with a broken deployment.

**Edge Cases / Failure Modes:**
- Deployment fails → coordinator does NOT open the PR; reports and waits.
- Health check times out → logs last 50 lines, suggests rollback, does not PR.
- E2E gate mandatory in **standard mode** too (not just deploy mode) for
  frontend/backend changes.

## Workflow: Legacy Refactor

**Trigger:** Taking over an untested codebase
**Actor:** Developer + agent

```mermaid
sequenceDiagram
  actor Dev
  participant Agent
  participant Audit as code-review + security-audit
  participant Char as characterization tests

  Dev->>Agent: legacy refactor
  Agent->>Agent: repo-docs (architecture docs)
  Agent->>Audit: parallel audits
  Audit-->>Agent: findings
  Agent->>Agent: brainstorm refactor goals
  Agent->>Char: lock down current behavior FIRST
  Agent->>Agent: plan → tdd → pr
```

**Description:**
Legacy mode writes **characterization tests** (capture current behavior) before
any refactor — you cannot safely change code you haven't locked down.

**Edge Cases / Failure Modes:**
- Characterization RED fails because code is too coupled to unit-test →
  decouple/extract until tests pass.
- Bulk mechanical changes (renames) → use the community `code-refactor` skill,
  but only after characterization tests exist.

## Workflow: Incident Response

**Trigger:** An alert from `observe` fires (or an incident happens)
**Actor:** On-call engineer + `incident-runbook` skill

```mermaid
sequenceDiagram
  actor Oncall
  participant Alert as observe alert
  participant Skill as incident-runbook skill
  participant RB as docs/runbooks/<failure>.md

  Alert-->>Oncall: page with runbook link (SEV1/2)
  Oncall->>Skill: follow the runbook
  Skill->>RB: read symptom → causes → check → mitigate → escalate → rollback
  RB-->>Oncall: steps
  Oncall->>Skill: post-incident postmortem (blameless, 5-Whys, action items)
```

**Description:**
Every `observe` alert links to a runbook; the `incident-runbook` skill creates
and maintains those runbooks (SEV1–4) and the blameless postmortem with owned,
dated action items.

**Edge Cases / Failure Modes:**
- Alert without a runbook → `observe` now instructs the agent to create one
  before shipping the alert.
- Postmortem blames a person → skill's hard rule forbids it (name processes/gaps).
- Suggested rollback = DB downgrade → skill forbids it (expand-contract instead).

## Workflow: Release

**Trigger:** PR merges to `staging` or `prod`
**Actor:** GitHub Actions `release.yml`

```mermaid
sequenceDiagram
  participant GH as GitHub Actions
  participant V as release.yml
  participant Tag as git tag
  participant Rel as GitHub Release

  GH->>V: push to staging/prod
  V->>V: detect env (-stg / -prod)
  V->>V: latest tag + conventional commits → bump (major/minor/patch)
  V->>Tag: create vX.Y.Z-env tag
  V->>Rel: publish release from CHANGELOG top section
```

**Description:**
Semantic versioning with an environment suffix (`v1.2.3-stg` / `-prod`). The
bump is derived from conventional commits since the last tag for the same env.

**Edge Cases / Failure Modes:**
- No prior tag for the env → starts from 0.0.0 so the first conventional commit
  rolls to a sane version.
- CHANGELOG has no top section → release notes fall back to the tag title.

## Workflow: Install the Hermes plugin

**Trigger:** A Hermes user wants Tapway skills without cloning this repo
**Actor:** Developer + `hermes` CLI

```mermaid
sequenceDiagram
  actor Dev
  participant CLI as hermes plugins
  participant GH as GitHub
  participant Guard as plugin-guard
  participant Home as HERMES_HOME/plugins

  Dev->>CLI: hermes plugins install tapway/tapway-superpowers/hermes/plugin --enable
  CLI->>GH: clone repo, keep hermes/plugin only
  CLI->>Guard: scan that subdirectory
  Guard-->>CLI: not DANGEROUS
  CLI->>Home: install as tapway-superpowers
  Dev->>Dev: new session, skill_view("tapway-superpowers:tdd")
```

**Description:**
The subdirectory install is the supported path. Installing the repository root
is rejected: plugin-guard marks hooks and installer docs DANGEROUS. Plugin
skills are namespaced and do not create `/tdd`-style slash commands. Use
`hermes/install.sh` for the `/tapway` bundle.

The plugin ships its own copy of `hermes/skills/` so an install is
self-contained. After adding or editing a skill, refresh the mirror:

```bash
./scripts/sync-hermes-plugin-skills.sh          # hermes/skills -> hermes/plugin/skills
./scripts/sync-hermes-plugin-skills.sh --check  # exit 1 when the trees differ
```

**Edge Cases / Failure Modes:**
- Install of the repo root → blocked. Retry with the `hermes/plugin` suffix.
- Skill text drifts from `hermes/skills/` → run the sync script.
  `tests/test_hermes_plugin.py` and `--check` both fail until the mirror is
  refreshed.
- Expecting `/brainstorming` from the plugin → it will not appear. Load
  `tapway-superpowers:brainstorming`, or run `install.sh` for slash commands.


## Hook-enforced contracts (v2.6.0)

| Gate | Where | Blocks |
|---|---|---|
| Brainstorm grounding | `pre-brainstorm-ground` (Claude/Codex) + Hermes `pre_tool_call` | a write to `docs/brainstorming/*.md` whose option sections carry no `Grounding:` line |
| Plan → issue | `pre-pr-contract` on `gh pr create`, plus `workflow-gate` CI | a `docs/plans/*.md` without `issue: <number>` frontmatter |
| Payload shapes | `hooks/lib/hook_payload.py` | n/a — normalises Claude (`tool_input`), Hermes (`args`) and Codex (flat) so every gate reads one shape |

The gates default **on under CodeMAX** (`CODEMAX_WORKFLOW=1` or a `.codemax.yml`)
and off elsewhere. `TAPWAY_BRAINSTORM_GATE=0` and `TAPWAY_PR_GATE=0` are the
documented per-run overrides; CI is still authoritative.
