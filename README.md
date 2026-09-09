# ClauseRunner — Post-Signature Contract Operations Agent

> Autonomous professional operations agent turning signed vendor agreements into persistent operational obligations, monitoring compliance, and executing remedies under strict human-in-the-loop boundaries.

---

## Why ClauseRunner Exists

Once a contract is signed, it is often archived as a passive PDF. Critical operational obligations—such as monthly service level commitments (SLAs), automatic renewal notice windows, and SOC 2 submissions—are left unmonitored. 

**ClauseRunner turns contracts into active operational code.** It persistently monitors compliance evidence, conducts autonomous investigations using Claude 3.5 Sonnet on AWS Bedrock via Strands, maps violations to remedies, and prepares claim packages under strict deterministic code rules.

---

## Main Architecture & Golden Workflow

```
Web Interface (React/Vite) ◄──► FastAPI Backend ◄──► Strands Operations Agent 
                                                       │
                                                       ├─► Amazon Bedrock (Claude 3.5)
                                                       ├─► Storage Layer (SQLite/DynamoDB)
                                                       └─► Audit Trail (Immutability Ledger)
```

### The Golden Workflow (SLA Breach Remedy)
1. **Contract Traceability**: Acme SaaS Agreement is loaded. Uptime SLA obligation (99.9%) is tracked.
2. **Evidence Attached**: An uptime log demonstrating 99.4% availability (breach) is attached.
3. **Agent Investigation**: The Strands Agent retrieves the clause, inspects the log, and invokes the **deterministic engine** to calculate the remedy (Tier 1 applies, $500 Credit).
4. **Human Control Policy**: The agent drafts a service credit claim and submits it to the **Human Approval Queue** (since external claims are consequential).
5. **Human Authorization**: A manager approves the credit claim in the console.
6. **Dispatched Execution**: The operator executes the approved claim, dispatching the credit claim and saving the terminal state with a complete audit history.

---

## Local Setup & Quick Start

Ensure you have Python 3.14.1+ and Node.js installed.

### 1. Backend Setup & Run
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install requirements
pip install -r requirements.txt --prefer-binary

# Run FastAPI backend (port 8000)
uvicorn backend.main:app --reload
```

### 2. Frontend Setup & Run
```powershell
cd frontend

# Install Node packages
npm install

# Run Vite dev server (port 5173)
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Environment Configuration (`.env`)

Create a `.env` file in your root workspace. A safe blank `.env.example` is tracked for reference:
```text
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
CLAUSERUNNER_S3_BUCKET=
CLAUSERUNNER_DYNAMODB_TABLE=
```
*Note: If AWS Bedrock credentials are not present, ClauseRunner automatically runs in a fully functional **Local Mock Mode**, running local agentic loops on SQLite without failing.*

---

## Testing & Verifications

```powershell
# Run the automated backend test suite
python -m pytest backend/tests -v

# Run the frontend production compiler check
cd frontend
npm run build
```

---

## AWS Services Used
- **Amazon Bedrock**: Powering the Strands Agent loop via Claude 3.5 Sonnet.
- **Amazon S3**: For storing compliance documents and uptime log evidence.
- **Amazon DynamoDB**: Single-table design schema storing authoritative contract states and audit ledgers.
- **Amazon EventBridge Scheduler**: Scheduled obligation checker for expiring notice deadlines.

---

## Security Boundaries & Decoupling
- **Server-Side Decoupling**: All boto3, Bedrock, and secret environment calls are executed on the server. The public React frontend is 100% credential-free.
- **Human Approval Policy in Code**: Financial and notice operations strictly block execution unless a corresponding human authorization is present in our database.

---

## License

This project is licensed under the **MIT License**—see the [LICENSE](LICENSE) file for details.
