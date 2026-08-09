---
name: api-contract-testing
description: >
  Prevent API contract drift between frontend/backend and third-party
  integrations. Validates every response against the OpenAPI schema, fuzzes
  the API with property-based tests (Schemathesis), and uses consumer-driven
  contracts (Pact) where services are independently deployed. Catches the
  highest-severity backend gap: an API that changes shape without breaking
  the contract. Triggers include "contract test", "schemathesis", "openapi",
  "api contract", "pact", "schema validation", "fuzz the api", "api drift".
---

# Skill: API Contract Testing

**When to invoke:** Any task that adds or changes an API endpoint, modifies a
DTO/response model, changes request/response schemas, or integrates with a
third-party API. Also when two services are deployed independently and could
drift. This skill prevents the most common backend prod-outage class: **API
contract drift** — where the producer changes the response shape and consumers
break silently.

> **Why contract testing?** Unit and integration tests verify *your* code against
> *your* expectations. Contract tests verify the *actual wire format* matches the
> *documented schema*. The producer and consumer can drift apart without either
> side's tests failing — until production.

---

## Core Concept

> Three layers, each catching a different drift class:

| Layer | Tool | What it catches |
|---|---|---|
| **Schema validation** | OpenAPI + response validator | Every response matches the documented schema |
| **Property-based fuzzing** | Schemathesis | Malformed/unexpected inputs, edge-case status codes |
| **Consumer-driven contracts** | Pact | Producer/consumer shape drift across deploy boundaries |

Drift is **expensive to find late** — this skill finds it at the API boundary,
before it reaches production.

---

## Protocol

### Step 0 — Detect the API Surface

- [ ] Locate the OpenAPI schema (FastAPI auto-generates `/openapi.json`; or `openapi.yaml` at repo root).
- [ ] Determine the API framework (FastAPI / Express / tRPC / etc.) and test runner.
- [ ] Identify which consumers depend on the changed endpoints (frontend, mobile, third-party).

### Step 1 — Schema Validation (always)

Validate every API response against the OpenAPI schema. This catches shape
changes (missing/renamed fields, wrong types) before consumers break.

**FastAPI + pytest** — add a response-contract check to your integration tests:

```python
# backend/tests/integration/test_api_contract.py
import json
import pytest
from openapi_spec_validator import validate_spec
from schemathesis import from_persistent

def test_openapi_schema_is_valid(client):
    """The auto-generated OpenAPI schema itself must be valid."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    validate_spec(response.json())

def test_response_matches_schema(client):
    """Every response the client sees must conform to the documented schema."""
    r = client.get("/users/1")
    assert r.status_code == 200
    # Validate the response body against the User schema from OpenAPI
    schema = client.get("/openapi.json").json()
    user_schema = schema["components"]["schemas"]["User"]
    # Use a validator (e.g. jsonschema) to check r.json() against user_schema
```

**CI enforcement** — add an OpenAPI validator to the quality gate:

```bash
# Validate the spec file on every PR (Spectral or openapi-spec-validator)
npx @stoplight/spectral-cli lint openapi.yaml
# or
openapi-spec-validator openapi.yaml
```

- [ ] `/openapi.json` validates
- [ ] Every changed endpoint's responses match their documented schema

### Step 2 — Property-Based Fuzzing (Schemathesis)

Fuzz the API with Schemathesis to find inputs that produce unexpected behavior
(500s instead of 4xx, response schema violations, crashes).

**Install:** `pip install schemathesis`

**Run against the live app (FastAPI):**

```bash
# Fuzz the whole API from the OpenAPI schema
schemathesis run --base-url http://localhost:8000 http://localhost:8000/openapi.json \
  --checks all --hypothesis-max-examples=50
```

**As a pytest plugin (runs in CI):**

```python
# backend/tests/e2e/test_api_fuzz.py
import schemathesis

# Load the schema once; generates property-based tests from it
schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

@schema.parametrize()
def test_api_contract_holds(case):
    """Any input generated from the schema must produce a valid response."""
    case.call_and_validate()
```

**Gotchas:**
- Add `schemathesis` to the `pytest` config via `[tool.schemathesis]` in `pyproject.toml` to set base URL / auth.
- For auth-protected endpoints, add a `Schemathesis` hook to inject auth headers.
- Start with `--hypothesis-max-examples=50` (fast), raise in CI.

### Step 3 — Consumer-Driven Contracts (Pact, for independently deployed services)

Use Pact when services are deployed independently and could drift (e.g. a
separately-deployed backend consumed by microservices or a mobile app).

- **Consumer** writes a Pact (expected request → expected response).
- **Producer** verifies it (its responses match the consumer's expectations).
- CI fails if either side drifts.

> **When to skip:** If it's a single monolith where frontend and backend deploy
> together, schema validation + Schemathesis are sufficient — Pact adds overhead
> that buys little. Use Pact only across real deploy boundaries.

---

## Verification / Gate

This skill is done when:

- [ ] OpenAPI schema validates (`openapi-spec-validator` passes)
- [ ] Every changed endpoint's responses match the documented schema
- [ ] Schemathesis fuzzing passes (no response-schema violations, no unexpected 5xx)
- [ ] If separately deployed services: Pact contracts verified on both sides
- [ ] CI includes the schema validation + fuzz step

If any endpoint's response drifts from its schema, fix the schema or the code —
**never** silently disable the check.

---

## Hard Rules

- ❌ Never change a response shape without updating the OpenAPI schema in the same PR
- ❌ Never disable a failing contract check to merge — fix the drift
- ❌ Never claim "responses match the schema" without running the validator
- ❌ Never add `--psyco`/`--hypothesis-suppress-health-check` to hide real failures
- ❌ Never mark an API task done until the contract test passes
