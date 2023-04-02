# arxiv-slack-bot
arxiv APIを利用して毎日定期的に新規の論文をslackに投げてくれるサービス


## 環境変数
- Github sercretsに以下を登録してください
  - AWS_ACCESS_KEY_ID：AWSのアクセスキー(lambda・eventbridge・s3・cloudformationのアクセス権限を付与されたもの)
  - AWS_SECRET_ACCESS_KEY：AWSのシークレットアクセスキー(lambda・eventbridge・s3・cloudformationのアクセス権限を付与されたもの)
  - OPENAI_TOKEN：openaiのアクセスキー
  - SLACK_TOKEN：Slackにアクセスするためのトークン(下記画像の部分で取得)
  
  <img width="838" alt="無題" src="https://user-images.githubusercontent.com/58076642/229334919-5a628c38-4ac9-4fe1-9ba9-b4a8a5e3cf7b.png">



## lambda layerの作り方  
必要なライブらりが増えるたびに以下のコマンドを入力する  

'''
pip install -t src/layer/python openai slack-sdk arxiv
'''
