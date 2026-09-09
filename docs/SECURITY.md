# ClauseRunner Security Review

This document contains a comprehensive review of the security controls, boundaries, credential policies, and static code protection practices implemented within ClauseRunner.

---

## 1. Zero Credentials Leakage Policy

ClauseRunner strictly enforces a zero-tolerance policy against committing real cloud credentials, API keys, or operational environment secrets into Git, screenshots, or logs.

### Protection Controls
- **`.gitignore` Enforced**: `.env` and all other environmental variants (`.env.local`, `.env.development`) are explicitly ignored by Git. Only safe blank examples (`.env.example`) are tracked.
- **Backend-Only Decoupling**: All administrative and runtime cloud interaction calls (such as Bedrock invocations via boto3 or Strands) occur strictly on the **server-side** (FastAPI). No AWS credentials, access tokens, or account IDs are ever exposed or served to the React frontend or compiled browser bundle.
- **Sanitized Logging**: Standard logger configurations strictly filter and sanitize fields like `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and bearer headers to prevent them from leaking into AWS CloudWatch, local files, or console outputs.

---

## 2. Human Execution Control Boundary

ClauseRunner implements a hard **Human Approval Execution Boundary** directly in the Python codebase rather than relying on weak LLM prompt instructions:
- Low-risk internal actions (logging, audit creation, calculating values) run autonomously.
- Consequential actions (financial claims, termination notices, legal renewals) are hard-coded in our business rules as `requires_approval = True`.
- The database execution guard `execute_approved_action` explicitly checks for a correspondly matched `ApprovalRequest` with `status == ApprovalStatus.APPROVED`. If not found, execution is immediately **blocked by the application server** and logged as an alert.

---

## 3. Strict Naming Policy Prefix

To guarantee that ClauseRunner cannot accidentally interfere with other unrelated projects or generic resources, all IAM roles, DynamoDB tables, S3 buckets, and EventBridge schedulers are provisioned with an unmistakable prefix:

> `clauserunner-`

---

## 4. Static Secret Code Scanning

Before every repository push or checkpoint commit, the following regex patterns are audited across our workspace:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `BEGIN PRIVATE KEY`
- `password=`
- `token=`

Any occurrence of static credentials in code triggers a block of deployment pipelines.
