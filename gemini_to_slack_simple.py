import os
import requests
import google.generativeai as genai
from datetime import datetime
import time

# 環境変数から API キーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # DM先のユーザーID

# 必須環境変数の確認
if not GEMINI_API_KEY or not SLACK_TOKEN or not SLACK_USER_ID:
    raise ValueError("環境変数 (GEMINI_API_KEY, SLACK_TOKEN, SLACK_USER_ID) が設定されていません。")

# Geminiの初期設定
def configure_gemini(api_key):
    genai.configure(api_key=api_key)
    print(f"Gemini APIキー {api_key} を使用します。")

configure_gemini(GEMINI_API_KEY)

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

# 前回のSlack投稿を取得
def get_last_slack_message(channel_id):
    response = requests.get(
        f"{SLACK_API_URL}/conversations.history",
        headers=headers,
        params={"channel": channel_id, "limit": 1}
    )
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    messages = data.get("messages", [])
    if messages:
        return messages[0].get("text")
    return None

# Geminiで新しい文章を生成
def generate_response_from_last_message(last_message):
    prompt = f"以下の文章を基に話を広げた新しい内容を生成してください:\n{last_message}"
    try:
        response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
        return response.text.strip() if response.text else "新しい内容を生成できませんでした。"
    except Exception as e:
        raise Exception(f"Gemini APIエラー: {e}")

# Slackに投稿
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

        # 前回のSlack投稿を取得
        last_message = get_last_slack_message(dm_channel_id)
        if not last_message:
            print("前回の投稿が見つかりませんでした。最初の投稿を生成します。")
            last_message = "人工知能の歴史について詳しく説明してください。"

        # 新しい文章を生成
        new_message = generate_response_from_last_message(last_message)
        print(f"生成されたメッセージ: {new_message}")

        # Slackに投稿
        today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📢 AIの投稿 {new_message}"
        post_to_slack(dm_channel_id, message)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
