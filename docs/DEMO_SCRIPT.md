# ClauseRunner Golden Demo Script

This walkthrough uses the repository's intended Acme SLA fixture. It does not create synthetic evidence during the presentation.

---

## Golden Scenario

- **Contract**: Acme Analytics Platform SaaS Agreement
- **Commitment**: 99.9% monthly uptime
- **Evidence**: March 2026 availability report showing 99.4% uptime
- **Deterministic remedy**: Tier 1, a 10% invoice credit worth $500

---

## Step 1: Open the Live Dashboard

1. Open [the public ClauseRunner application](https://cl-a7d669f525024e6a8413b2e0f7b851c8.ecs.us-east-1.on.aws/).
2. Confirm the header reports **LOCAL MOCK MODE**. This is the truthful current mode while Bedrock authorization remains pending.
3. Point out the live AWS service indicators and the **Golden SLA Demo** card.

## Step 2: Launch the Golden SLA

1. Select **Launch Golden SLA**.
2. Show the 99.9% commitment and the attached Acme March 2026 report.
3. Show that the report contains the intended 99.4% uptime evidence.

The fixture already contains this evidence. Do not attach another copy merely to manufacture the result. On a first cycle the obligation starts at `evidence_required`; after an earlier completed run it can begin a new periodic investigation cycle using the same demo fixture.

## Step 3: Run the Strands Investigation

1. Select **Trigger Strands Investigation**.
2. ClauseRunner moves the obligation through the valid `investigating` state.
3. The deterministic engine evaluates `99.4 < 99.9`, selects Tier 1, and calculates the 10% ($500) service credit.
4. The Strands workflow creates one proposed claim and one pending approval request. Repeated clicks while that request is active reuse the same action rather than creating duplicates.

## Step 4: Authorize the Remedy

1. Open **Approval Queue**.
2. Locate **Claim 10% Service Credit for March 2026 SLA Breach**.
3. Review the $500 impact and select **Approve**.
4. Confirm the request changes to `approved` and the ledger records the human decision.

## Step 5: Execute the Approved Claim

1. Open **Agreements**, select the Acme agreement, and open its uptime obligation.
2. Select **Execute Claim** on the approved action.
3. Confirm the obligation reaches `completed` and the execution result is persisted.

## Step 6: Show the Audit Ledger

1. Open **Audit Ledger**.
2. Show the evidence, investigation, action proposal, approval, and execution events.
3. Use **Load 100 older events** only if older history is needed. The first page stays responsive even when the full DynamoDB ledger contains thousands of records.
