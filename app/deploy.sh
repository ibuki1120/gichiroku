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
PROJECT_ID="${PROJECT_ID:-gichiroku}" 
REGION="${REGION:-asia-northeast1}"                # デフォルトはus-central1なので注意
SERVICE_NAME="gichiroku"                     # 任意のサービス名
INSTANCE_CONNECTION_NAME=$(gcloud sql instances describe gichidb --format="value(connectionName)") #your-instance-nameをインスタンス名に変更
CLOUD_SQL_USER="gichi"
CLOUD_SQL_PASSWORD="gichipass"
# DATABASE_NAME=$(gcloud sql databases list --instance=gichidb --format="value(name)" | grep "mygihi") →これ出力がおかしい。多分vlue(name)のとこ
DATABASE_NAME="mygichi"
export PROJECT_ID
export REGION
export INSTANCE_CONNECTION_NAME
export CLOUD_SQL_USER
export CLOUD_SQL_PASSWORD
export DATABASE_NAME
echo "環境変数の確認 本番時は絶対消す！！！"
echo "PROJECT_ID: $PROJECT_ID"
echo "REGION: $REGION"
echo "SERVICE_NAME: $SERVICE_NAME"
echo "INSTANCE_CONNECTION_NAME: $INSTANCE_CONNECTION_NAME"
echo "CLOUD_SQL_USER: $CLOUD_SQL_USER"
echo "CLOUD_SQL_PASSWORD: $CLOUD_SQL_PASSWORD"
echo "DATABASE_NAME: $DATABASE_NAME"


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


# 環境変数yamlにしたい
gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE_NAME}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --allow-unauthenticated \
    --platform managed \
    --set-env-vars PROJECT_ID="$PROJECT_ID",REGION="$REGION",INSTANCE_CONNECTION_NAME="$INSTANCE_CONNECTION_NAME",CLOUD_SQL_USER="$CLOUD_SQL_USER",CLOUD_SQL_PASSWORD="$CLOUD_SQL_PASSWORD",DATABASE_NAME="$DATABASE_NAME"
echo "========================================================"
echo "[4/4] 完了！"
echo "--------------------------------------------------------"
echo "サービスURL:"
gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --format='value(status.url)'
echo "========================================================"

echo "Curl: "
curl -X POST -F "audio=@voice.mp3" "https://gichiroku-228022295019.asia-northeast1.run.app/analyze_mp3"
echo "========================================================"
