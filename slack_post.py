import requests
import os
from datetime import datetime

# Slack API トークン & ユーザー ID（環境変数から取得）
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
USER_ID = os.getenv("SLACK_USER_ID")  # GitHub Secrets から取得

# ヘッダー設定
headers = {
    "Authorization": f"Bearer {SLACK_TOKEN}",
    "Content-Type": "application/json"
}

# Slack に投稿する関数
def post_message_to_slack():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 現在の時刻
    message = f"📢 {now} のお知らせ: これは GitHub Actions によるテスト投稿です！"

    payload = {
        "channel": USER_ID,  # DM に送る
        "text": message
    }

    response = requests.post("https://slack.com/api/chat.postMessage", headers=headers, json=payload)
    data = response.json()

    if data.get("ok"):
        print(f"✅ {now} に Slack DM へメッセージを投稿しました！")
    else:
        print(f"❌ Slack への投稿に失敗しました: {data.get('error')}")
        print("📌 詳細なレスポンス:", data)

# 実行
if __name__ == "__main__":
    post_message_to_slack()
