# Aegis AI Development Guide

This document tracks the ongoing architectural decisions and development milestones for the Aegis AI project.

## Current Architecture

**Clean Architecture + Modular Monolith**
Aegis AI relies on strict separation of concerns:
- `domain/`: Pure Python entities and events (zero external dependencies).
- `application/`: Business rules, ports/interfaces, and the core agent framework.
- `infrastructure/`: Adapters (SQLAlchemy, external API clients, message queues).
- `interface/`: Delivery mechanisms (FastAPI endpoints, background worker wrappers).

We use `pydantic` V2 for all data models and strict typing throughout.

## Completed Milestones

### Milestone 0: Foundation Complete ✅
- **Stack**: FastAPI, Next.js 14, Tailwind v4, PostgreSQL, Redis.
- **Auth**: Clerk JWT with manual RSA verification (avoiding Clerk SDK bloat).
- **Setup**: Docker-compose, complete CI pipeline.

### Milestone 1.1: Core Agent Framework ✅
- **Objective**: Establish the foundation for AI agents without external runtime dependencies.
- **Implementation**:
  - Defined pure Python Domain Events (`AgentEvent`).
  - Created execution models (`AgentState`, `AgentContext`, `AgentResult`, `WorkItem`).
  - Extracted abstract Ports (`EventBus`, `Logger`, `ConfigProvider`).
  - Implemented the `BaseAgent` using the Template Method pattern to enforce a unified lifecycle and automatic event emission.
  - Implemented a `WorkItemRegistry` to decouple agent instantiation from the task queue.
  - Test suite validated with 100% coverage on framework logic.

### Milestone 1.2: Supervisor Agent ✅
- **Objective**: Build the initial planning layer of the multi-agent system.
- **Implementation**:
  - Implemented `SupervisorAgent` inheriting from `BaseAgent`.
  - Supervisor analyzes context and writes a deterministic `ExecutionPlan` to `shared_state` to be executed by subsequent agents.
  - Successfully emitted `PROGRESS` and `COMPLETE` events reflecting lifecycle transitions.
  - Validated via 100% test coverage.

### Milestone 1.3: Repository Agent ✅
- **Objective**: Implement the `RepositoryAgent` to index a target project's filesystem and dependencies.
- **Implementation**:
  - Implemented safe, pure-python `pathlib` BFS traversal.
  - Skips heavy/irrelevant directories (`node_modules`, `.git`, `.venv`, etc).
  - Detects frameworks, languages, and configuration files via heuristics.
  - Outputs a strongly-typed `RepositoryManifest`.
  - 100% test coverage using Pytest `tmp_path`.

### Milestone 1.6: Execution API & Application Services [COMPLETED]

**Objective:**
Expose the existing agent pipeline (Supervisor, Repository, Security) through a production-quality FastAPI layer, without adding new business logic.

**Deliverables:**
*   [x] Designed the `AnalysisService` to act as an application layer facade.
*   [x] Implemented Pydantic v2 schemas (`projects.py`, `execution.py`) in `src/aegis/interface/api/models/`.
*   [x] Created API exception definitions and global exception handlers (`exceptions.py`).
*   [x] Re-structured the `health.py` endpoint for MVP architecture (volatile memory).
*   [x] Implemented `projects.py` router to accept ZIP/local path uploads and dispatch analysis in a `BackgroundTask`.
*   [x] Implemented `execution.py` router to query in-memory status, timeline, and findings via `SessionManager`.
*   [x] Verified functionality via unit/integration tests (`pytest tests/interface/api/`). for concurrency, state validation, and error catching.

### Milestone 1.8: Patch Generation Agent [COMPLETED]

**Objective:**
Implement a safe, read-only Patch Generation Agent that leverages deterministic patterns to transform security vulnerabilities into actionable patches.

