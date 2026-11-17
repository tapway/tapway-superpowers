---
name: repo-wiki-writer
description: Write or update a repository's GitHub Wiki in plain, human-readable language, using three standard pages - Home (what this repo is and why it exists), How it works (high-level architecture), and Technical Details (APIs, config files, .env variables, setup, and everything a teammate needs to know). Use this skill whenever someone asks to write, generate, refresh, fill in or improve the wiki, document a repo for the team, explain a codebase for onboarding, or update the Home / How it works / Technical Details pages, even if they don't say "wiki" explicitly.
---

# Repo Wiki Writer

Writes the team wiki for a repo as three pages that a new teammate can read top to bottom:

| Page | File in the wiki repo | Answers |
|---|---|---|
| Home | `Home.md` | What is this, who is it for, why does it exist? |
| How it works | `How-it-works.md` | What are the big pieces and how do they talk to each other? |
| Technical Details | `Technical-Details.md` | How do I run it, configure it, call it, and not break it? |

The reader is a teammate, not the author. Assume they are smart but have never opened this repo. Every page should make sense to someone who reads only that page.

## Workflow

### 1. Get the wiki repo next to the code repo

A GitHub Wiki is its own git repo. From the code repo's parent folder:

```bash
REPO_URL=$(git -C <code-repo> remote get-url origin)   # e.g. https://github.com/tapway/samurai-scout-ds.git
git clone "${REPO_URL%.git}.wiki.git"
```

If the clone fails with "not found", the wiki has no pages yet. Ask the user to create the Home page once in the browser (Wiki tab → Create the first page → Save), then retry.

Look at the existing page files first. If pages already exist under slightly different names, keep their file names so existing links don't break. Page titles come from file names: hyphens become spaces.

### 2. Study the code repo before writing anything

Read, in roughly this order, and stop once you understand the system:

1. `README*`, `CLAUDE.md`, `AGENTS.md`, `docs/`, any `*PLAN*.md` or design notes
2. How it starts: `Makefile`, `docker-compose*.yml`, `Dockerfile*`, `package.json` scripts, `pyproject.toml`, entrypoint files, `bin/`, `scripts/`
3. Configuration: `.env.example`, `config/`, settings modules, anywhere env vars are read (`os.getenv`, `process.env`, `Settings` classes)
4. Interfaces: HTTP routes, message topics/queues, database models and migrations, external services called
5. `tests/` to confirm what the code is actually expected to do

Facts must come from the repo. If something can't be found (who owns it, which server it runs on, why a decision was made), write `> ❓ Ask the team: ...` rather than guessing. A wiki that is confidently wrong is worse than one with honest gaps.

### 3. Write the three pages

Read `references/writing-style.md` first, then the template for each page:

- `references/page-home.md`
- `references/page-how-it-works.md`
- `references/page-technical-details.md`

Templates are a starting structure, not a form to fill. Drop sections that don't apply and add ones the repo needs.

If pages already have content, update instead of replacing. Keep anything a human wrote that is still accurate, fix what's outdated, and fill in what's missing.

### 4. Secrets: never

Never copy real values from `.env`, config files, CI secrets, or anywhere else into the wiki: no passwords, tokens, API keys, private hostnames with credentials, or connection strings with passwords. Document the variable **name**, what it's for, an example **format**, and where to get the real value ("ask the team lead", "from the vault"). Use `.env.example` as the source, not `.env`. If you spot a real secret committed in the code repo, tell the user instead of documenting it.

### 5. Review, then publish

1. Show the user a summary of what changed on each page and anything marked "Ask the team".
2. Only after the user confirms, commit and push the wiki repo. When this skill runs as a step inside `/pr` or `/autoship`, the user already confirmed by invoking that workflow — summarize the wiki diff in the same place you report doc updates (e.g. the PR body) instead of pausing for a second confirmation, and commit and push directly:

```bash
cd <repo>.wiki
git add -A
git commit -m "docs(wiki): update Home, How it works, Technical Details"
git push
```

3. Optionally add or update `_Sidebar.md` so the three pages appear in order:

```markdown
**[[Home]]**
- [[How it works]]
- [[Technical Details]]
```

## Keeping it fresh

When asked to refresh the wiki after code changes, check `git log` since the wiki's last commit date, look at what changed (new env vars, new endpoints, new services, removed features), and update only the affected sections.
