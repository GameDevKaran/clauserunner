# ClauseRunner AWS Deployment & Infrastructure Guide

This guide details how to package, deploy, and host ClauseRunner on Amazon Web Services (AWS) using industry standard cloud-native designs.

---

## 1. Deployed AWS Architecture Overview

```
Frontend Assets (S3) ──► Amazon CloudFront (HTTPS Content Delivery Network)
                                  │
                                  ▼
FastAPI Backend (AWS App Runner / ECS Fargate)
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
S3 Evidence Bucket (Artifacts)               DynamoDB Single-Table (State)
`clauserunner-evidence-...`                  `clauserunner-state-...`
```

---

## 2. Mandatory Naming Naming Policies & Safety

To prevent accidental interactions with other AWS accounts or unrelated client environments, **all ClauseRunner cloud resources MUST use an unmistakable prefix**:

> `clauserunner-`

### Examples
- **Amazon S3 Buckets**: `clauserunner-contracts-evidence-[account-id]`
- **Amazon DynamoDB Tables**: `clauserunner-state-[environment]`
- **Amazon EventBridge Schedules**: `clauserunner-events-checking`
- **IAM Policies / Roles**: `clauserunner-runtime-execution-role`

---

## 3. Storage Adapters (DynamoDB & S3)

ClauseRunner's repository layer is abstracted behind `StorageInterface` to support seamless database swapping.

### DynamoDB Schema
For AWS, we map all tables (Contracts, Clauses, Obligations, Actions, Approvals, Executions, Audit Logs) into a single, high-performance table `clauserunner-state` utilizing a **Single-Table Design**:
- **Partition Key (PK)**: `CONTRACT#[id]` or `OBLIGATION#[id]` or `APPROVAL#[id]`
- **Sort Key (SK)**: `METADATA` or `CLAUSE#[id]` or `AUDIT#[timestamp]`

---

## 4. Deployed Hosting Environments

### A. Frontend Hosting
The React + TS + Vite production build (`dist/` folder) is uploaded to an **Amazon S3** bucket configured for static web hosting and served securely using **Amazon CloudFront** with a custom SSL certificate:
```powershell
aws s3 sync frontend/dist s3://clauserunner-web-hosting-bucket/ --delete
```

### B. FastAPI Backend Hosting
The Python backend is packaged as a Docker container and deployed to **AWS App Runner** or **Amazon ECS Fargate**. 

Dockerfile structure:
```dockerfile
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --prefer-binary
COPY . .
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 5. Amazon Bedrock Access
Ensure that Bedrock model access is enabled on your AWS console for the Anthropic Claude 3.5 Sonnet model. The deployed backend service must be attached to an IAM execution role containing Bedrock invocation policies:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    }
  ]
}
```
