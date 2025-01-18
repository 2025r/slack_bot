import os
import requests
import google.generativeai as genai
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

# DMチャネル内の最後のメッセージを取得
def get_last_message(channel_id):
    response = requests.get(
        f"{SLACK_API_URL}/conversations.history",
        headers=headers,
        params={"channel": channel_id, "limit": 1}  # 最新メッセージ1件を取得
    )
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    messages = data.get("messages", [])
    return messages[0]["text"] if messages else None

# Gemini AI に基づく話を広げて要約（140文字以内）
def expand_and_summarize(last_message):
    if not last_message:
        prompt = "人工知能の歴史について話を広げ、140文字以内に要約してください。"
    else:
        prompt = f"次の内容を基に話を広げて、140文字以内に要約してください:『{last_message}』"
    genai.configure(api_key=GEMINI_API_KEY)
    response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
    return response.text.strip() if response.text else "AIの考察を生成できませんでした。"

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

        # 最後のメッセージを取得
        last_message = get_last_message(dm_channel_id)

        # Gemini AIで話を広げて140文字以内に要約
        ai_expanded_summary = expand_and_summarize(last_message)

        # 投稿メッセージを準備
        today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📢 AIの投稿:\n{ai_expanded_summary}"

        # Slackに投稿
        post_to_slack(dm_channel_id, message)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
