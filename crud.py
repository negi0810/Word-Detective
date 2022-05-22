import random
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
#   "now_state": "前半プレイ中",
#   "participants": {
#     "ehi2": {"user_id":"ehi2", "score": 2},
#     "dt8b": {"user_id":"ehi2", "score": 3},
#     "t89t": {"user_id":"t89t", "score": 0}
#   },
#   "mine": ["草", "色"],
#   "trigger": ["大学生になって初めて知ったこと", "休日何してる？"],
# }


# 地雷とトリガーのデータ構造を作る
mine = ["勉強", "サークル", "習い事", "わかる","大学","笑"]
trigger = ["大学生になって初めて知ったこと", "休日何してる？", "生きてるうちにしたいこと", "イチオシの本の魅力","出身地の自慢","意外と自慢なこと"]


def new_game(event, line_bot_api):
    doc_ref = db.collection("word-detective").document(event.source.group_id)
    
    # 送信元グループでルームが存在する:
    if not doc_ref.get().exists:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text=(
                    "ゲームを開始しました\n"
                    "ゲームの参加者は「@ジョイン」と入力してください\n"
                    "参加者の準備ができたら「@スタート」と入力してください"
                )
            )
        )
        # 送信元グループidをキーとしてルームを生成
        doc_ref.set(
            # DBの初期状態
            {
                "group_id": event.source.group_id,
                "now_state": "参加受付中",
                "participants": {},
                "mine": random.sample(mine, 2),
                "trigger": random.sample(trigger, 2),
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
                        event.source.user_id: {
                            "user_id": event.source.user_id,
                            "score": 0
                        }
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
    
    else:
        # 当該ルームが存在しないことを通知
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="現在このグループで実行中のゲームはありません\n「@ニューゲーム」でルームを作成してください"
            )
        )

    return


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
                        text="前半戦スタート！\n\n「"+doc_dict.get("trigger")[0]+(
                            "」について話し合ってください\n"
                            "終わり次第「@フィニッシュ」と入力してください"
                        )
                    )
                )
            elif doc_dict.get("now_state") == "後半開始待機":
                # 後半戦を始める処理
                doc_ref.update({"now_state": "後半プレイ中"})
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text="後半戦スタート！\n\n「"+doc_dict.get("trigger")[1]+(
                            "」について話し合ってください\n"
                            "終わり次第「@フィニッシュ」と入力してください"
                        )
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
                # 集計して表示
                reply_msg = ""
                players_dict = {}
                for player in doc_dict.get("participants"):
                    player_id = player
                    player_score = doc_dict.get("participants").get(player).get("score")
                    players_dict[player_id] = player_score
                    player_name = line_bot_api.get_group_member_profile(event.source.group_id, player_id).display_name
                    reply_msg += player_name+"さん、"+str(player_score)+"点！\n"
                reply_msg += "\n前半戦終了！\n地雷の予想はできましたか？後半戦の準備が出来たら「@スタート」と入力してください"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text=reply_msg
                    )
                )
            elif doc_dict.get("now_state") == "後半プレイ中":
                # 集計の処理
                # 集計して表示
                reply_msg = "【結果発表】\n\n"
                players_dict = {}
                for player in doc_dict.get("participants"):
                    player_id = player
                    player_score = doc_dict.get("participants").get(player).get("score")
                    players_dict[player_id] = player_score
                    player_name = line_bot_api.get_group_member_profile(event.source.group_id, player_id).display_name
                    reply_msg += player_name+"さん、"+str(player_score)+"点！\n"
                reply_msg += "\n地雷ワードは"
                for mine in doc_dict.get("mine"):
                    reply_msg += "「"+mine+"」と"
                reply_msg = reply_msg[:-1]
                reply_msg += "でした！"
                line_bot_api.reply_message(
                    event.reply_token, TextSendMessage(
                        text=reply_msg
                    )
                )
                # ゲームおしまいの処理
                doc_ref.delete()
                # line_bot_api.reply_message(
                #     event.reply_token, TextSendMessage(
                #         text="ゲームおしまい"
                #     )
                # )
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
                "使用できるコマンドは以下の通りです ※「@」は半角\n"
                "@ニューゲーム：ルームを作成します\n"
                "@アボート：ルームを削除します\n"
                "@ジョイン：ルームに入室します\n"
                "@エスケープ：ルームから退出します\n"
                "@スタート：前半戦or後半戦を始めます\n"
                "@フィニッシュ：前半戦or後半戦を終了します\n"
                "@ヘルプ"
            )    
        )
    )

    return


def keyword_count(event, line_bot_api):

    # user_idが取得できないとき
    if not hasattr(event.source, "user_id"):
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="userIDの取得に失敗しました"
            )
        )
        return

    # inのところ動くか不明
    docs = (
        db.collection('word-detective')
        .where('group_id', '==', event.source.group_id)
        .where('now_state', 'in', ["前半プレイ中", "後半プレイ中"])
        .where('participants.'+event.source.user_id+'.user_id', '==', event.source.user_id)
        .get()
    )

    if len(docs) == 1:
        doc = docs[0]
        doc_dict = doc.to_dict()
        doc_ref = doc.reference
        # ルームが存在し、発言者がそれに参加して、プレイ中のときの処理
        keyword_count_sum = 0
        for mine in doc_dict.get("mine"):
            keyword_count_sum += event.message.text.count(mine)
        player_score = doc_dict.get("participants").get(event.source.user_id).get("score") + keyword_count_sum
        doc_ref.update({("participants."+event.source.user_id+".score"): player_score})

    elif len(docs) == 0:
        # ルームが存在するがプレイ中でないまたは参加してない、またはそもそもルームがないときの処理
        pass

    else:
        # !?
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(
                text="このメッセージが見られるのはおかしい"
            )
        )
    
    return

def leave_event(event, line_bot_api):
    # 送信元グループでルームが存在する:
    doc_ref = db.collection('word-detective').document(event.source.groupId)
    if doc_ref.get().exists:
        doc_ref.delete()
    else:
        pass
