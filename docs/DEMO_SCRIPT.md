# ClauseRunner Golden Demo Script

This script walks through the **Golden SaaS SLA Breach Workflow** step-by-step, showing how ClauseRunner investigates evidence, calculates compliance, proposes remedies, enforces human boundaries, and commits immutable audit events.

---

## The Fictional Golden Scenario
- **Contract**: Acme Analytics Platform SaaS Agreement.
- **Commitment**: 99.9% Monthly Uptime commitment. If breached, Tier 1 (< 99.9% but >= 99.0%) triggers a **10% invoice credit ($500)**.
- **Evidence**: March 2026 uptime log demonstrating **99.4% uptime** (a breach).

---

## Step-by-Step Walkthrough

### Step 1: Initialize and Launch
1. Ensure the backend is running (`uvicorn backend.main:app --reload`).
2. Ensure the React frontend is running (`npm run dev` in `frontend`).
3. Open `http://localhost:5173` in your browser.
4. Observe the top right header:
   - Displays **LOCAL MOCK MODE** (or **AWS BEDROCK LIVE** if configured) and tells you the database is healthy.
   - The dashboard displays **2 Agreements**, **3 Active Obligations**, and **1 Approval Pending** (from our pre-seeded SOC 2 agreement).

### Step 2: Access the Golden Obligation
1. On the dashboard, locate the card on the right labeled **Golden SLA Demo**.
2. Click **Launch Golden SLA**.
3. This opens the **SLA Obligation Detail View**:
   - The status is currently `evidence_required` (waiting for the March server report).
   - Traceable Clauses show Section 4.1 (Uptime Commitment) and Section 4.3 (Remedy tiers) loaded directly from the SaaS agreement text.

### Step 3: Load March Evidence Logs
1. Click the **Load March Logs** button in the "Attached Evidence Artifacts" panel.
2. Observe:
   - An evidence artifact is created for the *March 2026 Availability Report* (pointing to S3).
   - The obligation status immediately transitions to **`investigating`** (the valid state transition in our deterministic state machine).
   - A new item is added to our immutable **Operational Audit Trail** timeline.

### Step 4: Run the Strands Operations Agent
1. Click the button **Trigger Strands Investigation**.
2. Observe:
   - The system executes the agentic loop.
   - It performs its investigation, invoking tools step-by-step: `get_obligation`, `get_contract`, `list_evidence`, `evaluate_numeric_threshold`, `propose_action`, and `request_approval`.
   - **The deterministic engine** evaluates `99.4 < 99.9` -> detects a breach -> maps it to Tier 1 -> calculates exactly **10% ($500.00)** credit.
   - It drafts the email claim to `vendor-claims@acme-analytics.com` and automatically places it in the **Human Approval Queue** (since financial claims are consequential).
   - The status transitions to **`approval_required`**.

### Step 5: Authorize the Remedy Claim
1. In the sidebar, click on **Approval Queue**.
2. Locate the pending request: **Claim 10% Service Credit for March 2026 SLA Breach**.
3. Review the potential impact ($500 credit), the draft email, and comments.
4. Click **Approve**.
5. Observe:
   - The request status becomes `approved`.
   - The audit ledger commits a new `approval_granted` event with the operator name ("Human Operations Manager").

### Step 6: Dispatch the Approved Action
1. Navigate back to **Agreements** -> click the Acme contract -> open the Uptime SLA obligation.
2. Locate the "Proposed Remedy Claim Draft" panel.
3. The action status is now **`approved`** and the button **Execute Claim** is active.
4. Click **Execute Claim**.
5. Observe:
   - The claim runs its execution tool (mimicking a dispatch of the credit claim).
   - The obligation transitions to its final terminal state: **`completed`**.
   - Review the Immutable Audit Ledger to see the entire unbroken chain: `obligation_created` -> `evidence_attached` -> `action_proposed` -> `approval_granted` -> `action_executed`.
