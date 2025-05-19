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

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise Exception("請設定 LINE_CHANNEL_SECRET 和 LINE_CHANNEL_ACCESS_TOKEN 環境變數")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def detect_language(text):
    # 自動語言判斷（LibreTranslate 支援）
    url = "https://libretranslate.de/detect"
    try:
        response = requests.post(url, data={"q": text}, timeout=5)
        response.raise_for_status()
        lang_code = response.json()[0]['language']
        return lang_code
    except Exception as e:
        print("語言判斷錯誤：", e)
        return "zh"  # 預設中文

def translate_text(text):
    source_lang = detect_language(text)
    target_lang = "id" if source_lang == "zh" else "zh"

    url = "https://libretranslate.de/translate"
    payload = {
        "q": text,
        "source": source_lang,
        "target": target_lang,
        "format": "text"
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        translated_text = data.get("translatedText")
        if translated_text:
            return translated_text
        else:
            print("翻譯錯誤：找不到 translatedText")
            return "翻譯錯誤，請稍後再試。"
    except Exception as e:
        print("翻譯錯誤：", e)
        return "翻譯出錯，請稍後再試。"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except Exception as e:
        print("處理訊息時錯誤：", e)
        # 即使錯誤也讓 LINE 收到 200 回應
        return "OK"

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
