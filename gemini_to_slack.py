import requests
import google.generativeai as genai
import os
from datetime import datetime

# 環境変数から API キーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # Slackの投稿先ユーザーID

# 必須環境変数の確認
if not GEMINI_API_KEY or not SLACK_TOKEN or not SLACK_USER_ID:
    raise ValueError("環境変数 (GEMINI_API_KEY, SLACK_TOKEN, SLACK_USER_ID) が設定されていません。")

# Gemini API の設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

# Slack API エンドポイント
SLACK_API_URL = "https://slack.com/api"
headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}

# Slack DM の最新メッセージを取得
def fetch_last_message():
    response = requests.get(
        f"{SLACK_API_URL}/conversations.history",
        headers=headers,
        params={"channel": SLACK_USER_ID, "limit": 1}
    )
    messages_data = response.json()
    if not messages_data.get("ok"):
        raise Exception(f"Slack APIエラー: {messages_data.get('error')}")

    messages = messages_data.get("messages", [])
    return messages[0]["text"] if messages else None

# Gemini AI に基づく投稿内容を生成
def generate_ai_message(last_message=None):
    if last_message:
        prompt = (
            f"前回の投稿『{last_message}』をもとに人工知能の歴史を拡張し、"
            "新しい視点を取り入れたコメントを生成してください。"
        )
    else:
        prompt = "人工知能の歴史について、興味深い事実や視点を含むコメントを生成してください。"

    response = model.generate_content(contents=[prompt])
    return response.text if response.text else "AIの考察を生成できませんでした。"

# Slack に投稿
def post_to_slack(message):
    payload = {"channel": SLACK_USER_ID, "text": message}
    response = requests.post(f"{SLACK_API_URL}/chat.postMessage", headers=headers, json=payload)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    print(f"✅ Slack にメッセージを投稿しました: {message}")

# 実行
if __name__ == "__main__":
    try:
        # 前回の投稿を取得
        last_message = fetch_last_message()
        print(f"前回の投稿内容: {last_message}")

        # 新しい投稿を生成
        ai_message = generate_ai_message(last_message)
        print(f"生成された投稿内容: {ai_message}")

        # Slack に投稿
        today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📢 {today_date} のAI投稿: {ai_message}"
        post_to_slack(message)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
