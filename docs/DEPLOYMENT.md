# ClauseRunner AWS Deployment and Infrastructure Guide

This guide records the deployment that is actually used by the public ClauseRunner demo.

---

## 1. Deployed Architecture

```text
Public HTTPS endpoint
        |
        v
Amazon ECS Express Mode (`default/clauserunner-web`, Fargate)
        |
        +-- Unified FastAPI API and compiled React/Vite assets
        +-- Amazon DynamoDB `clauserunner-state` (authoritative state)
        +-- Amazon S3 `clauserunner-contracts-772097700032-us-east-1` (artifact bucket)
        +-- Amazon CloudWatch Logs `/aws/ecs/default/clauserunner-web-2ef5`

Amazon EventBridge `clauserunner-obligation-check`
        +-- API Destination -> POST `/api/obligations/check-all`

GitHub Actions (OIDC) -> Amazon ECR `clauserunner-web` -> ECS rollout
```

The live URL is:

`https://cl-a7d669f525024e6a8413b2e0f7b851c8.ecs.us-east-1.on.aws/`

The frontend is not deployed through a separate S3 website, CloudFront distribution, or App Runner service. The ECS container serves both the API and compiled SPA assets.

---

## 2. Resource Naming and Safety

ClauseRunner resources use the `clauserunner-` prefix and live in `us-east-1`. Release verification uses the `clauserunner-dev` profile and never the AWS root profile.

Current resource identifiers are listed in [AWS_RESOURCES.md](AWS_RESOURCES.md). Do not create replacement resources merely to roll out a new application image.

---

## 3. DynamoDB Repository

Production uses the `clauserunner-state` table in `PAY_PER_REQUEST` mode. Every record has `SK = METADATA`; `PK` prefixes distinguish `CONTRACT#`, `CLAUSE#`, `OBLIGATION#`, `EVIDENCE#`, `INVESTIGATION#`, `ACTION#`, `APPROVAL#`, `EXECUTION#`, and `AUDIT#` records.

SQLite implements the same repository interface for local development and tests. It is not the database reported by the public deployment.

---

## 4. Build and Rollout

Pushes to `main` run the repository CI workflow and the ECR image workflow. GitHub Actions obtains temporary AWS credentials through OIDC by assuming `clauserunner-github-actions-role`; no long-lived AWS keys are stored in the repository.

The workflow builds the repository `Dockerfile`, compiles the React application, and pushes `clauserunner-web:latest` to ECR. The existing ECS Express Mode service is then rolled forward to resolve that image. A release does not require local Docker and must not create another service, cluster, load balancer, or hosting stack.

After rollout, verify `/health`, the public UI, the Golden SLA route, and `/api/audit?limit=100` before recording.

---

## 5. Bedrock and AgentCore Status

The Strands implementation targets Amazon Nova 2 Lite through `BedrockModel`, but live Amazon Bedrock inference remains pending AWS account authorization. The public runtime truthfully reports `strands_deterministic_mock` and `bedrock_configured=false`.

Amazon Bedrock AgentCore Runtime execution is also pending and is not part of the live request path. Do not describe either service as live until a successful authorized runtime invocation has been verified.
