import os
import requests
import google.generativeai as genai
from datetime import datetime
import random
import time

# 環境変数から API キーを取得
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY2 = os.getenv("GEMINI_API_KEY2")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_USER_ID = os.getenv("SLACK_USER_ID")  # DM先のユーザーID

# 必須環境変数の確認
if not GEMINI_API_KEY or not SLACK_TOKEN or not SLACK_USER_ID:
    raise ValueError("環境変数 (GEMINI_API_KEY, SLACK_TOKEN, SLACK_USER_ID) が設定されていません。")

# Slack API エンドポイント
SLACK_API_URL = "https://slack.com/api"
headers = {"Authorization": f"Bearer {SLACK_TOKEN}"}

# Geminiの初期設定
def configure_gemini(api_key):
    genai.configure(api_key=api_key)
    print(f"Gemini APIキー {api_key} を使用します。")

configure_gemini(GEMINI_API_KEY)

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

# 長文生成とトピック抽出を1回で実行
def generate_long_message_and_topics(prompt):
    try:
        improved_prompt = (
            f"次のテーマについて詳しく説明し、関連するトピックを箇条書きで列挙してください: {prompt}\n"
            "説明は詳細に、トピックは簡潔にしてください。"
        )
        response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[improved_prompt])
        if response.text:
            full_text = response.text.strip()
            split_index = full_text.rfind("\n")  # 最後の改行を探して分割
            long_message = full_text[:split_index].strip()
            topics_text = full_text[split_index + 1:].strip()
            topics = [topic.strip("- ") for topic in topics_text.split("\n") if topic.strip()]
            return long_message, topics
        else:
            raise Exception("Gemini APIからの応答が空でした。")
    except Exception as e:
        print(f"⚠️ Gemini APIエラー (長文生成とトピック抽出): {e}")
        if GEMINI_API_KEY2:
            print("GEMINI_API_KEY2 に切り替えます...")
            configure_gemini(GEMINI_API_KEY2)
            return generate_long_message_and_topics(prompt)
        else:
            raise Exception("Gemini APIエラー: 他のAPIキーが利用できません。")

# トピックを基に140字以内に要約
def summarize_topic_with_improved_prompt(topic):
    prompt = f"次のトピックについて140字以内で要約してください。畏まりすぎない丁寧語でお願いします: {topic}"
    try:
        response = genai.GenerativeModel(model_name="gemini-1.5-pro").generate_content(contents=[prompt])
        return response.text.strip() if response.text else "要約が生成できませんでした。"
    except Exception as e:
        print(f"⚠️ Gemini APIエラー (要約生成): {e}")
        if GEMINI_API_KEY2:
            print("GEMINI_API_KEY2 に切り替えます...")
            configure_gemini(GEMINI_API_KEY2)
            return summarize_topic_with_improved_prompt(topic)
        else:
            raise Exception("Gemini APIエラー: 他のAPIキーが利用できません。")

# Slackに投稿
def post_to_slack(channel_id, message):
    payload = {"channel": channel_id, "text": message}
    response = requests.post(f"{SLACK_API_URL}/chat.postMessage", headers=headers, json=payload)
    data = response.json()
    if not data.get("ok"):
        raise Exception(f"Slack APIエラー: {data.get('error')}")
    print(f"✅ Slack にメッセージを投稿しました: {message}")

# レートリミット対策: リトライ処理
def retry_with_backoff(func, retries=3, delay=5, *args, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ エラー: {e}. {delay}秒後にリトライします... (試行 {attempt + 1}/{retries})")
            time.sleep(delay)
    raise Exception("リトライ上限に達しました。")

# 実行
if __name__ == "__main__":
    try:
        # DMチャネルIDを取得
        dm_channel_id = retry_with_backoff(get_dm_channel_id, user_id=SLACK_USER_ID)

        # 初回または前回の投稿内容 (仮に last_message を None とする)
        last_message = None  # 初回は None、以降はSlack投稿内容などをここに設定

        # 初回または次の内容を生成
        if last_message:
            prompt = f"次の文章を基に人工知能の歴史について拡張した内容を生成してください: {last_message}"
        else:
            prompt = "人工知能の歴史について詳しく説明してください。"

        # 長文とトピックを同時に生成
        long_message, topics = retry_with_backoff(generate_long_message_and_topics, prompt=prompt)
        print(f"生成された長文: {long_message}")
        print(f"抽出されたトピック: {topics}")

        if not topics:
            raise ValueError("トピックが生成されませんでした。")

        # トピックからランダムに1つ選択
        selected_topic = random.choice(topics)
        print(f"選択されたトピック: {selected_topic}")

        # 選択されたトピックを基に140字以内で要約
        short_message = retry_with_backoff(summarize_topic_with_improved_prompt, topic=selected_topic)
        print(f"生成された要約: {short_message}")

        # Slackに投稿
        today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"📢 AIの投稿:\n{short_message}"
        retry_with_backoff(post_to_slack, channel_id=dm_channel_id, message=message)

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
