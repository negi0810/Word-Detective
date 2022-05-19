from firebase import db
from app import line_bot_api
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

# {
#   "groupID": "xxxx000", 
#   "participants": {
#     "user001": {"tier1_point": 2},
#     "user002": {"tier1_point": 3}, 
#     "user003": {"tier1_point": 0}
#   },
#   "gamestate": "tier1",
#   "gameinfo": {
#     "started_at": "2022/05/16 23:56:31"
#     "keyword": "草",
#     "question": "大学生になって初めて知ったこと",
#   }
# }

def operate(event):
    # メッセージがグループから送られている:
    if event.source.type == "group":
        # メッセージが"@ニューゲーム":
        if event.message.text == "@ニューゲーム":
            # 送信元グループでルームが存在する:
            if db.collection('word-detective').document(event.source.groupId).get().exists:
                # 一旦ゲームを終了するよう促す
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        (
                            "このグループで既に実行中のゲームがあります。\n"
                            "ゲームを新規に開始するにはこのゲームを終了する必要があります。\n"
                            "「@アボート」と発言することでゲームを強制終了することができます。"
                        )
                    )
                )
            else:
                # 送信元グループidをキーとしてルームを生成
                db.collection('word-detective').document(event.source.groupId).set(
                    # DBの初期状態
                    {
                        "groupID": "xxxx000", 
                        # "participants": {
                        # "user001": {"tier1_point": 2},
                        # "user002": {"tier1_point": 3}, 
                        # "user003": {"tier1_point": 0}
                        # },
                        # "gamestate": "tier1",
                        # "gameinfo": {
                        #     "started_at": "2022/05/16 23:56:31"
                        #     "keyword": "草",
                        #     "question": "大学生になって初めて知ったこと",
                        # }
                    }
                )
        # メッセージが"@アボート":
        elif event.message.text == "@アボート":
            # 送信元グループでルームが存在する:
            doc_ref = db.collection('word-detective').document(event.source.groupId)
            if doc_ref.get().exists:
                # そのルームを破棄
                doc_ref.delete()
            # 送信元グループでルームが存在しない:
            else:
                # 当該ルームが存在しないことを通知
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        "現在このグループで実行中のゲームはありません"
                    )
                )
                # または、何もしない
        # その他のメッセージ:
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    "その他のメッセージが送られました"
                )
            )
        #     送信元グループでルームが存在する and ルームに送信ユーザーが登録されている:
        #         ルームの状態に応じた返答をする
        #         メッセージによってルームの状態を変更する
        #     送信元グループでルームが存在しない:
        #         何もしない