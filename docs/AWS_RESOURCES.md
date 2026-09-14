# ClauseRunner AWS Resources Catalog

This document details the exact resources provisioned on Amazon Web Services (AWS) specifically for the ClauseRunner hackathon project, following our mandatory safety and naming standards.

---

## 1. Catalog of Provisioned Resources

| Resource Type | Resource Identifier | Region | Purpose | Required for Judging? |
| :--- | :--- | :--- | :--- | :--- |
| **Amazon ECS Express Mode service** | `default/clauserunner-web` | `us-east-1` | Runs the unified FastAPI and React container on Fargate and exposes the public endpoint. | **Yes** |
| **Amazon S3 Bucket** | `clauserunner-contracts-772097700032-us-east-1` | `us-east-1` | Private, encrypted artifact bucket provisioned for compliance documents and evidence objects. | **Yes** |
| **Amazon DynamoDB Table** | `clauserunner-state` | `us-east-1` | Single-table metadata store for active contracts, traceable clauses, operational obligations, approval request queues, and audits. | **Yes** |
| **Amazon ECR Repository** | `clauserunner-web` | `us-east-1` | Stores the unified ClauseRunner container image (Docker) for ECS Express Mode. | **Yes** |
| **Amazon EventBridge scheduled rule** | `clauserunner-obligation-check` | `us-east-1` | Invokes the obligation checker through `clauserunner-api-destination` every five minutes. | **Yes** |
| **Amazon CloudWatch Logs** | `/aws/ecs/default/clauserunner-web-2ef5` | `us-east-1` | Receives application and access logs from the ECS service. | **Yes** |
| **AWS CodeBuild Project** | `clauserunner-container-build` | `us-east-1` | Available as an optional remote container builder. Current `main` image builds use GitHub Actions. | No |

---

## 2. Resource Verification Proofs

- **ECS Express Mode**: Service status is `ACTIVE`, desired/running task count is `1/1`, and the public ingress health check uses `/health`.
- **S3 Bucket**: The bucket is live in `us-east-1`, blocks public access, and uses SSE-S3 (`AES256`) default encryption.
- **DynamoDB Single-Table**: Table status is `ACTIVE` with `PAY_PER_REQUEST` billing and production contract, obligation, approval, and audit state.
- **Amazon ECR**: Repository `clauserunner-web` is live and contains the tagged production image.
- **Amazon EventBridge**: Rule `clauserunner-obligation-check` is `ENABLED`. Its API Destination is `ACTIVE`, uses `POST`, and its target assumes the dedicated `clauserunner-eventbridge-role`.
- **Amazon CloudWatch**: The ECS log group exists and contains current health and request records.
- **Pending services**: Amazon Bedrock Nova 2 Lite live inference and Amazon Bedrock AgentCore Runtime execution are not verified or presented as live.

---

## 3. Deployment Automation Tools

- **GitHub Actions OIDC**: Pushes to `main` run CI and build the container image without committed long-lived AWS credentials. The deployment workflow assumes `clauserunner-github-actions-role` through GitHub's OIDC provider and pushes `latest` to ECR.
- **AWS CodeBuild**: `clauserunner-container-build` remains available as an alternate remote builder. It is not the current `main` image-build path.
- **ECS rollout**: The existing ECS Express Mode service is updated to resolve the newly pushed ECR image; no parallel deployment infrastructure is used.

