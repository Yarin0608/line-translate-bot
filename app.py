import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests

app = Flask(__name__)

# 讀環境變數
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def translate_text(text):
    # 簡單判斷是否含中文，有中文就中→印尼，否則印尼→中
    if any('\u4e00' <= char <= '\u9fff' for char in text):
        source_lang = "zh"
        target_lang = "id"
    else:
        source_lang = "id"
        target_lang = "zh"

    url = "https://libretranslate.de/translate"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        translated_text = data.get("translatedText")
        if not translated_text:
            return "翻譯失敗，沒有取得翻譯結果"
        return translated_text
    except Exception as e:
        print("翻譯錯誤:", e)
        return "翻譯出錯，請稍後再試。"

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
