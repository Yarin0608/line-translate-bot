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

# 判斷是否包含平假名或片假名（即日文）
def contains_japanese_kana(text):
    return any('\u3040' <= c <= '\u30ff' for c in text)

# 判斷是否包含中文字（但不一定是中文語言）
def contains_chinese_char(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def translate_text(text):
    # 如果有假名，視為日文 → 翻譯成中文
    if contains_japanese_kana(text):
        langpair = "ja|zh-TW"
    # 否則如果只有中文字，視為中文 → 翻譯成日文
    elif contains_chinese_char(text):
        langpair = "zh-TW|ja"
    else:
        return "請輸入中文或日文來翻譯喔！翻訳するには中国語または日本語を入力してください。"

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
        # 若翻成中文，先轉繁體
        if langpair == "ja|zh-TW":
            translated_text = OpenCC('s2t').convert(translated_text)
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
