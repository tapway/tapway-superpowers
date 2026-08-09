---
name: incident-runbook
description: >
  Create incident runbooks and blameless postmortems that close the gap
  between an alert firing and someone knowing what to do. Every alert from the
  observe skill must link to a runbook — this skill writes that runbook:
  SEV1-4 severity triage, symptom-to-mitigation playbook, escalation, and a
  blameless postmortem with action items. Triggers include "runbook",
  "incident", "postmortem", "on-call", "how do we handle X outage",
  "create a runbook", "write a postmortem", "SEV".
version: 1.0.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [incident, runbook, postmortem, on-call, severity, sre, reliability]
    related_skills: [observe, systematic-debugging, verification, code-review, db-migration-testing]
---

# Skill: Incident Runbooks & Blameless Postmortems (Hermes port)

**When to invoke:** When adding a new alert in `observe` (every alert needs a
runbook it links to), when an incident happens and needs a postmortem, or when
an existing alert fires without a documented response. This skill turns the
alert→action gap into a documented, testable playbook.

> **Hermes note:** This skill is coordinator-driven — the agent writes the
> runbook/postmortem files from the templates in this skill's directory. The
> verification gate is a file-existence + content check, not a subagent
> dispatch. No `delegate_task` needed.

> **Why it matters:** `observe` produces alerts that link to
> `docs/runbooks/<failure>.md`. Without a runbook, an on-call engineer gets a
> page and no instructions. This skill creates the artifact the alerts
> reference — so a fire is a procedure, not a panic.

---

## Core Concept

> SEV severity decides *who gets woken up*. The runbook decides *what they do*.
> The postmortem decides *what we prevent next time*.

| SEV | Definition | Response |
|---|---|---|
| **SEV1** | Production down / data loss / security breach | Page now; IC + on-call; incident channel |
| **SEV2** | Major feature degraded, no workaround | Page; on-call responds within 15min |
| **SEV3** | Partial degradation with workaround | Ticket; fix next business day |
| **SEV4** | Cosmetic / non-urgent | Backlog |

---

## Protocol

### Step 1 — Create the Runbook (`docs/runbooks/<failure>.md`)

Use the `runbook.md` template (in this skill's templates dir). Fill in:

- **Symptom** — the exact alert text / user-visible symptom an on-call person sees
- **Suspected causes** — the 2-5 most likely causes, ordered by likelihood
- **Check & confirm** — commands/logs/metrics to run to identify which cause it is
- **Mitigation** — the fastest safe action per cause (rollback, restart, feature-flag off, scale up)
- **Escalation** — who to page if mitigation doesn't work, and after how long
- **Rollback / roll-forward** — how to undo the change that caused it

```markdown
# Runbook: Payment Failures

- Severity: SEV2
- Owner: payments team
- Alerts: `payment_failures > 10 in 1min` (from observe)

## Symptom
Users see "Payment failed" on checkout.

## Suspected causes (most likely first)
1. Stripe webhook retry storm → check `stripe_webhook_lag` metric
2. DB connection pool exhaustion → check `pool_usage`, `pg_stat_activity`
3. Recent deploy (PR #1234) → check deploy log timestamp vs incident start

## Check & confirm
- `curl /metrics | grep payment_failure` — count and error codes
- `psql -c "SELECT count(*) FROM pg_stat_activity WHERE state='active'"`

## Mitigation
| Cause | Action |
|---|---|
| Webhook storm | Pause webhook processing (feature flag `webhooks_paused`) |
| Pool exhaustion | Roll out DB pool increase (config change, 2min) |
| Bad deploy | `git revert PR #1234` and redeploy |

## Escalation
Page payments-oncall after 15min if not resolved. Manager after 30min.

## Rollback
`git revert <sha>` + redeploy. DB migrations are forward-only; do not
downgrade — expand-contract instead (see db-migration-testing skill).
```

### Step 2 — Verify the Runbook

- [ ] An on-call engineer who has never seen this alert could follow it without Slack
- [ ] Every metric/log command in "Check & confirm" actually exists
- [ ] Mitigation actions are safe (no data loss)
- [ ] The alert in `observe` links to this exact file path

### Step 3 — Write a Blameless Postmortem (after the incident)

Use the `postmortem.md` template. Key sections:

- **Timeline** — what happened when (UTC), including detection, mitigation, resolution
- **Root cause analysis** — 5-Whys, not blame. "The deploy went out without a runbook" not "Alice shipped a bug"
- **Action items** — concrete, owner'd, tracked: fix the root cause, add the missing test/check, update the runbook
- **Blameless rule** — never name people as causes; name processes, gaps, and technical causes

```markdown
# Postmortem: Payment Failures 2026-08-09

Severity: SEV2 | Duration: 42min | Detect→Mitigate (MTTD/MTTR)

## Timeline (UTC)
- 14:02 — alert `payment_failures > 10` fired
- 14:05 — on-call paged, incident channel opened
- 14:11 — identified pool exhaustion (pg_stat_activity=120 active)
- 14:23 — config change raised pool limit; failures stopped
- 14:44 — fully resolved

## Root Cause (5-Whys)
1. Why failures? → DB pool exhausted
2. Why? → Webhook retry storm after Stripe latency spike
3. Why? → No backpressure on webhook queue
4. Why? → No load test for webhook burst
5. Why? → Load-test skill not applied to async workers

## Action Items
- [ ] Add backpressure to webhook queue (owner: payments, due: +1wk)
- [ ] Add webhook-burst load test (owner: qa, due: +2wk)
- [ ] Update runbook with pool-exhaustion section (owner: sre, done)

## Blameless
This was a process gap (no backpressure, no load test), not a person error.
```

### Step 4 — Track Action Items

- [ ] Each action item has an owner and a due date
- [ ] Follow up after the due date — an un-tracked postmortem action is a future SEV1
- [ ] Reference the postmortem from the runbook ("after this incident, see postmortem link")

---

## Verification / Gate

This skill is done when:

- [ ] `docs/runbooks/<failure>.md` exists for every alert in `observe`
- [ ] Runbook has symptom → causes → check → mitigate → escalate → rollback
- [ ] Postmortem (if incident happened) is blameless, has timeline + 5-Whys + tracked action items
- [ ] Every alert body links to its runbook

---

## Hard Rules

- ❌ Never create an alert in `observe` without a runbook for it
- ❌ Never write a postmortem that blames a person — name processes and gaps
- ❌ Never leave a postmortem action item un-owned or un-dated
- ❌ Never suggest a DB downgrade as a rollback — use expand-contract (see db-migration-testing)
- ❌ Never claim "incident resolved" without updating the runbook with what we learned