---
name: repo-docs
description: >-
  Generate standardized technical documentation for any repository. Use this skill
  whenever a user says "document this repo", "write architecture docs", "generate
  db schema", "create workflow diagrams", "document this project", "write deployment
  steps", or any variation of producing technical docs for a codebase. Always use
  this skill before writing any documentation file for a project — it defines
  Tapway's standard format.
version: 1.2.0
author: Tapway (ported to Hermes by limcheehow)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [documentation, docs, architecture, onboarding]
    related_skills: [writing-plans, brainstorming]
---

# Repo Docs Skill (Hermes port)

Generate a standardized `docs/` folder for any repository. Every repo at Tapway must have these documents before it is considered "production-ready" or handed off.

> **Hermes note:** In Hermes, delegate the repo reading to `delegate_task` (a leaf worker) or do the read yourself with `search_files` / `read_file`, then write the doc files with `write_file`. All diagrams use **Mermaid** syntax (renders natively in GitHub, Notion, and most markdown viewers).

## Step 0 — Understand the Repo First
Before writing anything, do a thorough read of the codebase:

```bash
# Get the top-level layout
find . -maxdepth 3 \
  -not -path '*/node_modules/*' -not -path '*/.git/*' \
  -not -path '*/dist/*' -not -path '*/__pycache__/*' \
  -not -path '*/venv/*' -not -path '*/.venv/*' | sort

# Read key config and entry points
cat package.json 2>/dev/null || cat pyproject.toml 2>/dev/null || \
  cat requirements.txt 2>/dev/null || cat go.mod 2>/dev/null || true
cat docker-compose.yml 2>/dev/null || cat Dockerfile 2>/dev/null || true
# Note presence of a sample env template only — do not dump secret-bearing files
ls .env.example .env.sample 2>/dev/null || true
```

Read all major source files to understand:
- What the service/app does
- Its external dependencies (databases, queues, APIs, cloud services)
- Data models and schemas
- Entry points and main flows
- How it is deployed

## Step 1 — Create the `docs/` Folder
```bash
mkdir -p docs
```

Generate the following files.

### 1. `docs/ARCHITECTURE.md`
**Purpose:** High-level system design. Anyone joining the project must understand the full picture from this file alone.

Required sections: Overview (2–4 sentences); System Diagram (Mermaid `graph TD` with every arrow labeled by protocol); Component Breakdown (one paragraph per major component); Data Flow (numbered steps for the primary use case); Key Design Decisions (non-obvious choices + reasons); External Dependencies table (Dependency / Type / Purpose / Notes).

### 2. `docs/DB_SCHEMA.md`
**Only generate if the service has a database, ORM models, or persistent storage.** Skip entirely if stateless.

Required sections: Storage Technology; Entity Relationship Diagram (Mermaid `erDiagram`); Table/Collection Definitions (per table: field, type, key, description); Access patterns (DynamoDB); Data Retention & Cleanup.

### 3. `docs/WORKFLOWS.md`
**Purpose:** Describe every significant runtime flow as a sequence diagram. Most important file for debugging and onboarding.

One section per major workflow (minimum: primary happy path + one error/retry path). Each: Trigger, Actor, Mermaid `sequenceDiagram`, step-by-step prose, Edge Cases / Failure Modes.

### 4. `docs/DEPLOYMENT.md`
Required sections: Environment Overview table; Prerequisites (tools, credentials, env vars, min versions); Environment Variables table; Build (actual commands); Deploy steps (edge/cloud); Health Check & Verification; Rollback; Common Issues table.

### 5. `docs/README.md` (optional but recommended)
If the repo root README is missing or outdated, generate a concise one linking the docs above.

## Step 2 — Quality Checklist
- [ ] Every Mermaid diagram is syntactically valid (no unclosed blocks)
- [ ] All external services mentioned in the code appear in ARCHITECTURE.md
- [ ] DB_SCHEMA.md was skipped if the service has no persistent storage
- [ ] WORKFLOWS.md covers at least the primary happy path AND one error path
- [ ] DEPLOYMENT.md has actual commands (not placeholders like `<command here>`)
- [ ] No section says "TODO" or is left blank

## Step 3 — Commit
Suggest this commit message after generating:
```
docs: add standardized architecture, workflow, and deployment docs

Generated via repo-docs skill. Covers:
- ARCHITECTURE.md — system diagram + component breakdown
- DB_SCHEMA.md — entity diagram + table definitions (if applicable)
- WORKFLOWS.md — sequence diagrams for all major flows
- DEPLOYMENT.md — build/deploy steps
```

## Notes for the Agent
- If the codebase is large, read the most important files first (entry points, models, config) and do not exhaustively read every file before starting.
- If something is genuinely unclear, note it as `<!-- TODO: verify -->` in the doc rather than inventing something incorrect.
- Mermaid diagrams must be inside fenced code blocks labeled `mermaid`.
- Do not generate placeholder content. Every field must reflect the actual code.
