#!/bin/bash

set -e

# 事前に環境変数を設定
PROJECT_ID="${PROJECT_ID:-gichiroku}"
REGION="${REGION:-asia-northeast1}"
SERVICE_NAME="${SERVICE_NAME:-mp3-analyzer}"
GCR_REPOSITORY="gcr.io/${PROJECT_ID}"
IMAGE_NAME="${GCR_REPOSITORY}/${SERVICE_NAME}"
CLOUD_SQL_CONNECTION_NAME="${PROJECT_ID}:${REGION}:gichidb" # 例: your-project-id:asia-northeast1:your-cloud-sql-instance
CLOUD_SQL_USER="gichi"
CLOUD_SQL_PASSWORD="gichipass"
DATABASE_NAME="mygichi"

echo "Building Docker image: ${IMAGE_NAME}"
docker build --no-cache -t "${IMAGE_NAME}" .

echo "Pushing Docker image to GCR: ${IMAGE_NAME}"
docker push "${IMAGE_NAME}"

echo "Deploying to Cloud Run: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --allow-unauthenticated \
    --platform managed \
    --set-env-vars PROJECT_ID="${PROJECT_ID}",REGION="${REGION}",CLOUD_SQL_CONNECTION_NAME="${CLOUD_SQL_CONNECTION_NAME}",CLOUD_SQL_USER="${CLOUD_SQL_USER}",CLOUD_SQL_PASSWORD="${CLOUD_SQL_PASSWORD}",DATABASE_NAME="${DATABASE_NAME}"

SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)')
echo "Service URL: ${SERVICE_URL}"

echo "Testing with curl:"
# curl -X POST -F "audio=@voice.mp3" "${SERVICE_URL}/analyze_mp3"

echo "Deployment completed!"