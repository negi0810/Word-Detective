from firebase import db
from firebase_admin import firestore
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)

# {
#   "group_id": "xxxx000",
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


def new_game(event, line_bot_api):
    doc_ref = db.collection("word-detective").document(event.source.group_id)
    # 送信元グループでルームが存在する:
    if not doc_ref.get().exists:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="ゲームを開始しました"
            )
        )
        # 送信元グループidをキーとしてルームを生成
        doc_ref.set(
            # DBの初期状態
            {
                "group_id": event.source.group_id,
                "now_state": "standby",
                # "gamestate": "tier1",
                # "gameinfo": {
                #     "started_at": "2022/05/16 23:56:31"
                #     "keyword": "草",
                #     "question": "大学生になって初めて知ったこと",
                # }
            }
        )
        doc_ref.update({"now_state": "recruiting"})
    else:
        # 一旦ゲームを終了するよう促す
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text=(
                    "このグループで既に実行中のゲームがあります。\n"
                    "ゲームを新規に開始するにはこのゲームを終了する必要があります。\n"
                    "「@アボート」と発言することでゲームを強制終了することができます。"
                )
            )
        )
    return True


def abort(event, line_bot_api):
    doc_ref = db.collection("word-detective").document(event.source.group_id)
    # 送信元グループでルームが存在する:
    if doc_ref.get().exists:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="ルームを消去しました"
            )
        )
        # そのルームを破棄
        doc_ref.delete()

    # 送信元グループでルームが存在しない:
    else:
        # 当該ルームが存在しないことを通知
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="現在このグループで実行中のゲームはありません"
            )
        )
        # または、何もしない
    return True


def join(event, line_bot_api):
    doc_ref = db.collection("word-detective").document(event.source.group_id)
    # 送信元グループでルームが存在する:
    if doc_ref.get().exists:
        doc_dict = doc_ref.get().to_dict()
        profile = line_bot_api.get_profile(event.source.user_id)
        # プレイヤーがまだ参加していないとき
        if event.source.user_id != doc_dict.get(event.source.user_id["user_id"]):
            # DBに送信者のIDを登録
            doc_ref.set({
                event.source.user_id: {"user_id": event.source.user_id}
            }, merge=True)
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text=(profile.display_name+"さんの参加を受け付けました")
                )
            )
        # プレイヤーがすでに参加してたとき
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text=(profile.display_name+"さんは既に参加しています")
                )
            )
        # TODO: PC版のLINEではユーザーIDを取得できないということを通知
    else:
        # 当該ルームが存在しないことを通知
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="現在このグループで実行中のゲームはありません\n「@ニューゲーム」でルームを作成してください"
            )
        )
    return True


def escape(event, line_bot_api):
    doc_ref = db.collection("word-detective").document(event.source.group_id)
    doc_dict = doc_ref.get().to_dict()
    profile = line_bot_api.get_profile(event.source.user_id)
    now_state = doc_dict.get("now_state")
    print(doc_ref.get().to_dict())
    print(doc_ref.get().to_dict().get(event.source.user_id))
    print(doc_ref.get().to_dict().get(event.source.user_id["user_id"]))

    if doc_ref.get().exists:
        if now_state == "recruiting":
            if event.source.user_id == doc_dict.get(event.source.user_id["user_id"]):
                doc_ref.update(
                    {
                        event.source.user_id: firestore.DELETE_FIELD
                    }
                )
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text=(profile.display_name+"さんがルームを退出しました")
                    )
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="あなたはまだこのルームに参加していません"
                    )
                )
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text="現在はルームを退出することができません\nゲームを終了したい場合は「@アボート」を入力してください"
                )
            )
    else:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="ルーム自体が存在していません"
            )
        )
