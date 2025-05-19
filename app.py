import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def translate_text(text):
    try:
        # 簡單判斷語言（中文 or 印尼文）
        if any('\u4e00' <= c <= '\u9fff' for c in text):
            source = "zh"
            target = "id"
        else:
            source = "id"
            target = "zh"

        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": f"{source}|{target}"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        translated_text = data.get("responseData", {}).get("translatedText")
        if not translated_text:
            return "翻譯錯誤，請稍後再試。"
        return translated_text
    except Exception as e:
        print("翻譯錯誤：", str(e))
        return f"翻譯錯誤：{str(e)}"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    translated = translate_text(user_text)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=translated)
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
