# Project Agent Instructions

## Development Process

**Always follow this pipeline for any feature or bug fix:**

1. **Interview** — if the request is underspecified, ask clarifying questions
   one at a time.
2. **Brainstorming** — explore approaches before coding. Save to
   `docs/brainstorming/`. Commit.
3. **Writing Plans** — create a bite-sized TDD plan. Save to
   `docs/plans/`. Commit.
4. **TDD** — RED (failing test) → GREEN (minimal implementation) → REFACTOR.
   Never write production code without a failing test first.
5. **Pre-Review Cleanup** — scan for placeholders, stale scaffolding.
6. **Code Review** — three-tier self-review (security, quality, architecture).
7. **PR** — rebase, test, push, open PR. Never push directly to main.

Invoke with `$tapway` or follow each step via its skill:
`$interview` `$brainstorming` `$writing-plans` `$tdd` `$code-review` `$pr`

## Guardrails

- **Never commit to main/master directly.** Always use a feature branch + PR.
- **Never force push.** Use a PR instead.
- **Never hardcode secrets.** Use environment variables.
- **Run lint + typecheck + tests before every commit.**
- **CodeMAX/gbrain is optional.** Set `CODEMAX_ENABLED=1` to activate.