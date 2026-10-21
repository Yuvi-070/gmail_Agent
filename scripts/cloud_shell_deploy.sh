#!/usr/bin/env bash
# ============================================================
# L&D Operations Copilot — Google Cloud Shell Deployment Script
# ============================================================
# Run directly in Google Cloud Shell (https://shell.cloud.google.com):
#
#   git clone https://github.com/Yuvi-070/gmail_Agent.git
#   cd gmail_Agent
#   bash scripts/cloud_shell_deploy.sh
# ============================================================

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}============================================================${NC}"
echo -e "${CYAN}🚀 L&D Operations Copilot — Cloud Shell Deployer${NC}"
echo -e "${CYAN}============================================================${NC}"
echo ""

PROJECT_ID="project-e5a2b3a6-f74d-4dfa-bed"
REGION="asia-south1"
SERVICE_NAME="ld-copilot"

echo -e "Setting active GCP Project to: ${YELLOW}${PROJECT_ID}${NC}"
gcloud config set project "${PROJECT_ID}"

# ────────────────────────────────────────────────────────────
# 1. Gather Configuration (From .env or Interactive Prompts)
# ────────────────────────────────────────────────────────────
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Found existing .env file. Loading configuration...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}⚠️ No .env file found. Please provide credentials (press Enter to accept defaults):${NC}"
    echo ""

    read -p "OAUTH_CLIENT_ID: " OAUTH_CLIENT_ID
    read -p "OAUTH_CLIENT_SECRET: " OAUTH_CLIENT_SECRET
    read -p "OAUTH_REFRESH_TOKEN: " OAUTH_REFRESH_TOKEN
    read -p "GEMINI_API_KEY: " GEMINI_API_KEY
    read -p "ACE_SHEET_ID [19D9vndSighrRDXCnp7alLguZ61uvTxHjo0B9u9goLI8]: " ACE_SHEET_ID
    ACE_SHEET_ID="${ACE_SHEET_ID:-19D9vndSighrRDXCnp7alLguZ61uvTxHjo0B9u9goLI8}"
    
    read -p "API_TRIGGER_TOKEN: " API_TRIGGER_TOKEN
    read -p "USER_EMAIL [yuvrajtale070@gmail.com]: " USER_EMAIL
    USER_EMAIL="${USER_EMAIL:-yuvrajtale070@gmail.com}"

    # Save to .env for future runs
    cat <<EOF > .env
OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID}
OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET}
OAUTH_REFRESH_TOKEN=${OAUTH_REFRESH_TOKEN}
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=gemini-3.5-flash
ACE_SHEET_ID=${ACE_SHEET_ID}
API_TRIGGER_TOKEN=${API_TRIGGER_TOKEN}
USER_EMAIL=${USER_EMAIL}
GCP_PROJECT_ID=${PROJECT_ID}
EOF
    echo -e "${GREEN}✅ Created .env file.${NC}"
fi

# Sanitize ACE_SHEET_ID if full URL was passed
if [[ "$ACE_SHEET_ID" == *"/d/"* ]]; then
    ACE_SHEET_ID=$(echo "$ACE_SHEET_ID" | sed -n 's/.*\/d\/\([^\/]*\).*/\1/p')
fi

# ────────────────────────────────────────────────────────────
# 2. Enable Required GCP APIs
# ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}🔧 Step 1/3: Enabling required Google Cloud APIs...${NC}"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  gmail.googleapis.com \
  calendar-json.googleapis.com \
  drive.googleapis.com \
  sheets.googleapis.com \
  --project "${PROJECT_ID}"

echo -e "${GREEN}✅ APIs enabled.${NC}"

# ────────────────────────────────────────────────────────────
# 3. Build & Deploy Container to Cloud Run
# ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}🚀 Step 2/3: Building container and deploying to Cloud Run...${NC}"
echo -e "Region: ${YELLOW}${REGION}${NC} | Service: ${YELLOW}${SERVICE_NAME}${NC}"

gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --region "${REGION}" \
  --set-env-vars="OAUTH_CLIENT_ID=${OAUTH_CLIENT_ID},OAUTH_CLIENT_SECRET=${OAUTH_CLIENT_SECRET},OAUTH_REFRESH_TOKEN=${OAUTH_REFRESH_TOKEN},GEMINI_API_KEY=${GEMINI_API_KEY},GEMINI_MODEL=gemini-3.5-flash,ACE_SHEET_ID=${ACE_SHEET_ID},API_TRIGGER_TOKEN=${API_TRIGGER_TOKEN},USER_EMAIL=${USER_EMAIL},GCP_PROJECT_ID=${PROJECT_ID}" \
  --min-instances 0 \
  --max-instances 1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120 \
  --allow-unauthenticated \
  --project "${PROJECT_ID}"

# Retrieve Service URL
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --format "value(status.url)")

# ────────────────────────────────────────────────────────────
# 4. Verify Health Check
# ────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}🔍 Step 3/3: Verifying Cloud Run deployment...${NC}"
HEALTH_STATUS=$(curl -s "${SERVICE_URL}/health" | grep -o '"status":"healthy"' || echo "failed")

if [ "$HEALTH_STATUS" = '"status":"healthy"' ]; then
    echo -e "${GREEN}✅ Health check passed! Endpoint is live and healthy.${NC}"
else
    echo -e "${YELLOW}⚠️ Notice: Could not verify /health immediately. Check logs if needed.${NC}"
fi

# ────────────────────────────────────────────────────────────
# 5. Output Summary
# ────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}🎉 CLOUD RUN DEPLOYMENT SUCCESSFUL!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "🌐 Service URL: ${YELLOW}${SERVICE_URL}${NC}"
echo ""
echo -e "${CYAN}FINAL STEP TO ACTIVATE GITHUB ACTIONS WITH CLOUD RUN:${NC}"
echo -e "1. Go to your GitHub repository:"
echo -e "   ${YELLOW}https://github.com/Yuvi-070/gmail_Agent/settings/secrets/actions${NC}"
echo ""
echo -e "2. Add this secret:"
echo -e "   Secret Name:  ${GREEN}CLOUD_RUN_URL${NC}"
echo -e "   Secret Value: ${YELLOW}${SERVICE_URL}${NC}"
echo ""
echo -e "3. Test the deployment right now by running:"
echo -e "   ${CYAN}curl -X POST ${SERVICE_URL}/generate-brief -H \"Authorization: Bearer ${API_TRIGGER_TOKEN}\"${NC}"
echo ""
echo -e "============================================================"
