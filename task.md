# TraceGuard Implementation Tasks

## Phase 1: The Core Primitives (Month 1)
- `[x]` Initialize Monorepo structure (Python root with `traceguard-sdk`)
- `[x]` Setup `traceguard-sdk` Python package boilerplate (pyproject.toml, pytest, mypy)
- `[/]` Implement OpenTelemetry trace capture decorators (`@traceguard.observe`)
- `[ ]` Implement async local SQLite trace syncing
- `[ ]` Create unit tests for core tracing logic

## Phase 2: The Statistical Runner & Fuzzer (Months 2-3)
- `[ ]` Setup `traceguard-run` Python CLI package
- `[ ]` Implement basic LLM-as-a-judge evaluators
- `[ ]` Implement Bootstrap Confidence Intervals math engine (NumPy/SciPy)
- `[ ]` Implement KS tests and PSI logic
- `[ ]` Build tool-boundary fuzzer engine
- `[ ]` Create test suite for math and fuzzing logic

## Phase 3: Dataset Curation & CI/CD (Month 4)
- `[ ]` Implement `traceguard-curate` failure detection pipeline
- `[ ]` Create `traceguard promote` CLI command
- `[ ]` Build GitHub Actions custom runner / action.yml
- `[ ]` Generate Markdown report templates for PRs

## Phase 4: The Enterprise Cloud Dashboard (Month 5)
- `[ ]` Initialize Next.js App Router project
- `[ ]` Setup UI with TailwindCSS and glassmorphism styling
- `[ ]` Configure Prisma ORM and Supabase/PostgreSQL connection
- `[ ]` Build trace visualization components (React Flow)
- `[ ]` Build dataset curation UI

## Phase 5: Production Readiness & Scale (Month 6)
- `[ ]` Implement RBAC
- `[ ]` Setup API key management
- `[ ]` Add SOC2 compliance logging basics
- `[ ]` Deploy hosted evaluation infrastructure
