
# VC-Assistant bot

VCで、あなたをお手伝いするdiscord用のボットです。
次のような機能があります。
- 正規表現([ここ](https://docs.python.org/ja/3/library/re.html#regular-expression-syntax)を参照)にマッチしたときにメッセージを送信
- VC(ボイスチャット)で音楽を再生する    
- VCでチャットを読み上げる(現在無効化されています)
# 使用方法
まず、discord bot tokenを取得してください。([ここ](https://discord.com/developers/)から取得可能です。)    
なお、このボットでは、intentを採用しています。Presence Intent(Developer Potal内)を有効にする必要があります。   
また、スラッシュコマンドを有効にするにはapplications.commandsスコープを有効にする必要があります。
そのあと、以下のいずれかの方法でご利用ください。
## 自力
このボットは、python3.8以上が必要です。
まず、依存関係(動作させるのに必要なライブラリ等)をインストールします。   
`python3 -m pip install -r requirements.txt`   
次に、ffmpegをインストールします。   
Windowsの場合は、ffmpeg公式より、ダウンロードしたものを、PATH環境変数に指定されているフォルダの配下におく必要があります。   
Linux,Macの場合は、パッケージマネージャを利用してインストールすることができることがあります。    
すべて完了したら、実行してください。   
`py main.py [トークン(必須), envに設定すると、代わりにBOT_TOKENを読みます。]`   
## Heroku
herokuでデプロイしてお使いください。   
以下のボタンを使用して、初期設定が終わったら、Dyno(run_bot)を有効化してください。   
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)      
自動的に設定されますが、念のため以下に示します。   
### 環境変数(Config Vars)
- BOT_TOKEN   
ボットトークン。以下で発行可能。   
https://discord.com/developers/
- DATABASE_URL
heroku postgre databaseの接続URL    
設定されているときは、データベースが使用されます。
### ビルドパック
- heroku/python(自動適用されるはず)
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
- https://github.com/xrisk/heroku-opus.git   
### アドオン
postgresql   
## 注意
このソフトウェアに関してMarusoftwareは一切の責任を負いません。   
Herokuに関しては、ボタンを使用して環境変数、並びにビルドパックを設定した上での利用をおすすめします。
