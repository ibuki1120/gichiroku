# Python 3.9 slimイメージを利用
FROM python:3.9-slim

# 作業ディレクトリの設定
WORKDIR /app

# 依存パッケージのコピー＆インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ポート8080でアプリを起動（gunicornで本番運用）
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
