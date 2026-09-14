# ClauseRunner Cost and Cleanup Guide

ClauseRunner uses managed AWS services and a single small ECS Express Mode task to keep the hackathon demo low maintenance. Actual charges depend on account credits, free-tier eligibility, storage, requests, data transfer, and task uptime.

This guide details our cost profile and provides precise instructions for safe post-judging cleanup.

---

## 1. Cloud Cost Profile (us-east-1)

- **Amazon S3**: Storage, requests, and applicable transfer are billed by usage; the current artifact volume is small.
- **Amazon DynamoDB**: The table uses `PAY_PER_REQUEST`, so there is no provisioned read/write capacity charge. Requests, storage, and optional features remain usage based and may be covered by account free-tier benefits.
- **Amazon EventBridge**: The live resource is a scheduled EventBridge rule with an API Destination. Its five-minute cadence is low volume, but API Destination and transfer pricing still apply.
- **Amazon ECR**: Private repository storage is usage based. Free-tier allowances are limited by eligibility, time, and stored volume, so zero cost is not guaranteed.
- **Amazon ECS Express Mode**: The live service keeps one `256` CPU-unit, `512` MiB Fargate task running. Confirm the task, managed ingress, and related network charges in AWS Billing rather than relying on a fixed estimate.

---

## 2. Safe Post-Judging Cleanup Instructions

The following commands target named ClauseRunner application resources after judging. Review the live inventory first and run them only when teardown is explicitly approved. IAM roles are intentionally excluded for separate account-owner review.

### A. Delete ECS Express Mode Service and Cluster
```powershell
# Delete only the named ECS Express Mode gateway service
aws ecs delete-express-gateway-service --service-arn arn:aws:ecs:us-east-1:772097700032:service/default/clauserunner-web --profile clauserunner-dev --region us-east-1
```

Do not delete the shared `default` ECS cluster as part of ClauseRunner cleanup.

### B. Remove S3 Evidence Bucket
```powershell
# Delete all remaining objects and the bucket itself
aws s3 rb s3://clauserunner-contracts-772097700032-us-east-1 --force --profile clauserunner-dev --region us-east-1
```

### C. Delete DynamoDB Single-Table State
```powershell
# Delete the state table
aws dynamodb delete-table --table-name clauserunner-state --profile clauserunner-dev --region us-east-1
```

### D. Delete Amazon ECR Repository
```powershell
# Delete the repository and any pushed images
aws ecr delete-repository --repository-name clauserunner-web --force --profile clauserunner-dev --region us-east-1
```

### E. Delete EventBridge Rules, API Destinations, and Connections
```powershell
# Remove the targets from our rule
aws events remove-targets --rule clauserunner-obligation-check --ids "1" --profile clauserunner-dev --region us-east-1

# Delete the rule
aws events delete-rule --name clauserunner-obligation-check --profile clauserunner-dev --region us-east-1

# Delete the api destination
aws events delete-api-destination --name clauserunner-api-destination --profile clauserunner-dev --region us-east-1

# Delete the connection
aws events delete-connection --name clauserunner-connection --profile clauserunner-dev --region us-east-1
```


