from flask import Flask, request, jsonify, render_template  # Flaskフレームワークの主要な機能
from google.cloud import speech_v1p1beta1 as speech  # Google Cloud Speech-to-Text API
from google.cloud import storage  # Google Cloud Storage API
import os  # 環境変数を取得するためのモジュール
import io  # メモリオブジェクトを扱うためのモジュール
import mysql.connector  # MySQLデータベース接続用モジュール
import logging  # ログ出力用モジュール
import json
import vertexai
from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    Part
)

from utiles import read_prompt_as_list, read_interaction_as_list

# Flaskアプリケーションの作成
app = Flask(__name__)

# ロギング設定 (Cloud Loggingに統合)
# Cloud Runにデプロイすると、この設定でCloud Loggingにログが送信される
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)  # ロガーの取得

# 環境変数の設定
# Cloud Runにデプロイ時に設定する
PROJECT_ID = os.environ.get("PROJECT_ID")  # Google CloudプロジェクトID
REGION = os.environ.get("REGION")  # Cloud Runリージョン
BUCKET_NAME = f"{PROJECT_ID}-storage"  # Cloud Storageバケット名
INSTANCE_CONNECTION_NAME = os.environ.get("INSTANCE_CONNECTION_NAME")  # Cloud SQL接続名
CLOUD_SQL_USER = os.environ.get("CLOUD_SQL_USER")  # Cloud SQLユーザー名
CLOUD_SQL_PASSWORD = os.environ.get("CLOUD_SQL_PASSWORD")  # Cloud SQLパスワード
DATABASE_NAME = os.environ.get("DATABASE_NAME", "mygichi")  # Cloud SQLデータベース名 (デフォルト: mygichi)

# Cloud Storageクライアントの初期化
storage_client = storage.Client()  # Cloud Storageクライアントを作成
bucket = storage_client.bucket(BUCKET_NAME)  # バケットを取得

# Speech-to-Textクライアントの初期化
speech_client = speech.SpeechClient()  # Speech-to-Textクライアントを作成

# Cloud SQL接続
cnx = None  # データベース接続オブジェクトを初期化
try:
    # 環境変数からデータベース接続情報を取得
    mysql_config = {
        "user": CLOUD_SQL_USER,
        "password": CLOUD_SQL_PASSWORD,
        "host": INSTANCE_CONNECTION_NAME.split(":")[0],  # 接続名を分割してホスト名を取得
        "database": DATABASE_NAME
    }
    cnx = mysql.connector.connect(**mysql_config)  # データベースに接続
    logger.info("Cloud SQL接続成功")  # 接続成功ログを出力
except Exception as e:
    logger.error(f"Cloud SQL接続エラー: {e}")  # 接続失敗ログを出力

# テキストを要約する関数 
def summarize_text(gcs_uri, user):
    """
    テキストを要約する
    """
    vertexai.init(project=PROJECT_ID, location="us-central1")
    system_instruction_list = read_interaction_as_list("./assets/interaction.txt", user)
    pronpt_txt = read_prompt_as_list("./assets/pronpt.txt", user)
    vertexai_model = GenerativeModel(
        "gemini-2.0-flash-exp",
        system_instruction=system_instruction_list
    )
    generation_config = GenerationConfig(
        temperature=1,
        max_output_tokens=8192
    )
    response = vertexai_model.generate_content([
        Part.from_uri(
            gcs_uri, mime_type="audio/mp3"
        ),
        pronpt_txt
    ], 
    generation_config=generation_config
    )
    logger.info(f"Response Text: {response.text}")
    return response.text

# MP3ファイルを解析するエンドポイント
@app.route('/analyze_mp3', methods=['POST'])
def analyze_mp3():
    try:
        user = request.form.get("user")
        if 'audio' not in request.files:  # リクエストに音声ファイルが含まれていない場合
            return jsonify({'error': 'No audio file provided'}), 400  # 400エラーを返す
        
        if not user:  # リクエストに音声ファイルが含まれていない場合
            return jsonify({'error': 'No user name'}), 400  # 400エラーを返す

        audio_file = request.files['audio']  # 音声ファイルを取得

        # 拡張子チェック
        if not audio_file.filename.lower().endswith(('.mp3',)):  # ファイル名が.mp3で終わっていない場合
            return jsonify({'error': 'Invalid file extension. Only MP3 files are allowed.'}), 400  # 400エラーを返す

        audio_content = audio_file.read()  # 音声ファイルの内容を読み込む

        # Cloud Storageにアップロード
        blob = bucket.blob(audio_file.filename)  # バケット内のblobを指定
        blob.upload_from_file(io.BytesIO(audio_content), content_type=audio_file.content_type)  # 音声ファイルをアップロード
        gcs_uri = f"gs://{BUCKET_NAME}/{audio_file.filename}"  # Cloud Storage URI
        logger.info(f"音声ファイルをCloud Storageにアップロード: {gcs_uri}")  # アップロード成功ログを出力

        # テキストを要約
        summary = summarize_text(gcs_uri, user)  # 要約を実行
        logger.info("テキストを要約")  # 要約成功ログを出力

        return app.response_class(
            response=json.dumps({'summary': summary, "user": user}, ensure_ascii=False),
            status=200,
            mimetype='application/json'
        )
    except Exception as e:  # エラーが発生した場合
        logger.error(f"エラー発生: {e}")  # エラーログを出力
        return jsonify({'error': 'An error occurred during processing.'}), 500  # 500エラーを返す

@app.route('/')
def index():
    return render_template('index.html')

# アプリケーションの起動
if __name__ == '__main__':
    # Cloud Runでは、ポート番号を環境変数PORTから取得する必要がある
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))