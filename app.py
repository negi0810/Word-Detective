import os
import random
import crud
from flask import Flask, request, abort

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    JoinEvent,
    LeaveEvent,
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
        elif msg == "@フィニッシュ":
            crud.finish(event, line_bot_api=line_bot_api)
        elif msg == "@ヘルプ":
            crud.game_help(event, line_bot_api=line_bot_api)
        elif msg[0] == "＠":
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text="「@」は半角であることに注意してください"
                )
            )
        # その他のメッセージ:
        else:
            crud.keyword_count(event, line_bot_api=line_bot_api)
            # line_bot_api.reply_message(
            #     event.reply_token, TextSendMessage(
            #         text="その他のメッセージが送られました"
            #     )
            # )
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="このBOTはグループチャットでのみ対応しています"
            )
        )
        
    return True

@handler.add(JoinEvent)
def handle_join(event):
    if event.source.type == "group":
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text=[
                    (
                        "このゲームでは、二つの「地雷ワード」が設定されています。\n"
                        "皆さんにはその言葉を推理し、ほかの人がその言葉を発言するように仕向けてもらいます。\n"
                        "最終的にその言葉を言った回数の最も少ない人が勝ちとなります。"
                    ),(
                        "ゲームは前半戦と後半戦に分かれており、それぞれ「お題」が設定されています。皆さんにはその「お題」をもとに会話をしてもらいます。\n"
                        "前半戦終了時において、二つの言葉を話した回数の合計が中間発表として掲示されますのでこれをもとに推理していってください。"
                    ),(
                        "以下の手順に従ってゲームを進めてください。\n"
                        "最初に「@ニューゲーム」と入力しルームを作成してください。\n"
                        "次に参加者はそれぞれ「@ジョイン」と入力してください。\n"
                        "参加者が確定したら「@スタート」と入力してください。これで前半戦が開始されます。\n"
                        "前半戦を終了したいときは「@フィニッシュ」と入力してください。\n"
                        "「@スタート」と入力すると今度は後半戦がスタートします。\n"
                        "後半戦を終了したい場合も同様に「@フィニッシュ」と入力してください。\n"
                        "「@ヘルプ」と入力すると使用できるコマンドの一覧が表示されます。"
                    )
                ]
            )
        )

@handler.add(LeaveEvent)
def handle_leave(event):
    crud.leave_event(event, line_bot_api)

if __name__ == "__main__":
    app.run()

