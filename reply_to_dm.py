import os
import requests
from datetime import datetime, timedelta

# 環境変数から API トークンとユーザー ID を取得
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # ボットが監視するユーザーのID

if not SLACK_TOKEN or not SLACK_USER_ID:
    raise ValueError("環境変数 (SLACK_TOKEN, SLACK_USER_ID) が設定されていません。")

# Slack API エンドポイント
SLACK_API_URL = "https://slack.com/api"

# 過去5時間のDMメッセージを取得
def fetch_recent_dm_messages():
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
    now = datetime.now()
    oldest = (now - timedelta(hours=5)).timestamp()  # 過去5時間のメッセージを取得

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

# メッセージに返信
def reply_to_dm_summary(dm_channel_id, messages):
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}
    
    if messages:
        # メッセージをまとめる
        summary = "\n".join([f"- {msg.get('text')}" for msg in messages])
        reply_text = f"以下は過去5時間のメッセージです:\n{summary}"
    else:
        # メッセージがない場合
        reply_text = "最近のメッセージはありませんでした。"

    payload = {"channel": dm_channel_id, "text": reply_text}
    response = requests.post(f"{SLACK_API_URL}/chat.postMessage", headers=headers, json=payload)
    data = response.json()

    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    print(f"✅ メッセージに返信しました: {reply_text}")

# 実行
if __name__ == "__main__":
    try:
        messages, dm_channel_id = fetch_recent_dm_messages()
        reply_to_dm_summary(dm_channel_id, messages)
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
