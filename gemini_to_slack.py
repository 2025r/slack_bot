import os
import requests
import google.generativeai as genai
from datetime import datetime
import random

# 環境変数から API キーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # DM先のユーザーID

# 必須環境変数の確認
if not GEMINI_API_KEY or not SLACK_TOKEN or not SLACK_USER_ID:
    raise ValueError("環境変数 (GEMINI_API_KEY, SLACK_TOKEN, SLACK_USER_ID) が設定されていません。")

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)

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

# 140字以上の文章を生成
def generate_long_message(prompt):
    response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
    return response.text.strip() if response.text else "AIの考察を生成できませんでした。"

# トピックを生成（複数のトピックを抽出）
def generate_topics_from_message(message):
    prompt = f"次の文章からトピックを複数抽出してください: {message}"
    response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
    topics_text = response.text.strip() if response.text else "トピックが生成できませんでした。"
    topics = [topic.strip() for topic in topics_text.split("\n") if topic.strip()]
    return topics

# トピックを基に140字以内に要約
def summarize_message_from_topic(topic):
    prompt = f"次のトピックについて140字以内で要約してください。畏まりすぎない丁寧語でお願いします。: {topic}"
    response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
    return response.text.strip() if response.text else "要約が生成できませんでした。"

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

        # 初回または前回の投稿内容 (仮に last_message を None とする)
        last_message = None  # 初回は None、以降はSlack投稿内容などをここに設定

        # 初回または次の内容を生成
        if last_message:
            prompt = f"次の文章を基に人工知能の歴史について拡張した内容を生成してください: {last_message}"
        else:
            prompt = "人工知能の歴史について詳しく説明してください。"

        # 140字以上の文章を生成
        long_message = generate_long_message(prompt)
        print(f"生成された長文: {long_message}")

        # 長文から複数のトピックを抽出
        topics = generate_topics_from_message(long_message)
        print(f"抽出されたトピック: {topics}")

        if not topics:
            raise ValueError("トピックが生成されませんでした。")

        # トピックからランダムに1つ選択
        selected_topic = random.choice(topics)
        print(f"選択されたトピック: {selected_topic}")

        # 選択されたトピックを基に140字以内で要約
        short_message = summarize_message_from_topic(selected_topic)
        print(f"生成された要約: {short_message}")

        # Slackに投稿
        today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📢 AIの投稿:\n{short_message}"
        post_to_slack(dm_channel_id, message)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
