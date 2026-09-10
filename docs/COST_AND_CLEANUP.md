# ClauseRunner Cost and Cleanup Guide

ClauseRunner is engineered to be serverless and extremely low cost, running on on-demand AWS serverless tiers (S3, DynamoDB, EventBridge) to ensure that the hackathon demo carries near-zero maintenance overhead.

This guide details our cost profile and provides precise instructions for safe post-judging cleanup.

---

## 1. Cloud Cost Profile (us-east-1)

- **Amazon S3**: Under standard storage tiers, our small evidence files and contracts cost less than **$0.01 per month**.
- **Amazon DynamoDB**: Provisioned in on-demand mode (`PAY_PER_REQUEST`). Pricing scales strictly with actual operations, costing **$0.00** during idle periods.
- **Amazon EventBridge Scheduler**: Pricing is serverless, offering **14 million free invocations per month**.
- **Amazon ECR**: Repository storage carries zero-cost within the AWS Free Tier.
- **Amazon ECS Express Mode**: Billed per task-hour for active containers, costing less than **$0.02 per hour** for standard micro task definitions.

---

## 2. Safe Post-Judging Cleanup Instructions

To completely tear down all ClauseRunner-specific resources once judging is complete without affecting any unrelated operational environments, run the following commands sequentially using the authorized `clauserunner-dev` profile in `us-east-1`:

### A. Delete ECS Express Mode Service
```powershell
# Delete the active ECS Express Mode gateway service
aws ecs delete-express-gateway-service --service-name clauserunner-web --profile clauserunner-dev --region us-east-1
```

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

### E. Delete EventBridge Schedule
```powershell
# Delete our scheduled obligation check trigger
aws scheduler delete-schedule --name clauserunner-obligation-check --profile clauserunner-dev --region us-east-1
```

