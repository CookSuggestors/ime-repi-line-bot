from flask import Flask, request, abort
import requests
import random

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
    TextSendMessage,
    StickerSendMessage,
    CarouselTemplate,
    CarouselColumn,
    MessageAction,
    URIAction,
    PostbackAction,
    ConfirmTemplate
)
import os

app = Flask(__name__)

# 環境変数取得
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
DISPLAYCOUNT = 3
RAKUTEN_API_ENDPOINT = os.environ["RAKUTEN_API_ENDPOINT"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
support_patern = [
    {
        "package_id": "11538",
        "sticker_id": "51626517"
    },
    {
        "package_id": "446",
        "sticker_id": "1997"
    },
    {
        "package_id": "1070",
        "sticker_id": "17840"
    },
    {
        "package_id": "11537",
        "sticker_id": "52002735"
    }
]

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

# メッセージが送信された時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message = event.message.text
    split_mate = message.split("食材: ")
    if(len(split_mate) <= 1):
        return
    user_id = event.source.user_id
    # すでに送信してたら，何も返さない
    if(user_id in recipeData):
        return
    recipeData[user_id] = {"index": 0}
    try:
        sendMessage("しばらくお待ちください...", user_id)
        recipeData[user_id]["recipe"] = getRecipe(split_mate)
        # ユーザーデータを作成
        sendMessage("こちらのレシピはいかがですか？", user_id)
        sendCarousel(getDisplayCarousel(recipeData, user_id), user_id)
        sendConfirm(user_id)
    except:
        del recipeData[user_id]
        sendMessage("サーバーが混雑しているので，少し時間をおいてからお試しください！", user_id)

# ユーザが操作した後の処理
@handler.add(PostbackEvent)
def handle_event(event):
    user_id = event.source.user_id
    if(not user_id in recipeData):
        sendMessage("食材を送信してください！", user_id)
        return
    if event.postback.data == "yes":
        del recipeData[user_id]
        sendMessage("調理頑張ってください！", user_id)
        sendStamp(user_id, support_patern)
    else:
        is_possible_to_recommend = recipeData[user_id]["index"] + 1 <= len(recipeData[user_id]["recipe"])
        if(is_possible_to_recommend):
            sendMessage("こちらのレシピはいかがでしょうか?", user_id)
            sendCarousel(getDisplayCarousel(recipeData, user_id), user_id)
            sendConfirm(user_id)
        else:
            del recipeData[user_id]
            sendMessage("ごめんなさい！これ以上レシピを提案できません(>_<)", user_id)

# メッセージの送信
def sendMessage(message, user_id):
    line_bot_api.push_message(
        user_id,
        TextSendMessage(message)
    )

# 確認メッセージの送信
def sendConfirm(user_id):
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

# カルーセルの送信
def sendCarousel(col, user_id):
    line_bot_api.push_message(
        user_id,
        TemplateSendMessage(
            alt_text = 'Carousel template',
            template = CarouselTemplate(
                columns = col
            )
        ) 
    )

def sendStamp(user_id, patern):
    stamp = patern[int(random.random() * 10 % len(patern))]
    line_bot_api.push_message(
        user_id,
        StickerSendMessage(
            package_id = stamp["package_id"],
            sticker_id = stamp["sticker_id"]
        )
    )

# 表示するカルーセルの取得
def getDisplayCarousel(recipeData, user_id):
    index = recipeData[user_id]["index"]
    recipeData[user_id]["index"] += DISPLAYCOUNT
    return list(map(lambda recipe: getRow(recipe), recipeData[user_id]["recipe"][index:index + DISPLAYCOUNT]))

def getRow(recipe):
    text = ""
    for material in recipe["notMatchRecipeMaterial"]:
        # 60字越えるかどうかをチェック
        if(len(text + material) + 1 >= 60):
            break
        text += material + ","
    return CarouselColumn(
        thumbnail_image_url = recipe["foodImageUrl"],
        title = recipe["recipeTitle"],
        text = text[:-1], # 最後のカンマを除去
        actions=[
            URIAction(
                label='レシピを確認する',
                uri = recipe["recipeUrl"]
            )
        ]
    )
# レシピの受け取り
def getRecipe(input):
    url = RAKUTEN_API_ENDPOINT + "?input=" + input
    res = requests.get(url)
    return res.json()

# ポート番号の設定
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
