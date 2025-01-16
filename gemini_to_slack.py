import requests
import google.generativeai as genai
import os
from datetime import datetime

# 環境変数から API キーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")  # Slackの投稿先チャンネルID

# 必須環境変数の確認
if not GEMINI_API_KEY or not SLACK_TOKEN or not SLACK_CHANNEL_ID:
    raise ValueError("環境変数 (GEMINI_API_KEY, SLACK_TOKEN, SLACK_CHANNEL_ID) が設定されていません。")

# Gemini API の設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name='gemini-1.5-pro')

# Gemini AI にメッセージ生成をリクエスト
prompt = "最近の話題について短いコメントを生成してください。"
response = model.generate_content(contents=[prompt])
ai_message = response.text if response.text else "AIの考察を生成できませんでした。"

# 投稿するメッセージ
today_date = datetime.now().strftime("%Y-%m-%d")
message = f"📢 {today_date} のAI投稿: {ai_message}"

# Slack に投稿
headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "channel": USER_ID,  # DM に送る
    "text": message
}

slack_response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
data = slack_response.json()

if data.get("ok"):
    print(f"✅ Slack にメッセージを投稿しました！")
else:
    print(f"❌ Slack への投稿に失敗しました: {data.get('error')}")
