---
name: observe
description: >
  Adds structured logging, RED metrics, and distributed tracing alongside feature
  development — not as a post-launch afterthought. Defines on-call questions first,
  then selects the right signal. Covers correlation IDs, OpenTelemetry, symptom-based
  alerting with runbooks, and staging verification. Triggers include "add observability",
  "add logging", "add metrics", "add tracing", "instrument this", "/observe".
---

# Skill: Observe

**When to invoke:** When shipping a new endpoint, background task, or service integration. Run this before `/pr` so instrumentation ships with the feature, not as a follow-up ticket that never gets done.

---

## Core Principle

> Code you can't observe is code you can't operate.

Production failures are invisible until users complain or alerts fire. This skill wires the three signal types — logs, metrics, traces — at development time, when the mental model of the code is fresh and instrumentation gaps are cheapest to fill.

---

## Protocol

### Step 1 — Define On-Call Questions First

Before writing a single log line, list the questions an on-call engineer will ask when this feature breaks at 3am:

```
What will the on-call ask?
1. Which user/request caused this?
2. How many requests are failing right now?
3. Which service in the chain is slow?
4. What was the input that triggered the failure?
5. When did this start?
```

Every piece of instrumentation must answer at least one of these questions. If it doesn't, skip it — logging noise makes finding the real signal harder.

### Step 2 — Choose the Right Signal

| Question type | Signal | Why |
|---|---|---|
| "Why did THIS specific request fail?" | **Structured log** | Carries full request context |
| "How often is this failing in aggregate?" | **Metric** | Aggregates across all requests |
| "Where in the chain is time being spent?" | **Trace** | Shows latency breakdown across services |

Don't use logs as metrics (log-parsing at scale is slow and brittle). Don't use metrics to debug individual requests (no per-request context). Don't add distributed tracing if the entire path is within a single process.

### Step 3 — Implement Structured Logging

**FastAPI (Python) — use structlog:**
```python
import structlog
log = structlog.get_logger()

log.info("payment.processed",
    correlation_id=request.state.correlation_id,
    user_id=user_id,
    amount_cents=amount,
    payment_method=method,
)
```

**Next.js (TypeScript) — structured JSON logger:**
```typescript
import { logger } from '@/lib/logger';

logger.info('payment.processed', {
  correlationId: req.headers['x-correlation-id'],
  userId,
  amountCents: amount,
});
```

**Logging rules:**
- Use stable `event_name` strings (`payment.processed`, not `"Processing payment for ${id}"`)
- All fields are machine-readable key-value — no string interpolation in the message body
- Every log line carries `correlation_id` — "every log line, span, and outbound call must carry a request ID"
- Log levels: `DEBUG` (dev detail), `INFO` (normal operations), `WARNING` (unexpected but handled), `ERROR` (requires human attention)
- **Never log PII** — log IDs that can be joined in a secure system, not the values themselves (no emails, passwords, card numbers, phone numbers)

**Correlation ID middleware (FastAPI):**
```python
import uuid
from fastapi import Request

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

### Step 4 — Add RED Metrics

For every new endpoint or background task, add three metrics:

| Metric | Type | Labels |
|---|---|---|
| `http_requests_total` | Counter | `method`, `endpoint`, `status_code` |
| `http_request_errors_total` | Counter | `method`, `endpoint`, `error_type` |
| `http_request_duration_seconds` | Histogram | `method`, `endpoint` |

**FastAPI (prometheus-client):**
```python
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    'http_requests_total', 'Total requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 'Request latency',
    ['method', 'endpoint']
)
```

**Critical cardinality rule:** Label values must come from **bounded sets**. Never use user IDs, error messages, or any unbounded strings as label values — this creates a cardinality explosion that kills Prometheus performance.

**Always use percentiles, not averages:** p50, p95, p99 surface tail latency that averages hide. Averages can look fine while 1% of users experience 10-second responses.

### Step 5 — Wire Distributed Tracing

Use OpenTelemetry with auto-instrumentation where available:

**FastAPI (Python):**
```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument()
HTTPXClientInstrumentor().instrument()
```

**Next.js (TypeScript) — custom spans for business logic:**
```typescript
import { trace } from '@opentelemetry/api';
const tracer = trace.getTracer('payment-service');

await tracer.startActiveSpan('process-payment', async (span) => {
  try {
    span.setAttributes({ userId, amountCents: amount });
    const result = await processPayment(userId, amount);
    return result;
  } catch (err) {
    span.recordException(err);
    throw err;
  } finally {
    span.end();
  }
});
```

**Sampling strategy:** Keep 100% of error traces. Sample ~10% of successful traffic. Never trace every request at full volume in production — storage costs balloon.

### Step 6 — Set Up Alerting

Alert on **symptoms users experience**, not infrastructure causes:

| Good alert (symptom) | Bad alert (cause) |
|---|---|
| `error_rate > 1% for 5min` | `CPU > 85%` |
| `p99_latency > 2s for 5min` | `memory > 80%` |
| `payment_failures > 10 in 1min` | `pod restarts > 3` |

Every alert requires:
1. **Threshold** — derived from SLOs or historical baseline, not guessed
2. **Runbook** — linked in the alert body: `See: docs/runbooks/payment-failures.md`. If the runbook doesn't exist yet, create it with the `incident-runbook` skill before shipping the alert — an alert without a runbook is a page with no procedure.
3. **Severity** — `page` (wake someone up now) vs `ticket` (fix next business day)

### Step 7 — Verify in Staging

Before opening the PR, induce failures intentionally in staging and confirm telemetry catches them:

- [ ] Trigger the error path — does a log line appear with the correct `correlation_id`?
- [ ] Hit the metrics endpoint (`/metrics`) — do new counters appear with expected labels?
- [ ] Check the trace UI (Jaeger / Grafana Tempo) — does the trace follow the request end-to-end without gaps?
- [ ] Send a deliberately slow request — does the histogram show the latency bucket correctly?

If you cannot find the induced failure using telemetry alone, the instrumentation is not complete. Do not open the PR.

---

## Checklist Before PR

- [ ] On-call questions defined upfront — every signal answers at least one
- [ ] Every log line carries `correlation_id`
- [ ] No PII in any log line
- [ ] RED metrics added for every new endpoint (`total`, `errors`, `duration`)
- [ ] Label values are bounded sets (no user IDs or error messages as labels)
- [ ] Alerts target user-visible symptoms, not infrastructure causes
- [ ] Every alert has a runbook link
- [ ] Staging verification passed — induced failures are findable via telemetry alone

---

## Hard Rules

- ❌ Never log PII — log IDs that reference the data, not the data itself
- ❌ Never use unbounded values as metric label values (cardinality explosion)
- ❌ Never alert on infrastructure causes — alert on user-visible symptoms
- ❌ Never ship instrumentation without staging verification
- ❌ Never leave an alert without a runbook link
