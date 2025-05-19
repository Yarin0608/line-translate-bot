import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# LibreTranslate API URL (免費版本不用 key)
LIBRETRANSLATE_URL = "https://libretranslate.com/translate"

def translate_text(text):
    # 判斷語言簡單示範，中文就翻印尼文，反之亦然
    source_lang = "zh"
    target_lang = "id"
    if any('\u4e00' <= ch <= '\u9fff' for ch in text):
        source_lang = "zh"
        target_lang = "id"
    else:
        source_lang = "id"
        target_lang = "zh"

    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }

    try:
        res = requests.post(LIBRETRANSLATE_URL, data=payload, timeout=5)
        res.raise_for_status()
        result = res.json()
        return result.get("translatedText", "翻譯失敗")
    except Exception as e:
        print("LibreTranslate error:", e)
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
