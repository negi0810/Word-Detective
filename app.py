import os
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import uvicorn

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = FastAPI()

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)


@app.post("/callback")
def callback():
    # get X-Line-Signature header value
    signature = Request.headers['X-Line-Signature']

    # get request body as text
    body = Request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return JSONResponse(content={"status": "error", "message": "Invalid signature. Please check your channel access token/channel secret."}, status_code=status.HTTP_400_BAD_REQUEST)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text))


# 起動
if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)