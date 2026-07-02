# Aegis AI

> An autonomous multi-agent AI security engineering platform.

## Recent Updates
* **Robust Gemini Integration:** Fully integrated Google Gemini models with automatic `.env` loading and synchronous thread-pool isolation to prevent SDK rate limits (429s) from blocking the FastAPI event loop.
* **Graceful AI Degradation:** Added a dynamic, regex-based mock generation service. If the Gemini API is unavailable or rate-limited, the system seamlessly falls back to local contextual mock generation without hanging the UI.
* **Synchronized SSE Dashboard:** Fixed React Query cache invalidation and Server-Sent Event (SSE) mappings in the Next.js frontend. The UI now perfectly tracks the state of the `security`, `patch`, `enhancement`, and `repository` agents in real-time, including artificial async delays so users can physically watch the AI "think" and process vulnerabilities.

* **Phase 1: Architecture & Framework**
  * ✅ M0: Foundation (FastAPI, Next.js, Auth, DB)
  * ✅ M1.1: Core Agent Framework (Domain Events, BaseAgent)
  * ✅ M1.2: Supervisor Agent (Execution Plans)
  * ✅ M1.3: Repository Agent (Filesystem indexing)
  * ✅ M1.4: Agent Execution Infrastructure (In-memory engine, State Machine)
* **Phase 2: Security & Analysis**
  * ✅ M1.5: Security Analysis Agent (Static Rules Engine)
  * ✅ M1.6: Execution API & Application Services
  * ✅ M1.7: Frontend Dashboard Implementation
* **Phase 3: Remediation & Reporting**
  * ✅ M1.8: Patch Generation Agent

**Aegis AI** runs a team of specialised AI agents that independently plan and execute a complete security audit — from vulnerability discovery through patch generation, validation, and professional report production.

---

## Architecture

```
User Browser (Next.js)
      │ HTTPS + SSE
FastAPI Backend (Python 3.12)
      │
 ┌────┴──────────────────────────┐
 │  Google ADK Agent Runtime     │
 │  Supervisor → Repo → Security │
 │  → Patch → Documentation      │
 └────┬──────────────────────────┘
      │
 PostgreSQL + Redis
```

---

## Quick Start (Local Development)

### Prerequisites

| Tool | Version |
|---|---|
| Python | 3.12+ |
| Node.js | 20+ |
| Docker Desktop | Latest |
| uv | Latest (`pip install uv`) |

### 1. Clone and configure

```bash
git clone https://github.com/your-org/aegis-ai
cd aegis-ai
cp .env.example .env
# Edit .env — fill in CLERK_SECRET_KEY, GEMINI_API_KEY, CLERK_JWKS_URL
```

### 2. Start infrastructure (PostgreSQL + Redis)

```bash
docker-compose up postgres redis -d
```

### 3. Set up and start the backend

```bash
cd aegis-backend

# Create virtual environment and install dependencies
uv venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

uv pip install -e ".[dev]"

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn aegis.main:app --reload --port 8000
```

### 4. Set up and start the frontend

```bash
# New terminal
cd aegis-frontend
npm install
npm run dev
```

### 5. Open the application

```
http://localhost:3000
```

---

## Full Docker Stack

```bash
# Build and start all services
docker-compose up --build

# Verify all services are healthy
docker-compose ps

# Run migrations against the Docker database
docker-compose exec backend alembic upgrade head
```

---

## Running Tests

```bash
cd aegis-backend
pytest tests/ -v
```

---

## Project Structure

```
aegis-ai/
├── aegis-backend/          # FastAPI + Python 3.12
│   ├── src/aegis/
│   │   ├── domain/            # Pure Python entities (no framework deps)
│   │   ├── application/       # Use cases and services
│   │   ├── infrastructure/    # DB, agents, MCP clients, queue
│   │   └── interface/         # FastAPI routers and middleware
│   ├── alembic/               # Database migrations
│   └── tests/                 # pytest test suite
├── aegis-frontend/         # Next.js 14 App Router (TypeScript)
│   └── src/app/               # App Router pages
├── aegis-mcp-servers/      # Custom MCP servers (added M1+)
├── infrastructure/docker/     # Dockerfiles
├── .github/workflows/         # GitHub Actions CI
└── docker-compose.yml
```

---

## Milestone Status

| Milestone | Status | Description |
|---|---|---|
| **M0** | ✅ Complete | Foundation: backend, frontend, DB, auth, Docker |
| **M1** | ✅ Complete | Agent framework: ADK, Supervisor, Repo Agent, SSE |
| **M2** | ✅ Complete | Security analysis: Deterministic Rules & Gemini AI |
| **M3** | ✅ Complete | Patch generation and approval flow |
| **M5** | ✅ Complete | PDF/JSON report generation |
| **M6** | ✅ Complete | Full premium dashboard with real-time SSE updates |

---

## Environment Variables

See [`.env.example`](.env.example) for the complete list with descriptions.

---

## API Documentation

When the backend is running:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)
