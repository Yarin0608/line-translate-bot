import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
from opencc import OpenCC
from langdetect import detect  # 語言偵測

app = Flask(__name__)

# 讀取 LINE 環境變數
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN):
    raise Exception("請先設定 LINE_CHANNEL_SECRET 與 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

cc = OpenCC('s2t')  # 將簡體轉成繁體

def translate_text(text):
    try:
        detected_lang = detect(text)
    except Exception:
        return "⚠️ 無法判斷語言，請輸入更完整的句子喔！"

    if detected_lang in ["zh-cn", "zh-tw"]:
        langpair =
