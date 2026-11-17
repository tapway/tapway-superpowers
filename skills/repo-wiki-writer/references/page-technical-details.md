# Technical Details page template

Purpose: everything a teammate needs to run, configure, call, debug and safely change this repo. This is the reference page, so precision matters, but still explain each item in plain words.

~~~markdown
# Technical Details

## Quick start
<The shortest path from fresh clone to running locally. Exact commands, in order.>

```bash
git clone ...
cp .env.example .env   # then fill in values; see "Configuration" below
make up                # or docker compose up -d, npm run dev, etc.
```

<How to tell it's working: URL to open, log line to look for, health endpoint.>

## Requirements
<Runtime versions, GPU/CUDA needs, OS, services that must be running (database, Redis, MQTT broker, Keycloak, ...).>

## Configuration

### Environment variables (`.env`)
| Variable | What it's for | Example format | Required? | Default |
|---|---|---|---|---|
| `DATABASE_URL` | Where the service stores events | `postgresql://user:***@host:5432/db` | Yes | none |

<Never put real values here. Say where to get them.>

### Config files
| File | What it controls | When you'd change it |
|---|---|---|

## API
<For each endpoint or message topic: what it's for in one line, method + path (or topic name), key inputs, what comes back, and a short example. Group by purpose. If there's OpenAPI/Swagger, link it and summarise only the important ones.>

| Method | Path | What it does |
|---|---|---|

Example:
```bash
curl -X GET http://localhost:8000/api/v1/health
```

## Data
<Databases, tables or collections that matter, queues/streams, file storage (MinIO/S3 buckets). What lives where and who writes it. How migrations are run.>

## Running, testing, deploying
- Run tests: `<command>`
- Lint/format: `<command>`
- Build images: `<command>`
- Deploy: <how and where it's deployed, CI workflows in `.github/workflows/`>

## Logs and troubleshooting
| Symptom | Likely cause | What to do |
|---|---|---|

## Gotchas
- <Things that have bitten people: ordering of startup, ports that clash, settings that only apply on first run, hard-coded values.>

## Glossary
| Term | Meaning here |
|---|---|
~~~

Build the env var table by reading `.env.example` and searching the code for where each variable is read, so the "What it's for" column reflects real use. Flag variables that are read in code but missing from `.env.example`, since those are what trip up new teammates.
