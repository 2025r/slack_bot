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

# 過去5分間のDMメッセージを取得
def fetch_recent_dm_messages():
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}
    now = datetime.now()
    oldest = (now - timedelta(minutes=5)).timestamp()

    # ボットとの DM チャンネルを検索
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
def reply_to_dm_message(dm_channel_id, ts, text):
    headers = {"Authorization": f"Bearer {SLACK_TOKEN}", "Content-Type": "application/json"}
    reply_text = f"返信: {text} に対するボットからの返信です！"
    payload = {"channel": dm_channel_id, "text": reply_text, "thread_ts": ts}

    response = requests.post(f"{SLACK_API_URL}/chat.postMessage", headers=headers, json=payload)
    data = response.json()

    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    print(f"✅ メッセージに返信しました: {reply_text}")

# 実行
if __name__ == "__main__":
    # DM チャンネル検索時のレスポンス
    print(f"DM チャンネル検索レスポンス: {response.json()}")
    
    # メッセージ取得時のレスポンス
    print(f"メッセージ履歴レスポンス: {messages_data}")
    
    # 各メッセージの内容を確認
    print(f"取得したメッセージ: {messages}")

    messages, dm_channel_id = fetch_recent_dm_messages()
    for message in messages:
        if "bot_id" not in message:  # ボット以外の投稿を処理
            ts = message.get("ts")
            text = message.get("text")
            reply_to_dm_message(dm_channel_id, ts, text)
