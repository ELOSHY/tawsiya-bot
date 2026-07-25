from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# إعدادات Telegram
TELEGRAM_TOKEN = "8722634125:AAE0N7Uj5FLlG8KRUeEDKYgFxuK11ShxX4o"
CHAT_ID = "-5301355043"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload)
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

        # استخراج البيانات من TradingView
        ticker    = data.get('ticker', 'غير محدد')
        price     = data.get('price', 'غير محدد')
        stop_loss = data.get('stop_loss', 'غير محدد')
        target_1  = data.get('target_1', 'غير محدد')
        target_2  = data.get('target_2', 'غير محدد')
        target_3  = data.get('target_3', 'غير محدد')
        time_val  = data.get('time', 'غير محدد')

        # استخراج اسم السهم
        stock_name = data.get('stock_name', ticker)

        # تنسيق الرسالة
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
            f"⏰ <b>التوقيت:</b> {time_val}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>هذه التوصيات للأغراض التعليمية فقط</i>"
        )

        result = send_telegram_message(message)
        return jsonify({"status": "success", "telegram_response": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
