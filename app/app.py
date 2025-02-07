from flask import Flask, request, jsonify
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import storage
import os
import io
import mysql.connector
import logging

app = Flask(__name__)

# ロギング設定 (Cloud Loggingに統合)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 環境変数の設定
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION")
BUCKET_NAME = f"{PROJECT_ID}-storage"
CLOUD_SQL_CONNECTION_NAME = os.environ.get("CLOUD_SQL_CONNECTION_NAME")
CLOUD_SQL_USER = os.environ.get("CLOUD_SQL_USER")
CLOUD_SQL_PASSWORD = os.environ.get("CLOUD_SQL_PASSWORD")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "mygichi") # デフォルトデータベース名を設定

# Cloud Storageクライアントの初期化
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# Speech-to-Textクライアントの初期化
speech_client = speech.SpeechClient()

# Cloud SQL接続
cnx = None
try:
    mysql_config = {
        "user": CLOUD_SQL_USER,
        "password": CLOUD_SQL_PASSWORD,
        "host": CLOUD_SQL_CONNECTION_NAME.split(":")[0],
        "database": DATABASE_NAME
    }
    cnx = mysql.connector.connect(**mysql_config)
    logger.info("Cloud SQL接続成功")
except Exception as e:
    logger.error(f"Cloud SQL接続エラー: {e}")

def transcribe_audio(gcs_uri):
    """音声ファイルを文字起こしする"""
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=44100,
        language_code="ja-JP",
        enable_automatic_punctuation=True
    )
    response = speech_client.recognize(config=config, audio=audio)
    transcript = ""
    for result in response.results:
        for alternative in result.alternatives:
            transcript += alternative.transcript
    return transcript

def summarize_text(text):
    """テキストを要約する (TODO: Vertex AI (LLM) 連携)"""
    return f"TODO: {text}"  # 仮の要約

def store_summary(transcript, summary):
    """要約結果をCloud SQLに保存する"""
    if cnx:
        try:
            with cnx.cursor() as cursor: # with構文で自動的にクローズ
                add_summary = ("INSERT INTO summaries (transcript, summary) VALUES (%s, %s)")
                data = (transcript, summary)
                cursor.execute(add_summary, data)
                cnx.commit()
            logger.info("要約結果をCloud SQLに保存")
        except Exception as e:
            logger.error(f"Cloud SQL保存エラー: {e}")
            cnx.rollback()

@app.route('/analyze_mp3', methods=['POST'])
def analyze_mp3():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    audio_content = audio_file.read()

    # Cloud Storageにアップロード
    blob = bucket.blob(audio_file.filename)
    blob.upload_from_file(io.BytesIO(audio_content), content_type=audio_file.content_type)
    gcs_uri = f"gs://{BUCKET_NAME}/{audio_file.filename}"
    logger.info(f"音声ファイルをCloud Storageにアップロード: {gcs_uri}")

    # 音声ファイルを文字起こし
    transcript = transcribe_audio(gcs_uri)
    logger.info("音声ファイルを文字起こし")

    # テキストを要約
    summary = summarize_text(transcript)
    logger.info("テキストを要約")

    # 要約結果をCloud SQLに保存
    store_summary(transcript, summary)

    return jsonify({'transcript': transcript, 'summary': summary})

@app.route('/healthz') # ヘルスチェック用エンドポイント
def healthz():
    if cnx:
       return "OK", 200
    return "Error", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))