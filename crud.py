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
#  now_state": "tier1",
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
                "now_state": "参加受付中",
                "participants": {}
                # now_state": "tier1",
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
    return


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
    return


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
        profile = line_bot_api.get_group_member_profile(
            event.source.group_id, event.source.user_id)
        # ルームの状態が参加受付中
        if doc_dict.get("now_state") == "参加受付中":
            # プレイヤーがまだ参加していないとき
            if event.source.user_id not in doc_dict.get("participants"):
                # DBに送信者のIDを登録
                doc_ref.set({
                    "participants": {
                        event.source.user_id: {"user_id": event.source.user_id}
                    }
                }, merge=True)
                # 送信者を登録する前の参加人数が(定員-1)のとき(つまり、定員に達したとき)
                # if len(doc_dict.get("participants")) == 2:
                #     doc_ref.update({"now_state": "前半待機中"})
                #     reply_msg += "\n前半が開始されるのを待ちます……準備ができたら「@スタート」を入力してください"
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
    return


# def escape(event, line_bot_api):
#     doc_ref = db.collection("word-detective").document(event.source.group_id)
#     doc_dict = doc_ref.get().to_dict()
#     profile = line_bot_api.get_profile(event.source.user_id)
#     now_state = doc_dict.get("now_state")
#     print(doc_ref.get().to_dict())
#     print(doc_ref.get().to_dict().get(event.source.user_id))
#     print(doc_ref.get().to_dict().get(event.source.user_id["user_id"]))

#     if doc_ref.get().exists:
#         if now_state == "recruiting":
#             if event.source.user_id not in doc_dict:
#                 doc_ref.update(
#                     {
#                         event.source.user_id: firestore.DELETE_FIELD
#                     }
#                 )
#                 line_bot_api.reply_message(
#                     event.reply_token, TextSendMessage(
#                         text=(profile.display_name+"さんがルームを退出しました")
#                     )
#                 )
#             else:
#                 line_bot_api.reply_message(
#                     event.reply_token, TextSendMessage(
#                         text="あなたはまだこのルームに参加していません"
#                     )
#                 )
#         else:
#             line_bot_api.reply_message(
#                 event.reply_token, TextSendMessage(
#                     text="現在はルームを退出することができません\nゲームを終了したい場合は「@アボート」を入力してください"
#                 )
#             )
#     else:
#         line_bot_api.reply_message(
#             event.reply_token, TextSendMessage(
#                 text="ルーム自体が存在していません"
#             )
#         )
#     return

def escape(event, line_bot_api):
    # user_idが取得できないとき
    if not hasattr(event.source, "user_id"):
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="userIDの取得に失敗しました"
            )
        )
        return
    doc_ref = db.collection('word-detective').document(event.source.group_id)
    doc = doc_ref.get()
    # 送信元グループでルームが存在する:
    if doc.exists:
        doc_dict = doc.to_dict()
        profile = line_bot_api.get_group_member_profile(
            event.source.group_id, event.source.user_id)
        # プレイヤーがすでに参加してたとき
        if event.source.user_id in doc_dict.get("participants"):
            # ルームの状態が参加受付中
            if doc_dict.get("now_state") == "参加受付中":
                # DBから送信者のIDを削除
                doc_ref.update({
                    ("participants."+event.source.user_id): firestore.DELETE_FIELD
                })
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text=(profile.display_name+"さんの参加を取り消しました")
                    )
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="ゲームの状態が参加受付中ではありません\nゲームを終了したい場合は「@アボート」を入力してください"
                    )
                )
        # プレイヤーがまだ参加していないとき
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text=(profile.display_name+"さんはゲームに参加していません")
                )
            )
    else:
        # 当該ルームが存在しないことを通知
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="現在このグループで実行中のゲームはありません"
            )
        )
    return


def start(event, line_bot_api):
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
        profile = line_bot_api.get_group_member_profile(
            event.source.group_id, event.source.user_id)
        # 発言者がゲームに参加しているとき
        if event.source.user_id in doc_dict.get("participants"):
            # ルームの状態が参加受付中か確認
            if doc_dict.get("now_state") == "参加受付中":
                # 前半戦を始める処理
                doc_ref.update({"now_state": "前半プレイ中"})
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="前半戦スタート！"
                    )
                )
            elif doc_dict.get("now_state") == "後半開始待機":
                # 後半戦を始める処理
                doc_ref.update({"now_state": "後半プレイ中"})
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="後半戦スタート！"
                    )
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="ゲーム開始待機中ではありません"
                    )
                )
        # 発言者がゲームに参加していないとき
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text=(profile.display_name +
                          "さんはゲームに参加していないため、ゲームを進行する権利がありません")
                )
            )
    else:
        # 当該ルームが存在しないことを通知
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="現在このグループで実行中のゲームはありません\n「@ニューゲーム」でルームを作成してください"
            )
        )
    return


def finish(event, line_bot_api):
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
        profile = line_bot_api.get_group_member_profile(
            event.source.group_id, event.source.user_id)
        # 発言者がゲームに参加しているとき
        if event.source.user_id in doc_dict.get("participants"):
            # ルームの状態が参加受付中か確認
            if doc_dict.get("now_state") == "前半プレイ中":
                # 前半戦を始める処理
                doc_ref.update({"now_state": "後半開始待機"})
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="前半戦終了！後半戦の準備が出来たら「@スタート」と入力"
                    )
                )
            elif doc_dict.get("now_state") == "後半プレイ中":
                # 集計の処理
                # ゲームおしまいの処理
                doc_ref.delete()
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="ゲームおしまい"
                    )
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="ゲームプレイ中ではありません"
                    )
                )
        # 発言者がゲームに参加していないとき
        else:
            line_bot_api.reply_message(
                event.reply_token, TextSendMessage(
                    text=(profile.display_name +
                          "さんはゲームに参加していないため、ゲームを進行する権利がありません")
                )
            )
    else:
        # 当該ルームが存在しないことを通知
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="現在このグループで実行中のゲームはありません\n「@ニューゲーム」でルームを作成してください"
            )
        )
    return


def game_help(event, line_bot_api):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(
            text=(
                "@ニューゲーム：ルームを作成します\n"
                "@アボート：ルームを削除します\n"
                "@ジョイン：ルームに入室します\n"
                "@エスケープ：ルームから退出します\n"
                "@スタート：ゲームを始めます\n"
                "@フィニッシュ：ゲームを中断（？）します\n"
                "@ヘルプ"
            )    
        )
    )
