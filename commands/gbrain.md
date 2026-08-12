# /gbrain — Query or Sync the Shared Brain

Query the shared gbrain brain (requirements, blueprints, ADRs, decisions) or
sync living-docs back into it. The brain is a **source of truth** — use it at
task boundaries, not continuously.

## Usage

```
/gbrain query <terms>    # search gbrain for context on a topic
/gbrain sync             # push living-docs (wiki) into gbrain
/gbrain context <WO-xx>  # pull the traced requirement/blueprint/ADR for a work order
```

## Implementation

The brain is exposed via the `gbrain` MCP server (registered with
`claude mcp add`, see the developer guide §2.1), or via the `codemax` CLI.

### Query
```bash
# Prefer the MCP server if registered:
claude mcp get gbrain   # confirm connected
# Then ask Claude to search gbrain via its tools (search / list_pages / get_page)

# Or via the codemax CLI-driven search through the panel API:
curl -s "http://47.250.116.35:8125/api/v1/brain/search?q=<terms>&limit=10" \
  -H "Authorization: Bearer <your-gbrain-token>"
```

### Sync (push living-docs → gbrain)
```bash
codemax sync run --wiki-dir ~/brain/wiki --gbrain-dir ~/brain
gbrain list -n 5   # verify recent pages
```

### Context for a work order
Follow the `codemax-gbrain` skill: find the WO's "Traces to:" line, read the
linked requirement/blueprint/ADR, and load that context. Never fabricate a
requirement — if it's missing, say so.

## Notes

- **Pull once, push once.** Don't query gbrain continuously mid-task.
- **Structural changes** (new requirements/blueprints/ADRs) land on a feature
  branch as a PR — not directly on `main`.
- If `codemax` / the MCP server isn't available, say so and continue with the
  repo's living-docs; note that sync must be run by someone with the CLI.