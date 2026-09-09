# ClauseRunner Test Suite Guide

ClauseRunner prioritizes automated test coverage as a core engineering standard. Our backend and frontend tests validate our state machine, deterministic calculations, human-in-the-loop control policies, and REST API contracts.

---

## 1. Backend Automated Unit Tests

We use `pytest` and `FastAPI TestClient` for full-range backend testing. Our test suite runs completely credential-free, leveraging database mocks and in-memory isolated SQLite structures.

### What is Covered
- **SLA calculations**: Verifies compliance calculations, breach detections, and correct tier mappings ($500 vs $1000 credit).
- **Obligation State Machine**: Verifies valid transitions and asserts that invalid transitions throw `InvalidStateTransition` exceptions.
- **Repository CRUD**: Verifies the SQLite Mixin structure, schema loading, seeding, and database operations.
- **Human Approval Policy Boundary**: Asserts that trying to execute a consequential proposed action (such as a financial claim) *without* explicit human authorization is strictly blocked by code, and executes successfully once approved.
- **REST Endpoints**: Integrates `TestClient` to verify health checks, contracts listing, and obligation data REST payloads.

### Running Backend Tests
Ensure your virtual environment is active:
```powershell
# Activate .venv
.\.venv\Scripts\activate

# Run Pytest
python -m pytest backend/tests -v
```

---

## 2. Frontend Build Verification

Our frontend is fully type-safe, written in TypeScript, and uses Vite for compilation. We verify static analysis and production assets generation on every build.

### Running Frontend Compilation
Navigate into the `frontend` directory:
```powershell
cd frontend

# Install Node modules
npm install

# Run static TypeScript compiler (tsc) and build bundle
npm run build
```
Vite compiles the assets under `frontend/dist/` with **0 errors**, assuring robust deployment-readiness.
