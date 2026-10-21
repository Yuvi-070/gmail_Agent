#!/usr/bin/env bash
# ============================================================
# L&D Operations Copilot — One-Click Cloud Run Deployer (Bash)
# ============================================================
# Run this script once your GCP billing account verification completes:
#     chmod +x scripts/deploy_cloud_run.sh
#     ./scripts/deploy_cloud_run.sh
# ============================================================

set -e

echo "============================================================"
echo "🚀 Deploying L&D Operations Copilot to Google Cloud Run"
echo "============================================================"

if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Ensure .env exists in project root."
    exit 1
fi

# Load .env
export $(grep -v '^#' .env | xargs)

PROJECT_ID="${GCP_PROJECT_ID:-project-e5a2b3a6-f74d-4dfa-bed}"
REGION="asia-south1"
SERVICE_NAME="ld-copilot"

echo "📋 Project: $PROJECT_ID"
echo "🌏 Region:  $REGION"
echo "📦 Service: $SERVICE_NAME"
echo ""

echo "🔧 Ensuring deployment APIs are enabled..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "$PROJECT_ID"

echo "🚀 Building and deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --set-env-vars="OAUTH_CLIENT_ID=$OAUTH_CLIENT_ID,OAUTH_CLIENT_SECRET=$OAUTH_CLIENT_SECRET,OAUTH_REFRESH_TOKEN=$OAUTH_REFRESH_TOKEN,GEMINI_API_KEY=$GEMINI_API_KEY,GEMINI_MODEL=gemini-3.5-flash,ACE_SHEET_ID=$ACE_SHEET_ID,API_TRIGGER_TOKEN=$API_TRIGGER_TOKEN,USER_EMAIL=$USER_EMAIL,GCP_PROJECT_ID=$PROJECT_ID" \
  --min-instances 0 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120 \
  --allow-unauthenticated \
  --project "$PROJECT_ID"

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --project "$PROJECT_ID" --format "value(status.url)")

echo ""
echo "============================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "============================================================"
echo "🌐 Cloud Run Service URL: $SERVICE_URL"
echo ""
echo "FINAL STEP:"
echo "Add this secret to your GitHub Repository (Settings -> Secrets -> Actions):"
echo "   Secret Name:  CLOUD_RUN_URL"
echo "   Secret Value: $SERVICE_URL"
echo ""
echo "Your GitHub Actions workflow will instantly switch to invoking Cloud Run!"
