import os
import requests
from datetime import datetime, timedelta
import google.generativeai as genai

# 環境変数から API トークンとユーザー ID を取得
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # ボットが監視するユーザーのID
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Gemini APIキー

if not SLACK_TOKEN or not SLACK_USER_ID or not GEMINI_API_KEY:
    raise ValueError("環境変数 (SLACK_TOKEN, SLACK_USER_ID, GEMINI_API_KEY) が設定されていません。")

# Slack API エンドポイント
SLACK_API_URL = "https://slack.com/api"

# Gemini API の設定
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

# 過去5時間内のDMメッセージを取得
def fetch_recent_dm_messages():
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
    now = datetime.now()
    oldest = (now - timedelta(hours=5)).timestamp()

    # DM チャンネルを検索
    response = requests.get(
        f"{SLACK_API_URL}/conversations.list",
        headers=headers,
        params={"types": "im"}  # DM チャンネルのみを取得
    )
    channels_data = response.json()
    if not channels_data.get("ok"):
        raise Exception(f"Slack APIエラー: {channels_data.get('error')}")

    # 特定ユーザーとの DM チャンネル ID を取得
    dm_channel_id = None
    for channel in channels_data.get("channels", []):
        if channel.get("user") == SLACK_USER_ID:
            dm_channel_id = channel.get("id")
            break

    if not dm_channel_id:
        raise Exception("指定されたユーザーとのDMチャンネルが見つかりませんでした。")

    # DM チャンネル内のメッセージを取得
    response = requests.get(
        f"{SLACK_API_URL}/conversations.history",
        headers=headers,
        params={"channel": dm_channel_id, "oldest": oldest}
    )
    messages_data = response.json()
    if not messages_data.get("ok"):
        raise Exception(f"Slack APIエラー: {messages_data.get('error')}")

    return messages_data.get("messages", []), dm_channel_id

# Geminiでメッセージを要約
def summarize_messages(messages):
    if not messages:
        return "直近5時間のメッセージはありませんでした。"

    # メッセージのテキスト部分を結合
    message_texts = [msg.get("text", "") for msg in messages]
    prompt = f"以下のメッセージを要約してください:\n\n" + "\n".join(message_texts)
    
    # Geminiに要約をリクエスト
    response = model.generate_content(contents=[prompt])
    summary = response.text if response.text else "要約に失敗しました。"
    return summary

# Slack に要約を投稿
def post_summary_to_slack(dm_channel_id, summary):
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}
    payload = {"channel": dm_channel_id, "text": f"📝 要約結果:\n\n{summary}"}

    response = requests.post(f"{SLACK_API_URL}/chat.postMessage", headers=headers, json=payload)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    print(f"✅ 要約を投稿しました: {summary}")

# 実行
if __name__ == "__main__":
    try:
        # メッセージ取得
        messages, dm_channel_id = fetch_recent_dm_messages()
        
        # メッセージ要約
        summary = summarize_messages(messages)
        print(f"Gemini 要約結果: {summary}")
        
        # 要約をSlackに投稿
        post_summary_to_slack(dm_channel_id, summary)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
