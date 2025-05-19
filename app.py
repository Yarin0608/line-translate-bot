import os
import re
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境變數
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ 語言簡易判斷：包含中文字元 → 中文；純拉丁字母 → 印尼文
def detect_language(text):
    if re.search(r'[\u4e00-\u9fff]', text):
        return "zh"
    elif re.fullmatch(r'[a-zA-Z\s]+', text):
        return "id"
    else:
        return None

# ✅ 翻譯函數（LibreTranslate）
def translate_text(text):
    source_lang = detect_language(text)
    if source_lang is None:
        return "無法判斷語言，只支援中文與印尼文。"

    target_lang = "id" if source_lang == "zh" else "zh"

    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }

    try:
        response = requests.post("https://libretranslate.de/translate", data=payload, timeout=5)
        response.raise_for_status()
        translated = response.json().get("translatedText")
        return translated if translated else "翻譯失敗，請稍後再試。"
    except Exception as e:
        return f"翻譯錯誤：{e}"

# ✅ LINE Webhook 接收入口
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ✅ 處理 LINE 訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    translated = translate_text(user_text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=translated))

# ✅ 啟動 Flask
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
