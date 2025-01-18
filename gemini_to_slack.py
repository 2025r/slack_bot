import requests
import google.generativeai as genai
import os
from datetime import datetime

# 環境変数から API キーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # DM先のユーザーID

# 必須環境変数の確認
if not GEMINI_API_KEY or not SLACK_TOKEN or not SLACK_USER_ID:
    raise ValueError("環境変数 (GEMINI_API_KEY, SLACK_TOKEN, SLACK_USER_ID) が設定されていません。")

# Slack API エンドポイント
SLACK_API_URL = "https://slack.com/api"
headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}

# DMチャネルのIDを取得
def get_dm_channel_id(user_id):
    response = requests.post(
        f"{SLACK_API_URL}/conversations.open",
        headers=headers,
        json={"users": user_id}
    )
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    return data["channel"]["id"]

# Gemini AI に基づく投稿内容を生成
def generate_ai_message(last_message=None):
    prompt = "人工知能の歴史について、コメントを生成してください。" if not last_message else f"前回の投稿『{last_message}』をもとに人工知能の歴史を拡張した内容を生成してください。"
    response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
    return response.text if response.text else "AIの考察を生成できませんでした。"

# Slack に投稿
def post_to_slack(channel_id, message):
    payload = {"channel": channel_id, "text": message}
    response = requests.post(f"{SLACK_API_URL}/chat.postMessage", headers=headers, json=payload)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    print(f"✅ Slack にメッセージを投稿しました: {message}")

# 実行
if __name__ == "__main__":
    try:
        # DMチャネルIDを取得
        dm_channel_id = get_dm_channel_id(SLACK_USER_ID)

        # Gemini AIで新しい投稿を生成
        ai_message = generate_ai_message()

        # 投稿メッセージを準備
        today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📢 {today_date} のAI投稿: {ai_message}"

        # Slackに投稿
        post_to_slack(dm_channel_id, message)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
