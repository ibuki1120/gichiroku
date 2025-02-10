# 議知録

## 前提
- チームメンバ全員同じ開発環境にしたいから、Cloud Shell エディターで開発するよ
- gitで連携

## 使用するツール
### VertexAI
- これで会話を解析させる。

### CLOUD SQL
- MySQL

## シーケンス図^^
```mermaid
sequenceDiagram
    participant ユーザ as ユーザ
    participant CR as Cloud Run
    participant CS as Cloud Storage
    participant VA as Vertex AI

    ユーザ->>CR: POST /analyze_mp3 (音声ファイル, ユーザ名)
    CR->>CR: リクエストの検証 (ファイル存在チェック、拡張子チェック、ユーザ名確認)
    CR->>CS: 音声ファイルをアップロード (blob.upload_from_file)
    CS-->>CR: アップロード完了 → gcs_uri を返却
    CR->>VA: summarize_text(gcs_uri, ユーザ) の呼び出し<br>（プロンプトファイル読み込み、モデル呼び出し）
    VA-->>CR: 要約テキストを返却
    CR->>ユーザ: JSON形式で要約テキストとユーザ名を返却
```

## GCPプロジェクトの作成手順
### プロジェクトの作成
- 作成後はGUI画面で作成されたことを確認しよう
- 画面右上からCLOUD SHELLを開く
```bash
# PJ一覧の作成：事前確認
gcloud projects list

# gijiroku PJの作成
gcloud projects create <PROJECT_NAME> --set-as-default

# PJ一覧の作成：事後確認
gcloud projects list

# 設定作業中のPJの確認
gcloud config get-value project
# <PROJECT_NAME> が出力されればOK!

```

### 請求の有効化
1. Google Cloud Consoleの「請求」 に移動。
2. 「請求アカウントの管理」 で、作成した請求アカウントを開く。
3. 「プロジェクトをリンク」 をクリックし、<PROJECT_NAME>を選択。
4. CLIでもいける
```bash
# アカウントID確認
gcloud beta billing accounts list

# 有効化確認
### NAME: 請求先アカウント
### OPEN: True
# ならOK
gcloud beta billing projects describe <PROJECT_NAME>

# 有効化
gcloud beta billing projects link <PROJECT_NAME> --billing-account=アカウントID
```


### 必要なAPIの有効化
```bash
# 有効化されているサービス一覧取得
gcloud services list --enabled
```

### Cloud Storageのセットアップ
- 作成したバケットをGCPコンソールで確認
```bash
# 一覧確認
gcloud storage buckets list

# 作成
gcloud storage buckets create gs://{bucket-name} --location={location}
```


###  MySQL データベースインスタンスとユーザーの作成
```bash
# 事前確認
gcloud sql instances list
# インスタンスの作成
# 15分くらいかかるよ
gcloud sql instances create <DB_NAME> --database-version=MYSQL_8_0 --tier=db-f1-micro --region=asia-northeast1

# DB作成
gcloud sql databases create mygichi --instance=<DB_NAME>
# ユーザ作成
gcloud sql users create <USER_NAME> --instance=<DB_NAME> --password=<DB_PASS>

# 事後確認
## インスタンスの確認
gcloud sql instances list
## DBの確認
gcloud sql databases list --instance=<DB_NAME> --format="value(name)"

## 環境変数は開発時はdebugしてる
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


## デバッグ
- 過去10件のログを出力するよ^^
- ChatGPTとGeminiにぶち込む
```
gcloud logging read "severity>=ERROR" --limit 10
```
