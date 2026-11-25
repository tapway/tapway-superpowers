# Writing style

The goal: a teammate reads the page once and understands. Not a spec, not a code dump.

## Rules

- **Lead with the point.** The first sentence of every section says what the reader needs to know. Details come after.
- **Plain words first, jargon second.** If a technical term is needed, explain it the first time in a few words: "Redis Streams (a queue that keeps messages until each consumer has read them)".
- **Short sentences, short paragraphs.** Three or four sentences per paragraph at most.
- **Say why, not just what.** "We cache Keycloak results for 60 seconds so live video doesn't stall when Keycloak is slow" beats "Cache TTL is 60s".
- **Use analogies sparingly** for the big ideas on Home and How it works. One good analogy per page is plenty.
- **Concrete over abstract.** Give a real example request, a real example config line, a real folder name.
- **Tables for lists of facts** (env vars, endpoints, services). Prose for explanations.
- **Diagrams for architecture.** GitHub wikis render Mermaid. Keep diagrams to about 10 boxes; split if bigger.
- **No filler.** Skip "This document describes..." and "In conclusion". Skip marketing words like "robust", "seamless", "cutting-edge".
- **Write for skimming.** Clear headings, so someone looking for "how do I run it locally" finds it in five seconds.

## Before / after

Too technical:
> The service consumes from the `cv-events` stream via XREADGROUP with a consumer group per evaluator, applies the rule DSL, and emits to the sink adapter.

Plain:
> Every camera detection lands in a queue called `cv-events`. Each rule checker reads from that queue on its own, decides whether the detection breaks a rule (for example, "person in restricted zone for more than 30 seconds"), and if so, sends an alert on to be stored and shown on the dashboard.

## Audience check

Before finishing a page, reread it as:
1. A new engineer on day one: can they find how to run it?
2. A PM or QA tester: can they understand what it does from Home and How it works without reading code?
