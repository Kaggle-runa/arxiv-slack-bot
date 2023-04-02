import re
import PyPDF2
import urllib.request
from io import BytesIO
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

system_parameter = """```
あなたは一流のデータサイエンティスト兼AI研究者です。
以下の制約条件と、入力された文章をもとに最高の要約を作成してください。

# 制約条件:
・文章は簡潔かつ学生にも分かりやすく書くこと。
・箇条書きで3行で出力すること。
・重要なキーワードを取り残さないこと。
・要約した文章は違和感のない日本語に翻訳すること。

# 期待する出力フォーマット:
・
・
・

```"""


# arxiv APIから取得したURLからPDF表示できるURLに変換する関数
def convert_abs_url_to_pdf_url(abs_url):
    pdf_url = abs_url.replace('/abs/', '/pdf/') + '.pdf'
    return pdf_url


# 論文中からGithubのURLを探す関数
def extract_git_url(pdf_url):
    git_url = None
    try:
        with urllib.request.urlopen(pdf_url) as response:
            pdf_data = response.read()
            pdf_file = BytesIO(pdf_data)
            reader = PyPDF2.PdfFileReader(pdf_file)
            for page_num in range(reader.numPages):
                page = reader.getPage(page_num)
                text = page.extract_text()
                match = re.search(r'https?://github.com[^\s]+', text)
                if match:
                    git_url = match.group()
                    break
    except Exception as e:
        print(f"Error while extracting Git URL from PDF: {e}")

    return git_url


# 論文を検索して要約する関数
def search_and_summarize_papers(query, num_papers, slack_channel):
    # arXiv APIで論文を検索
    search_results = arxiv.Search(
        query=query, max_results=num_papers, sort_by=arxiv.SortCriterion.Relevance)

    # 検索した論文の情報と要約をSlackに通知
    for result in search_results.results():
        # 論文の情報を取得
        title = result.title
        abstract = result.summary
        url = result.entry_id
        pdf_url = convert_abs_url_to_pdf_url(url)
        git_url = extract_git_url(pdf_url)

        # 論文の要約をOpenAI APIで生成
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_parameter},
                {"role": "user", "content": abstract},
            ]
        )
        summary = response["choices"][0]["message"]["content"]

        # 要約を含むメッセージをSlackに送信
        bar_line = '-' * 100
        message = f"Title: {title}\nURL: {url}\nSummary: \n{summary}\n{bar_line}"

        # git_urlが存在する場合はslackに送るメッセージに付与
        if git_url:
            message += f"\nGit URL: {git_url}"
        message += f"\n{bar_line}"

        try:
            response = slack_client.chat_postMessage(
                channel=slack_channel, text=message)
        except SlackApiError as e:
            print(f"Error sending message: {e}")


# Lambdaハンドラー関数
def lambda_handler(event, context):
    # EventBridgeイベントから検索クエリを取得
    query = event["query"]  # デフォルトの検索クエリを設定
    num_papers = int(event["num_papers"])  # デフォルトの取得論文数を設定
    slack_channel = event["slack_channel"]  # デフォルトのSlackチャンネルを設定

    search_and_summarize_papers(
        query, num_papers=num_papers, slack_channel=slack_channel)

    return {"statusCode": 200, "body": "OK"}
