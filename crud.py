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
                "now_state": "recruiting",
                # "gamestate": "tier1",
                # "gameinfo": {
                #     "started_at": "2022/05/16 23:56:31"
                #     "keyword": "草",
                #     "question": "大学生になって初めて知ったこと",
                # }
            }
        )
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
    return True


def join(event, line_bot_api):
    # user_idが取得できないとき
    if not hasattr(event.source, "user_id"):
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="userIDの取得に失敗しました"
            )
        )
        return
    doc_ref = db.collection("word-detective").document(event.source.group_id)
    doc = doc_ref.get()
    # 送信元グループでルームが存在する:
    if doc.exists:
        doc_dict = doc.to_dict()
        #profile = line_bot_api.get_profile(event.source.user_id)
        profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
        # ルームの状態が参加受付中
        if doc_dict.get("gamestate") == "参加受付中":
            # プレイヤーがまだ参加していないとき
            if event.source.user_id not in doc_dict.get("participants"):
                reply_msg = ""
                # DBに送信者のIDを登録
                doc_ref.set({
                    "participants": {
                        event.source.user_id: {"user_id": event.source.user_id}
                    }
                }, merge=True)
                reply_msg += (profile.display_name+"さんの参加を受け付けました")
                # 送信者を登録する前の参加人数が(定員-1)のとき(つまり、定員に達したとき)
                if len(doc_dict.get("participants")) == 2:
                    doc_ref.update({"gamestate": "前半待機中"})
                    reply_msg += "\n前半が開始されるのを待ちます……準備ができたら「@スタート」を"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text=reply_msg
                    )
                )
            # プレイヤーがすでに参加してたとき
            else:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text=(profile.display_name+"さんは既に参加しています")
                    )
                )
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text="ゲームの状態が参加受付中ではありません"
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
            if event.source.user_id not in doc_dict:
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
    return True
