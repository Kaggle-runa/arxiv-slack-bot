import json
import openai
import arxiv
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# APIキーの設定
OPENAI_API_KEY = os.environ["OPENAI_TOKEN"]
SLACK_API_TOKEN = os.environ["SLACK_TOKEN"]

# APIクライアントの初期化
openai.api_key = OPENAI_API_KEY
slack_client = WebClient(token=SLACK_API_TOKEN)


# 論文を検索して要約する関数
def search_and_summarize_papers(query, num_papers=3, slack_channel="#general"):
    # arXiv APIで論文を検索
    search_results = arxiv.Search(
        query=query, max_results=num_papers, sort_by=arxiv.SortCriterion.Relevance)

    # 検索した論文の情報と要約をSlackに通知
    for result in search_results.results():
        # 論文の情報を取得
        title = result.title
        abstract = result.summary
        url = result.entry_id

        # 論文の要約をOpenAI APIで生成
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Please summarize the following abstract in Japanese:\n{abstract}"}
            ]
        )
        summary = response["choices"][0]["message"]["content"]

        # 要約を含むメッセージをSlackに送信
        message = f"Title: {title}\nURL: {url}\nSummary: {summary}"
        try:
            response = slack_client.chat_postMessage(
                channel=slack_channel, text=message)
        except SlackApiError as e:
            print(f"Error sending message: {e}")


# Lambdaハンドラー関数
def lambda_handler(event, context):
    # EventBridgeイベントから検索クエリを取得
    query = event["query"]  # デフォルトの検索クエリを設定
    num_papers = event["num_papers"]  # デフォルトの取得論文数を設定
    slack_channel = event["slack_channel"]  # デフォルトのSlackチャンネルを設定

    search_and_summarize_papers(
        query, num_papers=num_papers, slack_channel=slack_channel)

    return {"statusCode": 200, "body": "OK"}
