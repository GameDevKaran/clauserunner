# ClauseRunner AWS Resources Catalog

This document details the exact resources provisioned on Amazon Web Services (AWS) specifically for the ClauseRunner hackathon project, following our mandatory safety and naming standards.

---

## 1. Catalog of Provisioned Resources

| Resource Type | Resource Identifier | Region | Purpose | Required for Judging? |
| :--- | :--- | :--- | :--- | :--- |
| **Amazon S3 Bucket** | `clauserunner-contracts-772097700032-us-east-1` | `us-east-1` | Stores compliance documents and PDF/JSON evidence logs. | **Yes** |
| **Amazon DynamoDB Table** | `clauserunner-state` | `us-east-1` | Single-table metadata store for active contracts, traceable clauses, operational obligations, approval request queues, and audits. | **Yes** |
| **Amazon ECR Repository** | `clauserunner-web` | `us-east-1` | Stores the unified ClauseRunner container image (Docker) for ECS Express Mode. | **Yes** |
| **Amazon EventBridge Schedule** | `clauserunner-obligation-check` | `us-east-1` | Scheduled check trigger that periodically evaluates approaching notice and compliance windows. | **Yes** |

---

## 2. Resource Verification Proofs

- **S3 Bucket Verification**: S3 put/get/delete and full KMS-AES256 default encryption have been successfully verified using the `clauserunner-dev` credentials.
- **DynamoDB Single-Table**: Fully provisioned under Pay-per-Request (`PAY_PER_REQUEST`) capacity and successfully seeded with golden contracts, traceable clauses, obligations, and evidence log records.
- **Amazon ECR Repository**: Repository `clauserunner-web` is created and verified successfully.

---

## 3. Deployment Automation Tools

- **`deploy_ecs.ps1`**: Located in the project root, this PowerShell script compiles local React assets, authenticates Docker to ECR, builds/tags/pushes the Docker image, and triggers service creation on `aws ecs create-express-gateway-service` using the owner's provisioned IAM roles.
