from flask import Flask, request, abort
 
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, MessageAction, URIAction, PostbackAction, TextSendMessage, TemplateSendMessage, ConfirmTemplate
)
import os
 
app = Flask(__name__)
 
#環境変数取得
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
 
@app.route('/')
def index():
    return "ok"
 
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
 
    # リクエストボディを取得
    body = request.get_data(as_text=True)
    app.logger.info("Request body: "  + body)
 
    try:
        handler.handle(body, signature)
    # 署名検証で失敗した場合、例外を出す
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return 'OK'
 
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.push_message(
        event.source.user_id,
        TextSendMessage("こちらのレシピはいかがですか?")
    )
    line_bot_api.push_message(
        event.source.user_id,
        TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=[
                    CarouselColumn(
                        thumbnail_image_url='https://www.kikkoman.co.jp/homecook/search/recipe/img/00006600.jpg',
                        title='肉じゃが',
                        text='追加食材: なし',
                        actions=[
                            URIAction(
                                label='レシピを確認する',
                                uri='http://example.com/1'
                            )
                        ]
                    ),
                    CarouselColumn(
                        thumbnail_image_url='https://www.kikkoman.co.jp/homecook/search/recipe/img/00006600.jpg',
                        title='ポトフ',
                        text='追加食材: にんじん, 玉ねぎ',
                        actions=[
                            URIAction(
                                label='レシピを確認する',
                                uri='http://example.com/2'
                            )
                        ]
                    )
                ]
            )
        ) 
    )
    line_bot_api.push_message(
        event.source.user_id,
        TemplateSendMessage(
            alt_text='Confirm template',
            template=ConfirmTemplate(
                text='作りたいメニューはありましたか？',
                actions=[
                    PostbackAction(
                        label='はい',
                        display_text='postback text',
                        data='action=buy&itemid=1'
                    ),
                    PostbackAction(
                        label='いいえ',
                        display_text='postback text',
                        data='action=buy&itemid=1'
                    ),
                ]
            )
        )
    )

# ポート番号の設定
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

