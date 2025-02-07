# 議知録

## 前提
- Google Cloud Shellで開発するよ
- 

## GCPプロジェクトの作成
## 手順
### プロジェクトの作成
- PJ名は meeting-mvp-project 
- 作成後はGUI画面で確認
```bash
# PJ一覧の事前確認
gcloud projects list

# まずアプデが求められた
gcloud components update
gcloud projects create meeting-mvp-project --set-as-default

# PJ一覧の事後確認
gcloud projects list

# 設定作業中のPJの確認
gcloud config get-value project

```

### 請求の有効化
1. Google Cloud Consoleの「請求」 に移動。
2. 「請求アカウントの管理」 で、作成した請求アカウントを開く。
3. 「プロジェクトをリンク」 をクリックし、meeting-mvp-project を選択。
4. CLIでもいける
```bash
# アカウントID確認
gcloud beta billing accounts list

# 有効化確認
gcloud beta billing projects describe meeting-mvp-project

# 有効化
gcloud beta billing projects link meeting-mvp-project --billing-account=アカウントID
```


### 必要なAPIの有効化
```bash
# 有効化されているサービス一覧取得
gcloud services list --enabled

# 有効化するAPI
gcloud services enable storage.googleapis.com 
gcloud services enable speech.googleapis.com 
gcloud services enable sqladmin.googleapis.com 
gcloud services enable aiplatform.googleapis.com 
gcloud services enable run.googleapis.com
```

### Cloud Storageのセットアップ
- 作成したバケットをGCPコンソールで確認
- バケット名は「meeting-mvp-audio-bucket」
```bash
# 一覧確認
gcloud storage buckets list

# 作成
gcloud storage buckets create gs://meeting-mvp-audio-bucket --location=asia-northeast1
```


### Postgreデータベースとユーザーの作成
```bash
# 事前確認
gcloud sql instances list

# まずDBインスタンス作成。とりあえずPostgreでいきます。
gcloud sql instances create mvp-chat-db --database-version=POSTGRES_14 --tier=db-f1-micro --region=asia-northeast1

# DB作成。※20分くらい必要
gcloud sql databases create chat --instance=mvp-chat-db

# 事後確認
gcloud sql databases list --instance=mvp-chat-db

# postgres ユーザーのパスワードを設定
gcloud sql users set-password postgres --instance=mvp-chat-db --password=P@ssw0rd123

# Cloud SQL に接続
## パスワード入力が求められる
gcloud sql connect mvp-chat-db --user=postgres
```


###  MySQL データベースとユーザーの作成
- ID: myuser
- PW: mypass0201
```bash
# 事前確認
gcloud sql instances list
# インスタンスの作成 15分くらいかかる
gcloud sql instances create my-sql-instance --database-version=MYSQL_8_0 --tier=db-f1-micro --region=asia-northeast1

# DB作成
gcloud sql databases create mydatabase --instance=my-sql-instance
# ユーザ作成
gcloud sql users create myuser --instance=my-sql-instance --password=mypass0201

# 事後確認
gcloud sql instances list
```





### Cloud Run（バックエンドのデプロイ）
- Cloud Run は コンテナ化されたアプリケーションをGCP上でサーバーレスで実行できるサービス です。
- Flask などの Python アプリを Docker コンテナとしてデプロイ し、GCP 上で動かすことができます。

#### メリット
- サーバーレス → インフラの管理不要（スケール自動化）
- Docker でデプロイ可能 → どんな言語でも動かせる
- HTTPS対応 → 自動的に公開URLが発行される


```bash
# ファイル構成
cloud-run-backend/
│── app.py            # Flaskアプリ
│── requirements.txt  # 必要なPythonパッケージ
│── Dockerfile        # Cloud Run用のDockerファイル
│── .dockerignore     # Dockerの不要ファイルを除外
│── templates/        # 🔹 `index.html` はここに配置
│   ├── index.html    # フロントエンドページ
│── static/           # 🔹 CSS, JS などを格納
│   ├── styles.css    # スタイルシート（任意）
│   ├── script.js     # JavaScriptファイル（任意）
```

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
