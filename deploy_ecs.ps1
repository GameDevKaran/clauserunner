# ClauseRunner AWS ECS Express Mode Deployment Tool
# Resolves: clauserunner-web service creation in us-east-1

$AWS_ACCOUNT_ID = "772097700032"
$AWS_REGION = "us-east-1"
$AWS_PROFILE = "clauserunner-dev"
$ECR_REGISTRY = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
$IMAGE_NAME = "clauserunner-web"
$SERVICE_NAME = "clauserunner-web"

# Roles expected to be provisioned by the account owner
$EXECUTION_ROLE_ARN = "arn:aws:iam::${AWS_ACCOUNT_ID}:role/clauserunner-ecs-execution-role"
$INFRASTRUCTURE_ROLE_ARN = "arn:aws:iam::${AWS_ACCOUNT_ID}:role/clauserunner-ecs-infrastructure-role"
$TASK_ROLE_ARN = "arn:aws:iam::${AWS_ACCOUNT_ID}:role/clauserunner-ecs-task-role"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   ClauseRunner ECS Express Mode Gateway Deployment Tool    " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Compile the React assets locally
Write-Host "[1/4] Compiling React static production bundle..." -ForegroundColor Yellow
cd frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "React build failed! Aborting."
    exit $LASTEXITCODE
}
cd ..

# 2. Authenticate Docker with Amazon ECR (requires Docker Desktop to be running)
Write-Host "[2/4] Authenticating local Docker daemon with Amazon ECR..." -ForegroundColor Yellow
aws ecr get-login-password --region $AWS_REGION --profile $AWS_PROFILE | docker login --username AWS --password-stdin $ECR_REGISTRY
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Docker login to ECR failed. Please verify that Docker Desktop is running locally."
}

# 3. Build, tag and push the ClauseRunner unified container image
Write-Host "[3/4] Packaging and pushing ECR container image..." -ForegroundColor Yellow
docker build -t $IMAGE_NAME .
docker tag "${IMAGE_NAME}:latest" "${ECR_REGISTRY}/${IMAGE_NAME}:latest"
docker push "${ECR_REGISTRY}/${IMAGE_NAME}:latest"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker push failed! Aborting."
    exit $LASTEXITCODE
}

# 4. Trigger ECS Express Gateway Service creation on AWS
Write-Host "[4/4] Deploying ECS Express Gateway Service..." -ForegroundColor Yellow
aws ecs create-express-gateway-service `
  --service-name $SERVICE_NAME `
  --primary-container "name=${SERVICE_NAME},image=${ECR_REGISTRY}/${IMAGE_NAME}:latest,port=8000,healthCheckPath=/health" `
  --execution-role-arn $EXECUTION_ROLE_ARN `
  --infrastructure-role-arn $INFRASTRUCTURE_ROLE_ARN `
  --task-role-arn $TASK_ROLE_ARN `
  --profile $AWS_PROFILE `
  --region $AWS_REGION `
  --monitor-resources

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSUCCESS: ClauseRunner is successfully deploying to Amazon ECS Express Mode!" -ForegroundColor Green
    Write-Host "Please use 'aws ecs describe-services --cluster express-cluster --services ${SERVICE_NAME}' to retrieve your live HTTPS endpoint." -ForegroundColor Green
} else {
    Write-Error "ECS Gateway Service creation failed!"
}
