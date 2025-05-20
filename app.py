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

# 建立簡轉繁轉換器
cc = OpenCC('s2t')

# 判斷是否為日文（包含平假名、片假名、日文漢字）
def is_japanese(text):
    return any(
        '\u3040' <= c <= '\u309F' or  # 平假名
        '\u30A0' <= c <= '\u30FF' or  # 片假名
        '\u4E00' <= c <= '\u9FFF'     # 漢字（中文和日文共用）
        for c in text
    )

def translate_text(text):
    # 判斷是否為日文
    if is_japanese(text):
        langpair = "ja|zh-TW"
    else:
        langpair = "auto|ja"

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
    translated = translate_text_
