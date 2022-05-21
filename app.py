import os
import random
import crud
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

app = Flask(__name__)


YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return "OK"


# 地雷とトリガーのデータ構造を作る
mine = ["勉強", "サークル", "習い事", "睡眠"]
trigger = ["大学生になって初めて知ったこと", "休日何してる？", "生きてるうちにしたいこと", "イチオシの本の魅力"]


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    print("call endpoint")
    msg = event.message.text
    # メッセージがグループから送られている:
    if event.source.type == "group":
        # メッセージが"@ニューゲーム":
        if msg == "@ニューゲーム":
            crud.new_game(event, line_bot_api=line_bot_api)
        # メッセージが"@アボート":
        elif msg == "@アボート":
            crud.abort(event, line_bot_api=line_bot_api)
        # メッセージが"@ジョイン"
        elif msg == "@ジョイン":
            crud.join(event, line_bot_api=line_bot_api)
        elif msg == "@エスケープ":
            crud.escape(event, line_bot_api=line_bot_api)
        elif msg == "@スタート":
            crud.start(event, line_bot_api=line_bot_api)
        elif msg == "@エンド":
            crud.end(event, line_bot_api=line_bot_api)
        elif msg == "@ヘルプ":
            crud.help(event, line_bot_api=line_bot_api)
        elif msg.count("＠") >= 1:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text="「@」は半角であることに注意してください"
                )
            )
        # その他のメッセージ:
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text="その他のメッセージが送られました"
                )
            )
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="このBOTはグループチャットでのみ対応しています"
            )
        )
    return True



if __name__ == "__main__":
    app.run()
