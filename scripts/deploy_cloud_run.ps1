# ============================================================
# L&D Operations Copilot — One-Click Cloud Run Deployer (PowerShell)
# ============================================================
# Run this script once your GCP billing account verification completes:
#     .\scripts\deploy_cloud_run.ps1
#
# It automatically reads your .env file and deploys the container to Cloud Run!
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 Deploying L&D Operations Copilot to Google Cloud Run" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Error "❌ .env file not found. Ensure .env exists in project root."
    exit 1
}

# 2. Parse .env
$envVars = @{}
Get-Content ".env" | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
        $parts = $line.Split("=", 2)
        $envVars[$parts[0].Trim()] = $parts[1].Trim()
    }
}

$PROJECT_ID = if ($envVars["GCP_PROJECT_ID"]) { $envVars["GCP_PROJECT_ID"] } else { "project-e5a2b3a6-f74d-4dfa-bed" }
$REGION = "asia-south1"
$SERVICE_NAME = "ld-copilot"

Write-Host "📋 Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "🌏 Region:  $REGION" -ForegroundColor Yellow
Write-Host "📦 Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host ""

# 3. Enable necessary deployment APIs
Write-Host "🔧 Ensuring Cloud Run, Cloud Build & Artifact Registry APIs are enabled..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

# 4. Construct env-vars string
$envVarList = @(
    "OAUTH_CLIENT_ID=$($envVars['OAUTH_CLIENT_ID'])",
    "OAUTH_CLIENT_SECRET=$($envVars['OAUTH_CLIENT_SECRET'])",
    "OAUTH_REFRESH_TOKEN=$($envVars['OAUTH_REFRESH_TOKEN'])",
    "GEMINI_API_KEY=$($envVars['GEMINI_API_KEY'])",
    "GEMINI_MODEL=gemini-3.5-flash",
    "ACE_SHEET_ID=$($envVars['ACE_SHEET_ID'])",
    "API_TRIGGER_TOKEN=$($envVars['API_TRIGGER_TOKEN'])",
    "USER_EMAIL=$($envVars['USER_EMAIL'])",
    "GCP_PROJECT_ID=$PROJECT_ID"
)
$envVarsParam = ($envVarList -join ",")

Write-Host "🚀 Building container from source and deploying to Cloud Run..." -ForegroundColor Cyan

gcloud run deploy $SERVICE_NAME `
  --source . `
  --region $REGION `
  --set-env-vars=$envVarsParam `
  --min-instances 0 `
  --max-instances 1 `
  --memory 512Mi `
  --cpu 1 `
  --timeout 120 `
  --allow-unauthenticated `
  --project $PROJECT_ID

# 5. Extract Service URL
$SERVICE_URL = (gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID --format "value(status.url)").Trim()

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "✅ DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "🌐 Cloud Run Service URL:" -ForegroundColor Yellow
Write-Host "   $SERVICE_URL" -ForegroundColor Yellow
Write-Host ""
Write-Host "FINAL STEP:" -ForegroundColor Cyan
Write-Host "Add this secret to your GitHub Repository (Settings -> Secrets -> Actions):" -ForegroundColor Cyan
Write-Host "   Secret Name:  CLOUD_RUN_URL" -ForegroundColor White
Write-Host "   Secret Value: $SERVICE_URL" -ForegroundColor White
Write-Host ""
Write-Host "Your GitHub Actions workflow will instantly switch to invoking Cloud Run!" -ForegroundColor Green
