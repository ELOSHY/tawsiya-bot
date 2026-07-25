from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8722634125:AAE0N7Uj5FLlG8KRUeEDKYgFxuK11ShxX4o')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '-1004107657002')

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    response = requests.post(url, json=payload )
    return response.json()

@app.route('/', methods=['GET'])
def home():
    return "✅ TawsiyaPlus Bot is Running!", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400

        action = data.get('action', 'buy').lower()
        if action == 'sell':
            return jsonify({"status": "ignored"}), 200

        ticker     = data.get('ticker', 'غير محدد')
        stock_name = data.get('stock_name', ticker)
        price      = data.get('price', 'غير محدد')
        stop_loss  = data.get('sl', data.get('stop_loss', 'غير محدد'))
        target_1   = data.get('tp1', data.get('target_1', 'غير محدد'))
        target_2   = data.get('tp2', data.get('target_2', 'غير محدد'))
        target_3   = data.get('tp3', data.get('target_3', 'غير محدد'))
        time_val   = data.get('time', data.get('tf', datetime.now().strftime('%H:%M')))
        tqi        = data.get('tqi', None)
        score      = data.get('score', None)

        message = (
            f"🟢 <b>إشارة شراء جديدة!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 <b>السهم:</b> {stock_name} ({ticker})\n"
            f"💰 <b>سعر الدخول:</b> {price}\n"
            f"🛑 <b>وقف مضاربي:</b> {stop_loss}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚽ <b>الهدف الأول:</b> {target_1}\n"
            f"⚽ <b>الهدف الثاني:</b> {target_2}\n"
            f"⚽ <b>الهدف الثالث:</b> {target_3}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⏰ <b>الإطار الزمني:</b> {time_val}\n"
        )
        if tqi is not None:
            message += f"📈 <b>جودة الإشارة (TQI):</b> {tqi}\n"
        if score is not None:
            message += f"🏆 <b>قوة الإشارة:</b> {score}/100\n"
        message += f"━━━━━━━━━━━━━━━\n⚠️ <i>هذه التوصيات للأغراض التعليمية فقط</i>"

        result = send_telegram_message(message)
        return jsonify({"status": "success", "telegram_response": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
