# ClauseRunner AWS ECS Express Mode Rolling Deployment Helper
# -------------------------------------------------------------------------
# NOTE: Local Docker builds are deprecated. Container compilation is fully
# automated and built securely inside AWS/GitHub Actions via OIDC.
# 
# This script compiles React static assets locally for safety verification,
# and triggers a secure rolling-deployment forward on your existing ECS service.
# -------------------------------------------------------------------------

$AWS_ACCOUNT_ID = "772097700032"
$AWS_REGION = "us-east-1"
$AWS_PROFILE = "clauserunner-dev"
$SERVICE_NAME = "clauserunner-web"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   ClauseRunner ECS Express Mode Rolling Deployment Helper   " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Compile the React assets locally for verification
Write-Host "[1/2] Verifying and compiling React static production bundle..." -ForegroundColor Yellow
cd frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Error "React build compilation failed! Aborting."
    exit $LASTEXITCODE
}
cd ..

# 2. Inform user about the remote build path
Write-Host "`n[Note] Local Docker is not required. All ECR container builds" -ForegroundColor Gray
Write-Host "       are compiled securely on git push via GitHub Actions OIDC." -ForegroundColor Gray

# 3. Trigger safe rolling-deployment on existing service
Write-Host "`n[2/2] Triggering in-place rolling update on ECS Service..." -ForegroundColor Yellow
aws ecs update-service `
  --cluster default `
  --service $SERVICE_NAME `
  --force-new-deployment `
  --profile $AWS_PROFILE `
  --region $AWS_REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[Success] rolling deployment initiated!" -ForegroundColor Green
    Write-Host "Waiting for service to reach steady state..." -ForegroundColor Yellow
    aws ecs wait services-stable `
      --cluster default `
      --services $SERVICE_NAME `
      --profile $AWS_PROFILE `
      --region $AWS_REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: ClauseRunner is successfully updated and stable on Amazon ECS!" -ForegroundColor Green
        Write-Host "Endpoint: https://cl-a7d669f525024e6a8413b2e0f7b851c8.ecs.us-east-1.on.aws/" -ForegroundColor Green
    } else {
        Write-Error "Service failed to stabilize."
    }
} else {
    Write-Error "ECS Service rolling update failed!"
}