**Deliverables:**
*   [x] Added Domain Models `Patch`, `PatchCollection`, and `PatchExplanation` with fields for `estimated_review_time`, `insertions`/`deletions`, and structured remediation details.
*   [x] Added `PatchQuality` Enum.
*   [x] Integrated `PatchGenerationStarted`, `PatchGenerated`, `PatchValidated`, `PatchSkipped`, and `PatchGenerationCompleted` events into `AgentEventType`.
*   [x] Implemented `UnifiedDiffGenerator` wrapping `difflib.unified_diff` to seamlessly use real surrounding file context from disk (without writing to it).
*   [x] Implemented `DeterministicPatchGenerator` with static fallback rules mapping to SQL Injections, Hardcoded Secrets, XSS, and Dependency pinning.
*   [x] Wired `PatchGenerationAgent` into the `SupervisorAgent` execution pipeline.
*   [x] Enforced strict read-only guarantees (no mutable write operations occur).
*   [x] Fully validated logic via PyTest.

**Objective:**
Build the first complete Aegis AI frontend to showcase the backend's autonomous capabilities in a premium, minimal, dark-mode-first dashboard.

**Deliverables:**
*   [x] Initialized Next.js frontend with TailwindCSS v4 and React Query.
*   [x] Implemented API proxy routes (`/api/...`) to safely route traffic to FastAPI.
*   [x] Built the **Landing Page** with a sleek hero section and architecture overview.
*   [x] Built the **Dashboard** with polished empty states and form integration.
*   [x] Built the **Execution Details** page featuring:
    *   Animated Agent Status Cards tracking execution progress.
    *   Repository Overview Card summarizing frameworks, languages, and dependencies.
    *   Execution Timeline updating automatically via polling.
    *   Expandable Findings Table with a deterministic AI Reasoning panel.
*   [x] Ensured strict TypeScript types throughout the application state.
- **Objective**: Establish the core runtime engine for the multi-agent system.
- **Implementation**:
  - Implemented an in-memory execution pipeline decoupled from security scanning.
  - Created strict state machine `ExecutionSession` acting as the single source of truth.
  - Created `AgentExecutor` to sequentially run agents given an execution plan.
  - Replaced EventSink/HistoryBuffer with a direct `SessionEventBus` that appends events to the session in memory.
  - Built an API endpoint `GET /api/v1/audits/{audit_id}/execution` exposing the live session state.
  - Validated lifecycle with 100% test coverage for concurrency, state validation, and error catching.

## Known Issues & Technical Debt
- The execution session is stored strictly in memory (`SessionManager`). If the server restarts, live status is lost.
- The Supervisor Plan is Mocked and synchronous.
- The `AgentContext.shared_state` dictionary is mutable.

### Milestone 1.5: Security Analysis Agent ✅
- **Objective**: Implement the core static analysis capabilities without LLM integration.
- **Implementation**:
  - Implemented `SecurityAnalysisAgent` which utilizes a `RuleEngine`.
  - Established a generic `SecurityRule` interface supporting concurrent rule execution.
  - Developed pure Python domain models: `Finding`, `Severity`, `Confidence`, and `ScanResult`.
  - Implemented 4 highly targeted rules avoiding generic regex soup:
    - **SQL Injection**: Detects unsafe f-strings, `.format()`, template literals, and concatenation.
    - **Hardcoded Secrets**: Curated high-fidelity patterns for AWS, Stripe, Google, GitHub, and RSA keys.
    - **Cross Site Scripting (XSS)**: Flags `dangerouslySetInnerHTML` and unsafe Jinja/Django templates.
    - **Vulnerable Dependencies**: Scans `package.json` and `requirements.txt` against a local dummy CVE dictionary.
  - The `RuleEngine` cleanly separates detection logic from agent orchestration and is strictly immutable.
  - Added new lifecycle events: `SECURITY_SCAN_STARTED`, `RULE_STARTED`, `FINDING_DETECTED`, `RULE_COMPLETED`, and `SECURITY_SCAN_COMPLETED`.
  - Unit tests generated for all components with positive, negative, and false-positive cases.

## Known Issues & Technical Debt
- The execution session is stored strictly in memory (`SessionManager`). If the server restarts, live status is lost.
- The Supervisor Plan is Mocked and synchronous.
- The `AgentContext.shared_state` dictionary is mutable.
- Vulnerable Dependencies rule relies on a hardcoded local mock dictionary rather than an online CVE database.

## Next Milestone

### Milestone 1.6: LLM Vulnerability Validation
- Introduce the Gemini Model wrapper.
- Use Gemini to validate the statically found vulnerabilities to filter out false positives before saving the `ScanResult`.
