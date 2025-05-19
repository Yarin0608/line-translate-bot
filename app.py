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

# 使用較穩定的 LibreTranslate 節點
TRANSLATE_URL = "https://translate.argosopentech.com"

def detect_language(text):
    try:
        response = requests.post(
            f"{TRANSLATE_URL}/detect",
            data={"q": text},
            timeout=5
        )
        print("語言偵測原始回應：", response.text)
        data = response.json()
        return data[0]["language"] if data else None
    except Exception as e:
        print("語言判斷錯誤：", str(e))
        return None

def translate_text(text):
    source_lang = detect_language(text)
    if source_lang not in ["zh", "id"]:
        return "⚠️ 無法辨識語言，只支援中文與印尼文。"

    target_lang = "id" if source_lang == "zh" else "zh"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }

    try:
        response = requests.post(f"{TRANSLATE_URL}/translate", data=payload, timeout=10)
        print("翻譯原始回應：", response.text)
        data = response.json()
        translated_text = data.get("translatedText")
        return translated_text if translated_text else "⚠️ 翻譯失敗，請稍後再試。"
    except Exception as e:
        print("翻譯錯誤：", str(e))
        return "⚠️ 翻譯出錯，請稍後再試。"

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
