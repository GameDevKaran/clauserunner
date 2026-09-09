# ClauseRunner Architecture Spec

This document details the software architecture, design principles, and technical boundaries of ClauseRunner, an autonomous post-signature contract operations system.

---

## 1. Core Philosophy: Autonomous Investigation, Controlled Execution

A core engineering principle of ClauseRunner is:
> **THE MODEL STATE IS NOT THE AUTHORITATIVE STATE.**

The Language Model (Amazon Bedrock / Strands Agent) is a powerful engine for **interpretation, synthesis, and planning**, but it does **not** own:
- Authoritative financial data or numeric calculations.
- Application state transitions (which are enforced deterministically by code).
- Consequential executions (e.g., executing service-credit claims or dispatching notices).

The Agent investigates, retrieves text, calculates recommendations via deterministic tools, and proposes actions. The **application code layer and human operator** hold the keys to state mutations and final action execution.

---

## 2. System Architecture

```
Web Interface (React/TS/Vite)
       │ (HTTP REST)
       ▼
FastAPI Operations Server
       │
       ├─► Storage Abstraction / Repository Interface
       │    ├─► LOCAL: SQLite DB (Authoritative State)
       │    └─► AWS CLOUD: Amazon DynamoDB (Authoritative State) & S3 (Documents)
       │
       ├─► Deterministic Business Logic (SLA & Renewal Engines)
       │
       └─► Strands Agent Runtime
            ├─► Amazon Bedrock (Claude 3.5 Sonnet Provider)
            └─► ClauseRunner Tools (Enforcing Code-Level Human Approval Policy)
```

---

## 3. Key Components

### A. Frontend Web Interface
- **React, TypeScript, and Vite** built as a single-page application (SPA).
- Communicates with the FastAPI backend over REST.
- Includes views for the main Dashboard, Agreements, Obligation Details, Human Approval Center, and visual Audit trail.

### B. FastAPI Backend
- Serves as the orchestration layer and schema validator (using Pydantic v2).
- Houses the deterministic rules engines (uptime credits, notice timelines).
- Exposes health checks and cloud-readiness monitoring.

### C. Strands Agentic Loop
- Built using the **Strands Agents SDK**.
- Uses `BedrockModel` to bind to Claude 3.5 Sonnet on AWS Bedrock.
- Invokes a tool list (`ALL_TOOLS`) to interact with obligations, retrieve text, and calculate numbers.
- Safe operational logs: The UI displays structured tool step outputs (`get_obligation`, `evaluate_numeric_threshold`) rather than exposing raw prompt thinking, guaranteeing user confidence and clean UX.

### D. ClauseRunner Tools (Approval Boundary)
- Registered as typed Strands tools.
- **Human Approval Policy in Code**: Standard alert actions run autonomously. Financial or notice actions (e.g., termination, service credit claims) are marked as `requires_approval = True`.
- `execute_approved_action` will query the database to find an authorized, human-signed `ApprovalRequest` in status `APPROVED`. If not found, execution is strictly blocked by python code.

### E. Storage Repository Abstraction
- Unified interface `StorageInterface` allows 100% credential-free local execution using **SQLite** with complete seeding of golden demo records.
- Ready for multi-table or single-table **Amazon DynamoDB** and **S3** adapters behind the identical repository interface.

### F. Amazon EventBridge Scheduler (Future Cloud Capability)
- Designed to run scheduled checks on approaching deadlines (such as renewal notices) so they trigger obligations autonomously without waiting for a user to log in.
