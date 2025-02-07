# gichiroku

## デプロイ
```
#!/bin/bash
# --------------------------------------------------------------
# Flask + Speech-to-Text + Vertex AI（LLM）アプリのデプロイ例スクリプト
# --------------------------------------------------------------
# 事前準備:
#   1) Google Cloud APIs の有効化
#       - Cloud Run
#       - Container Registry (または Artifact Registry)
#       - Vertex AI API
#       - Cloud Speech-to-Text API
#   2) gcloud コマンドにログイン済み (gcloud init / gcloud auth login など)
#   3) 環境変数 $PROJECT_ID, $REGION を自分の環境に合わせて設定する
#
# 使い方:
#   1) chmod +x deploy.sh
#   2) ./deploy.sh
# --------------------------------------------------------------

# エラーが起きたらそこでスクリプト終了
set -e

# ---- 必要に応じて環境変数を指定 (無ければ手動で書き換えてください) ----
PROJECT_ID="${PROJECT_ID:-mvpdemo-0201}"   # 未指定の場合は "my-sample-project"
REGION="${REGION:-us-central1}"                # デフォルト us-central1
SERVICE_NAME="mp3-analyzer"                     # 任意のサービス名
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "========================================================"
echo "[1/4] Dockerビルド: ${IMAGE_NAME}"
echo "========================================================"
docker build  --no-cache  -t "${IMAGE_NAME}" .

echo "========================================================"
echo "[2/4] Dockerイメージを GCR にプッシュ"
echo "========================================================"
docker push "${IMAGE_NAME}"

echo "========================================================"
echo "[3/4] Cloud Run にデプロイ"
echo "========================================================"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_NAME}" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --platform managed \
  --set-env-vars PROJECT_ID="${PROJECT_ID}",REGION="${REGION}"

echo "========================================================"
echo "[4/4] 完了！"
echo "--------------------------------------------------------"
echo "サービスURL:"
gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)'
echo "========================================================"

echo "Curl: "
curl -X POST -F "audio=@voice.mp3" https://mp3-analyzer-mbe4iiqw4q-uc.a.run.app/analyze_mp3
echo "========================================================"
```
