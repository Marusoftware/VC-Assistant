
# VC-Assistant bot

VCで、あなたをお手伝いするdiscord用のボットです。
次のような機能があります。
- 正規表現([ここ](https://docs.python.org/ja/3/library/re.html#regular-expression-syntax)を参照)にマッチしたときにメッセージを送信
- VCで音楽を流します。
herokuでデプロイしてお使いください。   
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## 注意
このソフトウェアに関してMarusoftwareは一切の責任を負いません。   
次のように環境変数、並びにビルドパックを設定した上でのおすすめします。   
### 環境変数(Config Vars)
- BOT_TOKEN   
あなたのボットトークン。以下で発行可能。   
https://discord.com/developers/
### ビルドパック
- heroku/python(自動適用されるはず)
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
- https://github.com/xrisk/heroku-opus.git
