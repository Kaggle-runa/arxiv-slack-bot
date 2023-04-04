import re
import random
import PyPDF2
from PyPDF2 import PdfReader
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
あなたは一流のデータサイエンス分野の研究者です。
以下の制約条件と、入力された文章をもとに最高の要約を作成してください。

# 制約条件:
・文章は簡潔かつ学生にも分かりやすく書くこと。
・箇条書きで3行で出力すること。
・重要なキーワードを取り残さないこと。
・要約した文章は違和感のない日本語に翻訳すること。

# 期待する出力フォーマット:
①
②
③

# 出力例
①深層学習の過去、現在、未来について説明されている。
②深層学習と皮質学習の収束により、人工的な皮質カラムが最終的に構築されると予測されている。
③本研究からは、深部皮質学習が注目されることが確認された。
```"""


# 取得する論文のカテゴリ
paper_dict = {
    "cs.AI": "人工知能",
    "cs.AR": "ハードウェア・アーキテクチャ",
    "cs.CE": "計算工学、金融、科学",
    "cs.CV": "コンピュータビジョンとパターン認識",
    "cs.DS": "データ構造とアルゴリズム",
    "cs.GR": "グラフィックス",
    "cs.GT": "コンピュータサイエンスとゲーム理論",
    "eess.AS": "音声・音声処理",
    "eess.IV": "画像・映像処理",
    "eess.SP": "信号処理",
    "math.OC": "最適化・制御",
    "math.PR": "確率",
    "stat.ML": "機械学習",
    "math.ST": "統計理論",
    "stat.TH": "統計学理論",
    "eess.AS": "音声・音声処理",
    "eess.IV": "画像・映像処理",
    "eess.SP": "信号処理"
}


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
            reader = PdfReader(pdf_file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
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

    # 検索に使う変数とslackに送信するカテゴリの内容をqueryから取得
    category = "cat:" + query[0]
    content = "今日紹介する論文のカテゴリーは「" + query[1] + "」だよ！"

    # slackにcontentを通知
    slack_client.chat_postMessage(channel=slack_channel, text=content)

    # arXiv APIで論文を検索
    search_results = arxiv.Search(
        query=category, max_results=num_papers, sort_by=arxiv.SortCriterion.Relevance)

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
        message = f"Title: {title}\nURL: {url}\nSummary: \n{summary}"

        # git_urlが存在する場合はslackに送るメッセージに付与
        if git_url:
            message += f"{bar_line}\nGit URL: {git_url}"
        message += f"\n{bar_line}"

        try:
            response = slack_client.chat_postMessage(
                channel=slack_channel, text=message)
        except SlackApiError as e:
            print(f"Error sending message: {e}")


# Lambdaハンドラー関数
def lambda_handler(event, context):

    # paper_dictから紹介する論文をランダムに選択
    query = random.choice(list(paper_dict.items()))

    # EventBridgeイベントから検索クエリを取得
    num_papers = int(event["num_papers"])  # デフォルトの取得論文数を設定
    slack_channel = event["slack_channel"]  # デフォルトのSlackチャンネルを設定

    search_and_summarize_papers(query, num_papers, slack_channel)

    return {"statusCode": 200, "body": "OK"}
