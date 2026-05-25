# Tapway Superpowers

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Tapway's collection of Claude Code skills, agents, and hooks for full-stack development with Next.js 14 + Python FastAPI.

## What's Included

- **12 skills** — brainstorming, TDD, code review, systematic debugging, security audit, refactoring, pre-review cleanup, verification, and more
- **4 agents** — specialized subagents for complex multi-step workflows
- **5 hooks** — automated triggers for common development workflows

## Installation

```bash
claude plugin marketplace add <repo-url>
claude plugin install tapway-superpowers@tapway
```

Replace `<repo-url>` with the GitHub repository URL once published.

## Skills

| Skill | Description |
|---|---|
| brainstorming | Explore approaches before writing code for new features or architecture decisions |
| code-review | Review code for quality, correctness, security, and project conventions |
| refactor | Improve code quality without changing behavior |
| tdd | Test-driven development workflow |
| systematic-debugging | Structured approach to diagnosing and fixing bugs |
| security-audit | Security review of pending changes |
| verification | Verify implementation against requirements |
| pre-review-cleanup | Scan for template placeholders and scaffolding artifacts |
| writing-plans | Write structured implementation plans for multi-step tasks |
| subagent-driven-development | Execute plans with isolated subagents |
| fewer-permission-prompts | Reduce permission prompts by allowing common tools |
| repo-docs | Generate standardized technical documentation |

## License

MIT