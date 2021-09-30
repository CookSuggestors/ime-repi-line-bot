from flask import Flask, request, abort
 
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,
     PostbackEvent,
     TextMessage,
     TemplateSendMessage,
     CarouselTemplate,
     CarouselColumn,
     MessageAction,
     URIAction,
     PostbackAction,
     TextSendMessage,
     TemplateSendMessage,
     ConfirmTemplate
)
import os

app = Flask(__name__)

# 環境変数取得
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ユーザーの一時保存
recipeData = {}
 
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
    user_id = event.source.user_id
    sendMessage("こちらのレシピはいかがですか？", user_id)
    # レシピデータを追加
    recipeData[user_id] = {"index": 0, "recipe": [
        {
            "title": "肉じゃが",
            "image_url": "https://www.kikkoman.co.jp/homecook/search/recipe/img/00006600.jpg",
            "material": ["にんじん", "タマネギ"],
            "url": "https://www.kikkoman.co.jp/homecook/search/recipe/00006600/index.html"
        },
        {
            "title": "ポトフ",
            "image_url": "https://www.kikkoman.co.jp/homecook/search/recipe/img/00006600.jpg",
            "material": ["にんじん", "タマネギ"],
            "url": "https://www.kikkoman.co.jp/homecook/search/recipe/00006600/index.html"
        },
        {
            "title": "肉じゃが2",
            "image_url": "https://www.kikkoman.co.jp/homecook/search/recipe/img/00006600.jpg",
            "material": ["にんじん", "タマネギ"],
            "url": "https://www.kikkoman.co.jp/homecook/search/recipe/00006600/index.html"
        },
        {
            "title": "ポトフ2",
            "image_url": "https://www.kikkoman.co.jp/homecook/search/recipe/img/00006600.jpg",
            "material": ["にんじん", "タマネギ"],
            "url": "https://www.kikkoman.co.jp/homecook/search/recipe/00006600/index.html"
        }
    ]}
    caroucelCol = []
    for recipe in recipeData[user_id]["recipe"][0:2]:
        caroucelCol.append(CarouselColumn(
            thumbnail_image_url = recipe["image_url"],
            title = recipe["title"],
            text = "，".join(recipe["material"]),
            actions=[
                URIAction(
                    label='レシピを確認する',
                    uri = recipe["url"]
                )
            ]
        ))
    line_bot_api.push_message(
        user_id,
        TemplateSendMessage(
            alt_text = 'Carousel template',
            template = CarouselTemplate(
                columns = caroucelCol
            )
        ) 
    )
    line_bot_api.push_message(
        user_id,
        TemplateSendMessage(
            alt_text='Confirm template',
            template=ConfirmTemplate(
                text='作りたいメニューはありましたか？',
                actions=[
                    PostbackAction(
                        label='はい',
                        display_text='はい',
                        data='yes'
                    ),
                    PostbackAction(
                        label='いいえ',
                        display_text='いいえ',
                        data='no'
                    ),
                ]
            )
        )
    )

@handler.add(PostbackEvent)
def handle_event(event):
    user_id = event.source.user_id
    if event.postback.data == "yes":
       del recipeData[user_id]
       sendMessage("調理頑張ってください！", user_id)
    else:
        # レシピが提案できるかどうか
        if(recipeData[user_id]["index"] + 2 < len(recipeData[user_id]["recipe"])):
            sendMessage("こちらのレシピはいかがでしょうか?", user_id)
            recipeData[user_id]["index"] += 2
            index = recipeData[user_id]["index"]
            caroucelCol = []
            for recipe in recipeData[user_id]["recipe"][index:index + 2]:
                caroucelCol.append(CarouselColumn(
                    thumbnail_image_url = recipe["image_url"],
                    title = recipe["title"],
                    text = "，".join(recipe["material"]),
                    actions=[
                        URIAction(
                            label='レシピを確認する',
                            uri = recipe["url"]
                        )
                    ]
                ))
            line_bot_api.push_message(
                user_id,
                TemplateSendMessage(
                    alt_text = 'Carousel template',
                    template = CarouselTemplate(
                        columns = caroucelCol
                    )
                ) 
            )
            line_bot_api.push_message(
                user_id,
                TemplateSendMessage(
                    alt_text='Confirm template',
                    template=ConfirmTemplate(
                        text='作りたいメニューはありましたか？',
                        actions=[
                            PostbackAction(
                                label='はい',
                                display_text='はい',
                                data='yes'
                            ),
                            PostbackAction(
                                label='いいえ',
                                display_text='いいえ',
                                data='no'
                            ),
                        ]
                    )
                )
            )
        else:
            del recipeData[user_id]
            sendMessage("ごめんなさい！これ以上レシピを提案できません(>_<)", user_id)

def sendMessage(message, user_id):
    line_bot_api.push_message(
        user_id,
        TextSendMessage(message)
    )

# ポート番号の設定
if __name__ == "__main__":
#    app.run()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
