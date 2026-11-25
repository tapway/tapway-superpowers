# Runbook: [Failure Name]

- Severity: SEV[1|2|3|4]
- Owner: [team]
- Alerts: [exact alert text from observe, with threshold]

## Symptom
[What the user or on-call engineer sees — the alert text, user-visible symptom]

## Suspected causes (most likely first)
1. [Cause 1] — [how to check: metric/log/query]
2. [Cause 2] — [how to check]
3. [Cause 3] — [how to check]

## Check & confirm
```bash
# [command that confirms / rules out cause]
# [command 2]
```

## Mitigation
| Cause | Action | Time |
|---|---|---|
| [Cause] | [Fastest safe action] | [time to do] |

## Escalation
- [Who to page] after [time] if not resolved
- [Manager / second-level] after [time]

## Rollback / Roll-forward
- `git revert <sha>` + redeploy for code issues
- DB migrations are forward-only — never downgrade; use expand-contract (see db-migration-testing skill)

## Related
- Postmortem: [link after incident]