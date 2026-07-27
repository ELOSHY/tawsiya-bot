from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8722634125:AAE0N7Uj5FLlG8KRUeEDKYgFxuK11ShxX4o')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '-1004107657002')

# قاموس أسماء الأسهم السعودية
STOCK_NAMES = {
    "1010": "الرياض", "1020": "بنك الجزيرة", "1030": "الراجحي",
    "1050": "البنك السعودي البريطاني", "1060": "البنك السعودي الفرنسي",
    "1080": "العربي", "1120": "الأهلي", "1140": "البنك السعودي للاستثمار",
    "1150": "الأول", "1180": "سامبا", "1202": "مبكو",
    "1210": "التصنيع", "1211": "معادن", "1212": "أسترا الصناعية",
    "1213": "الصناعات الوطنية", "1214": "الصناعات الكيميائية",
    "1301": "أسمنت العربية", "1302": "أسمنت اليمامة", "1303": "أسمنت السعودية",
    "1304": "أسمنت القصيم", "1305": "أسمنت الجنوب", "1320": "أسمنت الجوف",
    "1321": "أنابيب الشرق", "1322": "أسمنت الشمالية", "1330": "أسمنت ينبع",
    "1810": "زين السعودية", "1820": "موبايلي", "1833": "الموارد للقوى البشرية",
    "2010": "سابك", "2020": "الصدارة", "2030": "بترو رابغ",
    "2060": "الكيميائية السعودية", "2070": "الزيت العربية", "2080": "نماء للكيماويات",
    "2090": "نهضة", "2110": "اللجين", "2150": "فيبكو",
    "2160": "جبسكو", "2170": "الجبس", "2180": "الزجاج",
    "2200": "أرامكو السعودية", "2222": "أرامكو",
    "2270": "السعودية للكهرباء", "2280": "الغاز والتصنيع", "2282": "الغاز والتصنيع",
    "2290": "الشرق الأوسط للتكرير", "2300": "السعودية للصناعات الأساسية",
    "2310": "سيبكو", "2320": "الخزف السعودي", "2330": "المتقدمة",
    "2340": "وفرة", "2350": "الكيماويات الدولية", "2360": "بترو رابغ",
    "3002": "يونيفرست", "3003": "الحكير", "3004": "الشاطئ",
    "3005": "أسواق عبدالله العثيم", "3007": "الواحة", "3008": "المراعي",
    "3010": "سدافكو", "3020": "نادك", "3030": "الجوف للزراعة",
    "3040": "الشرقية للتنمية", "3050": "سمكو", "3060": "الوطنية للزراعة",
    "3080": "فيفا", "3090": "جاكو",
    "4001": "ثمار", "4002": "المستشفى السعودي الألماني", "4004": "دله الصحية",
    "4005": "رعاية", "4007": "أنعام القابضة", "4008": "المنار",
    "4009": "الحمادي", "4013": "بيبان", "4015": "جمجوم فارما",
    "4016": "الأمل", "4017": "المتحدة للطبية", "4018": "الموسى الصحية",
    "4020": "الدواء", "4030": "الصحة", "4031": "الشرق الأوسط للرعاية الصحية",
    "4040": "بوبا العربية", "4050": "ساسكو", "4051": "المملكة القابضة",
    "4061": "الوطنية للتعليم", "4070": "المدارس العالمية", "4071": "تعليم",
    "4080": "فتيحي", "4083": "تسهيل", "4100": "وادي النيل",
    "4110": "عسير", "4130": "جازان", "4140": "نجران",
    "4141": "الحجاز", "4142": "الباحة", "4143": "حائل",
    "4144": "تبوك", "4145": "القصيم", "4146": "جاز العربية للخدمات",
    "4150": "اليمامة", "4160": "الجزيرة", "4161": "الرياض",
    "4162": "الوطن", "4163": "عكاظ", "4164": "السعودية للصحافة",
    "4170": "بدجت السعودية", "4180": "الجميح", "4190": "اليوسف",
    "4191": "الصالح", "4200": "الدريس", "4210": "عبدالله العثيم",
    "4220": "المنيع", "4230": "الأنماء", "4240": "الحسن",
    "4250": "الشايع", "4260": "الزامل للتجزئة", "4270": "الجبر",
    "4280": "الخليج", "4290": "الحكير", "4291": "الشاطئ",
    "4292": "الراشد", "4300": "الشركة السعودية للخدمات الأرضية",
    "4310": "الطيران السعودي", "4320": "نقل", "4330": "سبل",
    "4331": "بدجت", "4332": "لومي", "4333": "الأجيال",
    "4334": "البحري", "4335": "الشحن الدولي", "4336": "الخطوط السعودية",
    "4337": "ناقلات", "4338": "موانئ", "4339": "سار",
    "4340": "الخطوط الجوية", "4341": "فلاي",
    "6010": "الأسمنت العربي", "6012": "الأسمنت السعودي",
    "6013": "الأسمنت الغربي", "6014": "الأسمنت الشرقي",
    "6015": "الأسمنت اليمامة", "6020": "الأسمنت القصيم",
    "6040": "الأسمنت الجوف", "6050": "الأسمنت ينبع",
    "7010": "الاتصالات السعودية", "7020": "موبايلي",
    "7030": "زين السعودية", "7040": "قو للاتصالات", "7203": "علم",
    "8010": "التعاونية", "8020": "الراجحي للتأمين", "8030": "ملاذ",
    "8040": "سلامة", "8050": "الأهلية", "8060": "بوبا",
    "8070": "الاتحاد الخليجي", "8100": "ميدغلف", "8120": "الخليجية للتأمين",
    "8150": "أليانز", "8160": "الوطنية للتأمين", "8170": "الإعادة السعودية",
    "8230": "الدرع العربي", "8240": "أمانة", "8250": "الصقر",
    "8260": "الأمان", "8270": "العالمية للتأمين",
    "8310": "الشركة السعودية للتأمين", "9500": "أرامكو",
}

