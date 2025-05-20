import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
from opencc import OpenCC

app = Flask(__name__)

# 讀取 LINE 環境變數
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

cc = OpenCC('s2t')  # 將簡體轉成繁體

# 偵測文字中是否包含中文
def contains_chinese(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)

# 偵測文字中是否包含日文（假名）
def contains_japanese(text):
    return any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in text)

def translate_text(text):
    if contains_chinese(text):
        langpair = "zh-TW|ja"
    elif contains_japanese(text):
        langpair = "ja|zh-TW"
    else:
        return "請輸入中文或日文來翻譯喔！"

    url = "https://api.mymemory.translated.net/get"
    params = {
        "q": text,
        "langpair": langpair
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        translated_text = data.get("responseData", {}).get("translatedText", "")
        if not translated_text:
            return "翻譯失敗，請稍後再試。"
        # 如果翻譯結果是簡體中文，轉成繁體
        if langpair == "ja|zh-TW":
            translated_text = cc.convert(translated_text)
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
