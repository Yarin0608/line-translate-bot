import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 讀取環境變數
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 使用 LibreTranslate 免費 API
def translate_text(text):
    try:
        # 自動偵測來源語言並翻譯為對應語言
        data = {
            "q": text,
            "source": "auto",
            "target": detect_target_language(text),
            "format": "text"
        }
        response = requests.post("https://libretranslate.com/translate", data=data)
        translated = response.json()["translatedText"]
        return translated
    except Exception as e:
        print(f"翻譯錯誤：{e}")
        return "翻譯出錯，請稍後再試。"

# 偵測文字語言並決定翻譯方向（中翻印或印翻中）
def detect_target_language(text):
    # 假設含有中文字就翻成印尼文，否則翻成中文
    if any('\u4e00' <= c <= '\u9fff' for c in text):
        return "id"  # 翻譯成印尼文
    else:
        return "zh"  # 翻譯成中文

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
