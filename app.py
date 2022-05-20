import os, random
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

# じゃんけん処理に使用
# DRAW = 0
# USER1_WIN = 1
# USER2_WIN = 2

now_state = "standby"

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

# # 1 -> グー , 2 -> チョキ, 3 -> パー
# def game_janken(user1, user2):
#     # IDで受け取る。
#     if user1 not in [1, 2, 3] or user2 not in [1, 2, 3]:
#         raise Exception("game_janken() failure: invalid params")

#     if user1 == user2:
#         return DRAW
#     elif (
#         (user1 == 1 and user2 == 2)
#         or (user1 == 2 and user2 == 3)
#         or (user1 == 3 and user2 == 1)
#     ):
#         return USER1_WIN
#     else:
#         return USER2_WIN


# def hand_id2str(hand_id):
#     if hand_id == 1:
#         return "ぐー"
#     elif hand_id == 2:
#         return "ちょき"
#     elif hand_id == 3:
#         return "ぱー"

#     raise Exception("handid2str() failure: 不正な入力値です")


# def hand_str2id(hand_str):
#     if hand_str == "ぐー":
#         return 1
#     elif hand_str == "ちょき":
#         return 2
#     elif hand_str == "ぱー":
#         return 3

#     raise Exception("hand_str2id() failure: 不正な入力値です")


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


# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     msg = event.message.text
#     if msg not in ["ぐー", "ちょき", "ぱー"]:
#         line_bot_api.reply_message(
#             event.reply_token, TextSendMessage(text="「ぐー」, 「ちょき」, 「ぱー」のいずれかで答えてね！")
#         )
#         return

#     # 勝敗を決める処理
#     user_hand = hand_str2id(msg)
#     bot_hand = random.randint(1, 3)  # [1, 3]
#     ret_msg = f"{hand_id2str(bot_hand)} !!\n"
#     res = game_janken(bot_hand, user_hand)

#     if res == DRAW:
#         ret_msg += "あーいこーで ..."
#     elif res == USER1_WIN:
#         ret_msg += "僕の勝ち！！"
#     elif res == USER2_WIN:
#         ret_msg += "君の勝ち！！"

#     line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ret_msg))

# 地雷とトリガーのデータ構造を作る
mine = ["勉強", "サークル", "習い事", "睡眠"]
trigger = ["大学生になって初めて知ったこと", "休日何してる？", "生きてるうちにしたいこと", "イチオシの本の魅力"]

@handler.add(MessageEvent, message=TextMessage)
async def handle_message(event):
    print("call endpoint")
    # await crud.operate(event, line_bot_api=line_bot_api)
    msg = event.message.text
    i = random.randint(0, 1)
    global now_state
    if msg == "ゲーム開始":
        now_state = "started"
        line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text="それではゲームを始めます")
        )
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=trigger[2*i])
        )
    # if now_state == "started" and msg == "後半スタート":
    #     now_state = "latter_game_started"
    #     line_bot_api.reply_message(
    #     event.reply_token, TextSendMessage(text=trigger[2*i + 1])
    #     )
    #     # now_state = "completed"
    #     line_bot_api.reply_message(
    #     event.reply_token, TextSendMessage(text="結果発表\n勝者はAさんです")
    #     )
    #     now_state = "standby"
    # else:
    #     line_bot_api.reply_message(
    #         event.reply_token, TextSendMessage(text="まずは「ゲームを開始」と言ってください")
    #     )


    # if msg == "ゲーム開始":
    #     line_bot_api.reply_message(
    #     event.reply_token, TextSendMessage(text="それではゲームを始めます！")
    #     )
    #     i = random.randint(0, 1)
    #     line_bot_api.reply_message(
    #         event.reply_token, TextSendMessage(text=trigger[2*i])
    #     )
    #     if msg == "スタート":
    #         line_bot_api.reply_message(
    #             event.reply_token, TextSendMessage(text=trigger[2*i+1])
    #         )
    #         line_bot_api.reply_message(
    #             event.reply_token, TextSendMessage(text="勝者はAさんです")
    #         )


if __name__ == "__main__":
    app.run()