def get_stock_name(ticker):
    clean = ticker.replace("TADAWUL:", "").replace("TASI:", "").strip()
    return STOCK_NAMES.get(clean, clean)

def safe_float(val):
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None

def format_num(val):
    if val is None:
        return "غير محدد"
    if val == int(val):
        return str(int(val))
    return f"{val:.2f}".rstrip('0').rstrip('.')

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

        ticker = data.get('ticker', 'غير محدد')
        stock_name = data.get('stock_name', None)
        if not stock_name or stock_name == ticker:
            stock_name = get_stock_name(ticker)

        price = safe_float(data.get('price'))
        stop_loss = safe_float(data.get('sl') or data.get('stop_loss') or data.get('plot_0'))
        target_1  = safe_float(data.get('tp1') or data.get('target_1') or data.get('plot_1'))
        target_2  = safe_float(data.get('tp2') or data.get('target_2') or data.get('plot_2'))
        target_3  = safe_float(data.get('tp3') or data.get('target_3') or data.get('plot_3'))

        # حساب SL وTP تلقائياً إذا كانت null
        if price and (stop_loss is None or target_1 is None):
            risk = price * 0.02
            if stop_loss is None:
                stop_loss = round(price - risk, 2)
            if target_1 is None:
                target_1 = round(price + risk * 1.0, 2)
            if target_2 is None:
                target_2 = round(price + risk * 2.0, 2)
            if target_3 is None:
                target_3 = round(price + risk * 3.0, 2)

        time_val = data.get('time', data.get('tf', datetime.now().strftime('%H:%M')))
        tqi   = data.get('tqi', None)
        score = data.get('score', None)
        clean_ticker = ticker.replace("TADAWUL:", "").replace("TASI:", "").strip()

        message = (
            f"🟢 <b>إشارة شراء جديدة!</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 <b>السهم:</b> {stock_name} ({clean_ticker})\n"
            f"💰 <b>سعر الدخول:</b> {format_num(price)}\n"
            f"🛑 <b>وقف مضاربي:</b> {format_num(stop_loss)}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚽ <b>الهدف الأول:</b> {format_num(target_1)}\n"
            f"⚽ <b>الهدف الثاني:</b> {format_num(target_2)}\n"
            f"⚽ <b>الهدف الثالث:</b> {format_num(target_3)}\n"
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
