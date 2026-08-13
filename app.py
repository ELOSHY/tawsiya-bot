from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime
import threading
from bs4 import BeautifulSoup
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8722634125:AAE0N7Uj5FLlG8KRUeEDKYgFxuK11ShxX4o')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '-1004107657002')

# ══════════════════════════════════════════════════════════
# قاموس أسماء الأسهم السعودية - شامل (مصدر: تداول الرسمي)
# ══════════════════════════════════════════════════════════
STOCK_NAMES = {
    "1010": "الرياض",
    "1020": "الجزيرة",
    "1030": "الإستثمار",
    "1050": "بي اس اف",
    "1060": "الأول",
    "1080": "العربي",
    "1111": "مجموعة تداول",
    "1120": "الراجحي",
    "1140": "البلاد",
    "1150": "الإنماء",
    "1180": "الأهلي",
    "1182": "أملاك",
    "1183": "سهل",
    "1201": "تكوين",
    "1202": "مبكو",
    "1210": "بي سي آي",
    "1211": "معادن",
    "1212": "أسترا الصناعية",
    "1213": "نسيج",
    "1214": "شاكر",
    "1301": "أسلاك",
    "1302": "بوان",
    "1303": "الصناعات الكهربائية",
    "1304": "اليمامة للحديد",
    "1320": "أنابيب السعودية",
    "1321": "أنابيب الشرق",
    "1322": "أماك",
    "1323": "يو سي آي سي",
    "1324": "صالح الراشد",
    "1810": "سيرا",
    "1820": "بان",
    "1830": "لجام للرياضة",
    "1831": "مهارة",
    "1832": "صدر",
    "1833": "الموارد",
    "1834": "سماسكو",
    "1835": "تمكين",
    "2001": "كيمانول",
    "2010": "سابك",
    "2020": "سابك للمغذيات الزراعية",
    "2040": "الخزف السعودي",
    "2050": "مجموعة صافولا",
    "2060": "التصنيع",
    "2070": "الدوائية",
    "2080": "الغاز القابضة",
    "2081": "الخريف",
    "2082": "أكوا",
    "2083": "مرافق",
    "2084": "مياهنا",
    "2090": "جبسكو",
    "2100": "وفرة",
    "2110": "الكابلات السعودية",
    "2120": "متطورة",
    "2130": "صدق",
    "2140": "أيان",
    "2150": "زجاج",
    "2160": "أميانتيت",
    "2170": "اللجين",
    "2180": "فيبكو",
    "2190": "سيسكو القابضة",
    "2200": "أنابيب",
    "2210": "نماء للكيماويات",
    "2220": "معدنية",
    "2222": "أرامكو السعودية",
    "2223": "لوبريف",
    "2230": "الكيميائية",
    "2240": "صناعات",
    "2250": "المجموعة السعودية",
    "2270": "سدافكو",
    "2280": "المراعي",
    "2281": "تنمية",
    "2282": "نقي",
    "2283": "المطاحن الأولى",
    "2284": "المطاحن الحديثة",
    "2285": "المطاحن العربية",
    "2286": "المطاحن الرابعة",
    "2287": "إنتاج",
    "2288": "نفوذ",
    "2290": "ينساب",
    "2300": "صناعة الورق",
    "2310": "سبكيم العالمية",
    "2320": "البابطين",
    "2330": "المتقدمة",
    "2340": "ارتيكس",
    "2350": "كيان السعودية",
    "2360": "الفخارية",
    "2370": "مسك",
    "2380": "بترو رابغ",
    "2381": "الحفر العربية",
    "2382": "أديس",
    "3002": "أسمنت نجران",
    "3003": "أسمنت المدينة",
    "3004": "أسمنت الشمالية",
    "3005": "أسمنت ام القرى",
    "3007": "الواحة",
    "3008": "الكثيري",
    "3010": "أسمنت العربية",
    "3020": "أسمنت اليمامة",
    "3030": "أسمنت السعودية",
    "3040": "أسمنت القصيم",
    "3050": "أسمنت الجنوب",
    "3060": "أسمنت ينبع",
    "3080": "أسمنت الشرقية",
    "3090": "أسمنت تبوك",
    "3091": "أسمنت الجوف",
    "3092": "أسمنت الرياض",
    "4001": "أسواق ع العثيم",
    "4002": "المواساة",
    "4003": "إكسترا",
    "4004": "دله الصحية",
    "4005": "رعاية",
    "4006": "أسواق المزرعة",
    "4007": "الحمادي",
    "4008": "ساكو",
    "4009": "السعودي الألماني الصحية",
    "4011": "لازوردي",
    "4012": "الأصيل",
    "4013": "سليمان الحبيب",
    "4014": "دار المعدات",
    "4015": "جمجوم فارما",
    "4016": "أفالون فارما",
    "4017": "فقيه الطبية",
    "4018": "الموسى",
    "4019": "اس ام سي للرعاية الصحية",
    "4020": "العقارية",
    "4021": "المركز الكندي الطبي",
    "4030": "البحري",
    "4031": "الخدمات الأرضية",
    "4040": "سابتكو",
    "4050": "ساسكو",
    "4051": "باعظيم",
    "4061": "أنعام القابضة",
    "4070": "تهامة",
    "4071": "العربية",
    "4072": "مجموعة إم بي سي",
    "4080": "سناد القابضة",
    "4081": "النايفات",
    "4082": "مرنة",
    "4083": "تسهيل",
    "4084": "دراية",
    "4090": "طيبة",
    "4100": "مكة",
    "4110": "باتك",
    "4130": "درب السعودية",
    "4140": "صادرات",
    "4141": "العمران",
    "4142": "كابلات الرياض",
    "4143": "تالكو",
    "4144": "رؤوم",
    "4145": "أو جي سي",
    "4146": "جاز",
    "4147": "سي جي إس",
    "4148": "الوسائل الصناعية",
    "4150": "التعمير",
    "4160": "ثمار",
    "4161": "بن داود",
    "4162": "المنجم",
    "4163": "الدواء",
    "4164": "النهدي",
    "4165": "الماجد للعود",
    "4170": "شمس",
    "4180": "مجموعة فتيحي",
    "4190": "جرير",
    "4191": "أبو معطي",
    "4192": "السيف غاليري",
    "4193": "نايس ون",
    "4194": "محطة البناء",
    "4200": "الدريس",
    "4210": "الأبحاث والإعلام",
    "4220": "إعمار",
    "4230": "البحر الأحمر",
    "4240": "سينومي ريتيل",
    "4250": "جبل عمر",
    "4260": "بدجت السعودية",
    "4261": "ذيب",
    "4262": "لومي",
    "4263": "سال",
    "4264": "طيران ناس",
    "4265": "شري",
    "4270": "طباعة وتغليف",
    "4280": "المملكة",
    "4290": "الخليج للتدريب",
    "4291": "الوطنية للتعليم",
    "4292": "عطاء",
    "4300": "دار الأركان",
    "4310": "مدينة المعرفة",
    "4320": "الأندلس",
    "4321": "سينومي سنترز",
    "4322": "رتال",
    "4323": "سمو",
    "4324": "بنان",
    "4325": "مسار",
    "4326": "الماجدية",
    "4327": "الرمز",
    "4330": "الرياض ريت",
    "4331": "الجزيرة ريت",
    "4332": "جدوى ريت الحرمين",
    "4333": "تعليم ريت",
    "4334": "المعذر ريت",
    "4335": "مشاركة ريت",
    "4336": "ملكية ريت",
    "4337": "العزيزية ريت",
    "4338": "الأهلي ريت 1",
    "4339": "دراية ريت",
    "4340": "الراجحي ريت",
    "4342": "جدوى ريت السعودية",
    "4344": "سدكو كابيتال ريت",
    "4345": "الإنماء ريت للتجزئة",
    "4346": "ميفك ريت",
    "4347": "بنيان ريت",
    "4348": "الخبير ريت",
    "4349": "الإنماء ريت الفندقي",
    "4350": "الإستثمار ريت",
    "5110": "السعودية للطاقة",
    "6001": "حلواني إخوان",
    "6002": "هرفي للأغذية",
    "6004": "كاتريون",
    "6010": "نادك",
    "6012": "ريدان",
    "6013": "التطويرية الغذائية",
    "6014": "الآمار",
    "6015": "أمريكانا",
    "6016": "برغرايززر",
    "6017": "جاهز",
    "6018": "الأندية للرياضة",
    "6019": "المسار الشامل",
    "6020": "جاكو",
    "6040": "تبوك الزراعية",
    "6050": "الأسماك",
    "6060": "الشرقية للتنمية",
    "6070": "الجوف",
    "6090": "جازادكو",
    "7010": "اس تي سي",
    "7020": "إتحاد إتصالات",
    "7030": "زين السعودية",
    "7040": "قو للإتصالات",
    "7200": "ام آي اس",
    "7201": "بحر العرب",
    "7202": "سلوشنز",
    "7203": "علم",
    "7204": "توبي",
    "7205": "دي بي اس",
    "7211": "عزم",
    "8010": "التعاونية",
    "8012": "جزيرة تكافل",
    "8020": "ملاذ للتأمين",
    "8030": "ميدغلف للتأمين",
    "8040": "متكاملة",
    "8050": "سلامة",
    "8060": "ولاء",
    "8070": "الدرع العربي",
    "8100": "سايكو",
    "8120": "إتحاد الخليج الأهلية",
    "8150": "أسيج",
    "8160": "التأمين العربية",
    "8170": "الاتحاد",
    "8180": "الصقر للتأمين",
    "8190": "المتحدة للتأمين",
    "8200": "الإعادة السعودية",
    "8210": "بوبا العربية",
    "8230": "تكافل الراجحي",
    "8240": "تْشب",
    "8250": "جي آي جي",
    "8260": "الخليجية العامة",
    "8280": "ليفا",
    "8300": "الوطنية",
    "8310": "أمانة للتأمين",
    "8311": "عناية",
    "8313": "رسن",
    "9300": "الواحة ريت",
    "9510": "الوطنية للبناء والتسويق",
    "9514": "الناقول",
    "9515": "فش فاش",
    "9516": "غاز",
    "9517": "موبي للصناعة",
    "9521": "إنمار",
    "9522": "الحاسوب",
    "9523": "جروب فايف",
    "9524": "آيكتك",
    "9527": "ألف ميم ياء",
    "9530": "طبية",
    "9532": "حلوة",
    "9533": "المركز الآلي",
    "9535": "لدن",
    "9536": "فاديكو",
    "9537": "أمواج الدولية",
    "9538": "نسيج للتقنية",
    "9539": "أقاسيم",
    "9540": "تدوير",
    "9541": "أكاديمية التعلم",
    "9542": "كير",
    "9543": "نت وركرس",
    "9544": "الرعاية المستقبلية",
    "9545": "الدولية",
    "9546": "نبع الصحة",
    "9547": "رواسي",
    "9548": "ابيكو",
    "9549": "البابطين الغذائية",
    "9550": "شور",
    "9551": "برج المعرفة",
    "9552": "قمة السعودية",
    "9553": "ملان",
    "9555": "لين الخير",
    "9557": "إدارات",
    "9558": "القمم",
    "9559": "بلدي",
    "9560": "وجا",
    "9561": "نولجنت",
    "9562": "بوابة الأطعمة",
    "9563": "بناء",
    "9564": "آفاق الغذاء",
    "9565": "معيار",
    "9566": "الصناعات الجيرية",
    "9567": "غذاء السلطان",
    "9568": "ميار",
    "9569": "آل منيف",
    "9570": "تام التنموية",
    "9571": "مناوله",
    "9572": "الرازي",
    "9574": "بروميديكس",
    "9575": "ماربل ديزاين",
    "9576": "منزل الورق",
    "9577": "دار المركبة",
    "9578": "مصاعد أطلس",
    "9579": "رماث",
    "9580": "الراشد للصناعة",
    "9581": "كلين لايف",
    "9583": "المتحدة للتعدين",
    "9584": "ريال",
    "9585": "ملكية",
    "9586": "أصول وبخيت",
    "9587": "لانا",
    "9588": "حديد الرياض",
    "9589": "فاد",
    "9590": "أرماح",
    "9591": "فيو",
    "9592": "المجتمع الطبية",
    "9593": "عبر الخليج",
    "9594": "المداواة",
    "9595": "وسم",
    "9596": "كوارا",
    "9597": "الليف",
    "9598": "المحافظة للتعليم",
    "9599": "طاقات",
    "9600": "كومل",
    "9601": "الرشيد",
    "9602": "يقين",
    "9603": "الأفق التعليمية",
    "9604": "ميرال",
    "9605": "نفط الشرق",
    "9606": "ثروة",
    "9607": "عسق",
    "9608": "الأشغال الميسرة",
    "9609": "بترول ناس",
    "9610": "الجادة الأولى",
    "9611": "المتحدة للزجاج المسطح",
    "9612": "مياه سما",
    "9613": "شلفا",
    "9614": "نقاوة",
    "9615": "مفيد",
    "9616": "جنى",
    "9617": "ارابيكا ستار",
    "9618": "الفاخرة",
    "9619": "الأعمال المتعددة",
    "9620": "بلسم الطبية",
    "9621": "دي آر سي",
    "9622": "شموع الماضي",
    "9623": "مصنع البتال",
    "9624": "الشهيلي المعدنية",
    "9625": "إتمام",
    "9626": "سمايل كير",
    "9627": "طوارئيات",
    "9628": "لمسات",
    "9630": "ريشيو",
    "9631": "هضاب الخليج",
    "9632": "رؤية المستقبل",
    "9633": "آلات الصيانة",
    "9634": "أدير",
    "9635": "دخون",
    "9636": "الخزامى",
    "9637": "الحلول المتسارعة",
    "9639": "أنماط",
    "9640": "أساس مكين",
    "9641": "هوية",
    "9642": "تايم",
    "9644": "ناف",
    "9645": "ساين وورلد",
    "9647": "وجد الحياة",
    "9648": "حمد بن سعيدان العقارية",
    "9649": "جمجوم فاشن",
    "9650": "ساحة المجد",
    "9651": "التويجري",
    "9653": "خالد ظافر وإخوانه",
    "9655": "مسقا",
}


def get_stock_name(ticker):
    """استخراج اسم السهم من رمزه"""
    clean = ticker.replace("TADAWUL:", "").replace("TASI:", "").strip()
    return STOCK_NAMES.get(clean, clean)


def safe_float(val):
    """تحويل القيمة لـ float بأمان"""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0 else None
    except (ValueError, TypeError):
        return None


def format_num(val):
    """تنسيق الرقم للعرض"""
    if val is None:
        return "غير محدد"
    try:
        if float(val) == int(float(val)):
            return str(int(float(val)))
        return f"{float(val):.2f}".rstrip('0').rstrip('.')
    except:
        return str(val)


def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
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

        action = str(data.get('action', '')).lower().strip()
        ticker = data.get('ticker', 'غير محدد')
        clean_ticker = ticker.replace("TADAWUL:", "").replace("TASI:", "").strip()

        # إذا لم يكن هناك action لكن فيه sl وtp1 → اعتبره شراء
        if not action and (data.get('sl') or data.get('tp1') or data.get('price')):
            action = 'buy'

        # ── إشارة شراء ──────────────────────────────────────
        if action == 'buy':
            stock_name = get_stock_name(ticker)

            price      = safe_float(data.get('price'))
            entry_low  = safe_float(data.get('entry_low'))
            entry_high = safe_float(data.get('entry_high'))
            stop_loss  = safe_float(data.get('sl') or data.get('stop_loss') or data.get('plot_0'))
            target_1   = safe_float(data.get('tp1') or data.get('target_1') or data.get('plot_1'))
            target_2   = safe_float(data.get('tp2') or data.get('target_2') or data.get('plot_2'))
            target_3   = safe_float(data.get('tp3') or data.get('target_3') or data.get('plot_3'))

            # إذا جاء entry_low وentry_high بدل price، نستخدم المتوسط للحسابات
            if entry_low and entry_high and not price:
                price = round((entry_low + entry_high) / 2, 2)

            # منطقة الدخول الافتراضية: دائماً رقمين حول سعر الإشارة.
            # تقبل zone كبوليان أو نص، وتبقى مفعّلة افتراضياً لحماية الرسائل القديمة.
            zone_value = data.get('zone', True)
            zone_enabled = str(zone_value).strip().lower() in {'true', '1', 'yes', 'on'}
            if zone_enabled and price and not (entry_low and entry_high):
                entry_low = round(price * 0.99, 2)
                entry_high = round(price * 1.005, 2)

            # حساب SL وTP تلقائياً إذا كانت null (2% افتراضي)
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
            tqi      = data.get('tqi', None)
            score    = data.get('score', None)

            message = (
                f"🟢 <b>إشارة شراء جديدة!</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📊 <b>السهم:</b> {stock_name} ({clean_ticker})\n"
                f"💰 <b>منطقة الدخول:</b> {format_num(entry_low) + ' - ' + format_num(entry_high) if entry_low and entry_high else format_num(price)}\n"
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
            # إضافة لقائمة التوصيات النشطة
            try:
                add_active_signal(clean_ticker, get_stock_name(ticker), price, stop_loss, target_1, target_2, target_3, timeframe)
            except:
                pass
            return jsonify({"status": "success", "telegram_response": result}), 200
        # ── إشارة بيع → تجاهل (السوق السعودي شراء فقط) ─────
        elif action == 'sell':
            return jsonify({"status": "ignored", "reason": "sell signals ignored"}), 200

        # ── تحقيق هدف TP ─────────────────────────────────────
        elif action in ['tp1', 'tp2', 'tp3', 'tp1_hit', 'tp2_hit', 'tp3_hit']:
            tp_num = action.replace('_hit', '').upper()
            price  = safe_float(data.get('price'))
            stock_name = get_stock_name(ticker)
            message = (
                f"🎯 <b>تم تحقيق {tp_num}!</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📊 <b>السهم:</b> {stock_name} ({clean_ticker})\n"
                f"💰 <b>السعر الحالي:</b> {format_num(price)}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"⚠️ <i>هذه التوصيات للأغراض التعليمية فقط</i>"
            )
            result = send_telegram_message(message)
            return jsonify({"status": "success", "telegram_response": result}), 200

        # ── تفعيل وقف الخسارة ────────────────────────────────
        elif action in ['sl', 'sl_hit', 'stop']:
            price = safe_float(data.get('price'))
            stock_name = get_stock_name(ticker)
            message = (
                f"🛑 <b>تم تفعيل وقف الخسارة</b>\n"
                f"━━━━━━━━━━━━━━━\n"
                f"📊 <b>السهم:</b> {stock_name} ({clean_ticker})\n"
                f"💰 <b>السعر الحالي:</b> {format_num(price)}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"⚠️ <i>هذه التوصيات للأغراض التعليمية فقط</i>"
            )
            result = send_telegram_message(message)
            return jsonify({"status": "success", "telegram_response": result}), 200

        # ── أي إشارة أخرى → تجاهل ────────────────────────────
        else:
            return jsonify({"status": "ignored", "reason": f"unknown action: {action}"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
# نظام مراقبة الأخبار التلقائي - كل 5 دقائق
# ══════════════════════════════════════════════════════════

# مجموعة لتتبع الأخبار المُرسلة ومنع التكرار
sent_news_hashes = set()

def get_news_hash(title):
    """توليد hash مختصر للخبر لمنع التكرار"""
    import hashlib
    return hashlib.md5(title.strip()[:80].encode('utf-8')).hexdigest()[:16]


def fetch_argaam_news():
    """جلب أحدث أخبار تاسي والشركات من fxnewstoday"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'ar,en;q=0.9'
        }
        articles = []
        r = requests.get('https://www.fxnewstoday.ae/stocks/saudi-arabia-news', headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        for sel in ['h2 a', 'h3 a', 'h2', 'h3', 'a']:
            items = soup.select(sel)
            for item in items:
                txt = item.get_text(strip=True)
                if len(txt) > 30 and txt not in articles:
                    articles.append(txt)
            if len(articles) >= 8:
                break
        return articles[:8]
    except Exception as e:
        print(f'fetch_argaam_news error: {e}')
        return []


def fetch_earnings_news():
    """جلب النتائج المالية للشركات السعودية فور صدورها"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                   'Accept-Language': 'ar,en;q=0.9'}
        earnings = []

        # ── مصدر 1: fxnewstoday (أفضل مصدر للنتائج) ──
        try:
            r = requests.get('https://www.fxnewstoday.ae/stocks/saudi-arabia-news', headers=headers, timeout=12)
            soup = BeautifulSoup(r.text, 'html.parser')
            for sel in ['h2 a', 'h3 a', 'h2', 'h3', 'a']:
                items = soup.select(sel)
                for item in items:
                    txt = item.get_text(strip=True)
                    if len(txt) > 30 and any(k in txt for k in ['ربح', 'خسار', 'نتائج', 'أرباح', 'إيراد', 'مالي', 'توزيع']):
                        if txt not in earnings:
                            earnings.append(txt)
                if len(earnings) >= 8:
                    break
        except Exception as e:
            print(f'fxnewstoday earnings error: {e}')

        # ── مصدر 2: argaam الرئيسي ──
        try:
            r2 = requests.get('https://www.argaam.com/ar', headers=headers, timeout=12)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            for sel in ['h2 a', 'h3 a', 'a']:
                items = soup2.select(sel)
                for item in items:
                    txt = item.get_text(strip=True)
                    if len(txt) > 25 and any(k in txt for k in ['ربح', 'خسار', 'نتائج', 'أرباح', 'إيراد', 'مالي']):
                        if txt not in earnings:
                            earnings.append(txt)
                if len(earnings) >= 12:
                    break
        except Exception as e:
            print(f'argaam earnings error: {e}')

        return earnings[:10]
    except Exception as e:
        print(f'fetch_earnings_news error: {e}')
        return []


def fetch_fed_news():
    """جلب أخبار الفيدرالي الأمريكي"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get('https://www.argaam.com/ar/article/articlelist/tag/6', headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles = []
        for sel in ['h2 a', 'h3 a', '.article-title a', 'article a']:
            items = soup.select(sel)
            for item in items:
                txt = item.get_text(strip=True)
                if len(txt) > 25 and ('فيدرالي' in txt or 'فائدة' in txt or 'بنك' in txt or 'Fed' in txt.lower() or 'dollar' in txt.lower() or 'دولار' in txt):
                    if txt not in articles:
                        articles.append(txt)
            if len(articles) >= 3:
                break
        return articles[:3]
    except Exception as e:
        print(f'fetch_fed_news error: {e}')
        return []


def fetch_major_announcements():
    """جلب الإعلانات المهمة: تغييرات كبار الملاك، إعلانات تداول، قرارات مجالس الإدارة"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ar,en;q=0.9'
        }
        announcements = []
        keywords = [
            'تخارج', 'كبار الملاك', 'تغيير ملكية', 'استحواذ',
            'اندماج', 'توزيع أرباح', 'أحقية', 'صرف أرباح',
            'زيادة رأس المال', 'طرح أسهم', 'إصدار صكوك',
            'عقد مهم', 'صفقة', 'شراكة', 'إيقاف تداول',
            'عودة للتداول', 'توقف عن التداول', 'إدراج',
            'خطة استراتيجية', 'تعيين', 'استقالة'
        ]
        # مصدر 1: argaam الرئيسي
        try:
            r = requests.get('https://www.argaam.com/ar', headers=headers, timeout=12)
            soup = BeautifulSoup(r.text, 'html.parser')
            for sel in ['h2 a', 'h3 a', 'a']:
                items = soup.select(sel)
                for item in items:
                    txt = item.get_text(strip=True)
                    if len(txt) > 25 and any(k in txt for k in keywords):
                        if txt not in announcements:
                            announcements.append(txt)
                if len(announcements) >= 8:
                    break
        except Exception as e:
            print(f'major_announcements argaam error: {e}')

        # مصدر 2: موقع تداول السعودية (إعلانات الشركات)
        try:
            r2 = requests.get('https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/issuer-news/issuer-announcements?locale=ar',
                              headers=headers, timeout=12)
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            for sel in ['h2 a', 'h3 a', '.news-title', 'a']:
                items = soup2.select(sel)
                for item in items:
                    txt = item.get_text(strip=True)
                    if len(txt) > 25 and any(k in txt for k in keywords):
                        if txt not in announcements:
                            announcements.append(txt)
                if len(announcements) >= 12:
                    break
        except Exception as e:
            print(f'major_announcements tadawul error: {e}')

        return announcements[:8]
    except Exception as e:
        print(f'fetch_major_announcements error: {e}')
        return []


def fetch_saudi_market_news():
    """جلب أحدث أخبار السوق السعودي من argaam (للتوافق مع الكود القديم)"""
    return fetch_argaam_news()[:5]


def fetch_tasi_data():
    """جلب بيانات مؤشر تاسي"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get('https://www.saudiexchange.sa/wps/portal/saudiexchange/trading/market-summary', headers=headers, timeout=10)
        return None
    except:
        return None


def fetch_breaking_news():
    """جلب الأخبار العاجلة المؤثرة على السوق السعودي (حروب، نفط، جيوسياسية)"""
    breaking = []
    # كلمات مفتاحية للأخبار العاجلة
    BREAKING_KEYWORDS = [
        'حرب', 'ضربة', 'هجوم', 'صاروخ', 'طائرة', 'سفينة', 'انفجار',
        'عقوبات', 'حظر', 'أزمة', 'طوارئ', 'تصعيد',
        'oil', 'crude', 'نفط', 'برميل', 'أوبك', 'opec',
        'فيدرالي', 'فائدة', 'fed', 'rate',
        'ترامب', 'بايدن', 'تصريحات',
        'الحوثي', 'غزة', 'لبنان', 'إيران', 'إسرائيل',
        'سعودي', 'أرامكو', 'سابك', 'تاسي', 'السوق السعودي'
    ]
    try:
        sources = [
            'https://fxnewstoday.com/category/middle-east/',
            'https://fxnewstoday.com/category/commodities/',
            'https://fxnewstoday.com/category/economy/',
        ]
        headers = {'User-Agent': 'Mozilla/5.0'}
        for url in sources:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.text, 'html.parser')
                for tag in soup.find_all(['h2', 'h3', 'h4', 'a'], limit=30):
                    title = tag.get_text(strip=True)
                    if len(title) > 20:
                        title_lower = title.lower()
                        for kw in BREAKING_KEYWORDS:
                            if kw.lower() in title_lower:
                                breaking.append(title)
                                break
            except:
                continue
    except Exception as e:
        print(f'Breaking news error: {e}')
    return list(dict.fromkeys(breaking))[:10]  # إزالة التكرار


def check_and_send_news():
    """فحص الأخبار الجديدة كل 5 دقائق وإرسال غير المكررة"""
    global sent_news_hashes
    try:
        now = datetime.now()
        # فقط أيام العمل (الأحد=6, الاثنين=0, ..., الخميس=3) في ساعات السوق والمساء
        # نرسل من 8 صباحاً حتى 11 مساءً
        if now.hour < 8 or now.hour >= 23:
            return
        # تجاهل الجمعة (4) والسبت (5)
        if now.weekday() in [4, 5]:
            return

        new_items = []

        # ── أخبار تاسي والشركات ──
        tasi_news = fetch_argaam_news()
        for title in tasi_news:
            h = get_news_hash(title)
            if h not in sent_news_hashes:
                sent_news_hashes.add(h)
                new_items.append(('tasi', title))

        # ── النتائج المالية للشركات ──
        earnings_news = fetch_earnings_news()
        for title in earnings_news:
            h = get_news_hash(title)
            if h not in sent_news_hashes:
                sent_news_hashes.add(h)
                new_items.append(('earnings', title))

        # ── أخبار الفيدرالي ──
        fed_news = fetch_fed_news()
        for title in fed_news:
            h = get_news_hash(title)
            if h not in sent_news_hashes:
                sent_news_hashes.add(h)
                new_items.append(('fed', title))

        # ── الأخبار العاجلة (حروب، نفط، جيوسياسية) ──
        breaking_news = fetch_breaking_news()
        for title in breaking_news:
            h = get_news_hash(title)
            if h not in sent_news_hashes:
                sent_news_hashes.add(h)
                new_items.append(('breaking', title))

        # ── تغييرات كبار الملاك وإعلانات تداول ──
        major_news = fetch_major_announcements()
        for title in major_news:
            h = get_news_hash(title)
            if h not in sent_news_hashes:
                sent_news_hashes.add(h)
                new_items.append(('major', title))

        # إرسال الأخبار الجديدة
        if new_items:
            tasi_items     = [t for cat, t in new_items if cat == 'tasi']
            earnings_items = [t for cat, t in new_items if cat == 'earnings']
            fed_items      = [t for cat, t in new_items if cat == 'fed']
            breaking_items = [t for cat, t in new_items if cat == 'breaking']
            major_items    = [t for cat, t in new_items if cat == 'major']

            msg = ''
            if breaking_items:
                msg += '🚨 <b>خبر عاجل يؤثر على السوق!</b>\n━━━━━━━━━━━━━━━\n'
                for i, item in enumerate(breaking_items[:5], 1):
                    msg += f'  {i}. {item[:130]}\n'
                msg += '━━━━━━━━━━━━━━━\n'
            if earnings_items:
                msg += '📊 <b>نتائج مالية جديدة ✨</b>\n━━━━━━━━━━━━━━━\n'
                for i, item in enumerate(earnings_items[:5], 1):
                    msg += f'  {i}. {item[:130]}\n'
                msg += '━━━━━━━━━━━━━━━\n'
            if tasi_items:
                msg += '📢 <b>أخبار السوق السعودي</b>\n━━━━━━━━━━━━━━━\n'
                for i, item in enumerate(tasi_items[:5], 1):
                    msg += f'  {i}. {item[:120]}\n'
                msg += '━━━━━━━━━━━━━━━\n'
            if fed_items:
                msg += '🇺🇸 <b>أخبار الفيدرالي الأمريكي</b>\n━━━━━━━━━━━━━━━\n'
                for i, item in enumerate(fed_items[:3], 1):
                    msg += f'  {i}. {item[:120]}\n'
                msg += '━━━━━━━━━━━━━━━\n'

            if major_items:
                msg += '🚨 <b>إعلان مهم من تداول!</b>\n━━━━━━━━━━━━━━━\n'
                for i, item in enumerate(major_items[:5], 1):
                    msg += f'  {i}. {item[:130]}\n'
                msg += '━━━━━━━━━━━━━━━\n'
            if msg:
                msg += f'⏰ <i>{now.strftime("%H:%M")} | {now.strftime("%Y/%m/%d")}</i>'
                send_telegram_message(msg)
                print(f'✅ Sent {len(new_items)} new items (earnings={len(earnings_items)}, tasi={len(tasi_items)}, fed={len(fed_items)}) at {now.strftime("%H:%M")}')

        # تنظيف الـ cache إذا كبر كثيراً (أكثر من 500 خبر)
        if len(sent_news_hashes) > 500:
            sent_news_hashes = set(list(sent_news_hashes)[-200:])

    except Exception as e:
        print(f'check_and_send_news error: {e}')


def send_morning_briefing():
    """إرسال ملخص صباحي قبل الجلسة"""
    try:
        now = datetime.now()
        # لا ترسل في عطلة نهاية الأسبوع (الجمعة=4، السبت=5)
        if now.weekday() in [4, 5]:
            return

        news = fetch_saudi_market_news()
        news_text = ''
        if news:
            for i, item in enumerate(news[:3], 1):
                news_text += f'  {i}. {item[:100]}\n'
        else:
            news_text = '  لا توجد أخبار متاحة حالياً\n'

        message = (
            f"🌅 <b>صباح الخير! ملخص السوق السعودي</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📅 <b>التاريخ:</b> {now.strftime('%Y/%m/%d')}\n"
            f"⏰ <b>الجلسة تبدأ الساعة:</b> 10:00 صباحاً\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📰 <b>أبرز الأخبار:</b>\n"
            f"{news_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 <b>مؤشر تاسي الأسبوع الماضي:</b> متابعة مستمرة\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>هذه المعلومات للأغراض التعليمية فقط</i>"
        )
        send_telegram_message(message)
    except Exception as e:
        print(f'Error in morning briefing: {e}')


def fetch_tasi_price():
    """جلب سعر تاسي الحقيقي من تداول السعودية"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get('https://www.saudiexchange.sa/wps/portal/saudiexchange/ourmarkets/main-market-watch?locale=ar',
                         headers=headers, timeout=15)
        import re
        text = r.text
        # البحث عن سعر تاسي (نمط: 10,xxx.xx)
        matches = re.findall(r'(1[0-9],\d{3}\.\d{2})', text)
        if matches:
            price = matches[0]
            # البحث عن التغيير والنسبة
            change_matches = re.findall(r'([+-]?\d{1,4}\.\d{2})\s*\(?\s*([+-]?\d{1,2}\.\d{2})\s*%?\s*\)?', text)
            for cm in change_matches:
                try:
                    val = float(cm[0])
                    pct = float(cm[1])
                    if 0 < abs(pct) < 10:  # نسبة منطقية
                        return price, cm[0], cm[1]
                except:
                    continue
            return price, None, None
    except Exception as e:
        print(f'Error fetching TASI price: {e}')
    return None, None, None


def send_closing_summary():
    """إرسال ملخص إغلاق السوق مع سعر تاسي الحقيقي"""
    try:
        now = datetime.now()
        # لا ترسل في عطلة نهاية الأسبوع
        if now.weekday() in [4, 5]:
            return

        # جلب سعر تاسي الحقيقي
        tasi_price, change_val, change_pct = fetch_tasi_price()

        if tasi_price:
            try:
                pct = float(change_pct) if change_pct else 0
                arrow = '📈' if pct >= 0 else '📉'
                color = '🟢' if pct >= 0 else '🔴'
                sign = '+' if pct >= 0 else ''
                tasi_line = f"{arrow} <b>تاسي:</b> {tasi_price} نقطة  {color} ({sign}{change_pct}%)"
            except:
                tasi_line = f"📊 <b>تاسي:</b> {tasi_price} نقطة"
        else:
            tasi_line = "📊 <b>تاسي:</b> تعذّر جلب البيانات"

        # جلب أبرز الأخبار
        news = fetch_saudi_market_news()
        news_text = ''
        if news:
            for i, item in enumerate(news[:3], 1):
                news_text += f'  {i}. {item[:100]}\n'
        else:
            news_text = '  لا توجد أخبار متاحة حالياً\n'

        # اليوم بالعربي
        days_ar = ['الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت','الأحد']
        day_name = days_ar[now.weekday()]

        message = (
            f"🔔 <b>ملخص إغلاق السوق السعودي</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>{day_name} {now.strftime('%d/%m/%Y')}</b>\n"
            f"⏰ <b>إغلاق الساعة:</b> 3:30 مساءً\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"{tasi_line}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📰 <b>أبرز أخبار اليوم:</b>\n"
            f"{news_text}"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <b>تابع إشاراتنا غداً إن شاء الله</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>هذه المعلومات للأغراض التعليمية فقط</i>"
        )
        send_telegram_message(message)
        print(f'✅ Closing summary sent: TASI={tasi_price}')
    except Exception as e:
        print(f'Error in closing summary: {e}')


# ══════════════════════════════════════════════════════════
# تشغيل الجدولة التلقائية
# ══════════════════════════════════════════════════════════
def keep_alive_ping():
    """Ping البوت نفسه كل 10 دقائق لمنع Render من النوم"""
    try:
        url = os.environ.get('RENDER_EXTERNAL_URL', 'https://tawsiya-bot.onrender.com')
        requests.get(f'{url}/', timeout=10)
        print(f'✅ Keep-Alive ping sent at {datetime.now().strftime("%H:%M")}')
    except Exception as e:
        print(f'Keep-Alive ping error: {e}')


def send_dividends_alert():
    """إرسال تنبيه الأسهم القريبة من توزيع الأرباح كل أحد"""
    try:
        from datetime import date
        import calendar
        today = date.today()
        # جلب توزيعات الأرباح من argaam
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ar,en;q=0.9'
        }
        dividends = []
        try:
            from bs4 import BeautifulSoup
            url = 'https://www.argaam.com/ar/company/calendar/details/marketid/3/home//'
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                # البحث عن أحداث توزيع الأرباح
                rows = soup.find_all('tr')
                for row in rows[:50]:
                    text = row.get_text(strip=True)
                    if 'أحقية' in text or 'توزيع' in text:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            dividends.append(cells[1].get_text(strip=True) if len(cells) > 1 else text[:80])
        except:
            pass

        now = datetime.now()
        week_start = today.strftime('%d/%m')

        if dividends:
            div_list = '\n'.join([f'• {d}' for d in dividends[:10]])
            msg = (
                f'U0001f4b0 <b>تنبيه توزيعات الأرباح - هذا الأسبوع</b>\n'
                f'━━━━━━━━━━━━━━━\n'
                f'{div_list}\n'
                f'━━━━━━━━━━━━━━━\n'
                f'⚠️ <i>لتستحق الأرباح اشترِ قبل يوم الأحقية</i>\n'
                f'⏰ {now.strftime("%H:%M")} | {now.strftime("%Y/%m/%d")}'
            )
        else:
            # رسالة ثابتة لو ما جبنا بيانات
            msg = (
                f'U0001f4b0 <b>تنبيه توزيعات الأرباح - أغسطس 2026</b>\n'
                f'━━━━━━━━━━━━━━━\n'
                f'U0001f525 <b>2282 نقي</b> - 1 ريال/سهم (أحقية 9 أغسطس)\n'
                f'U0001f525 <b>4260 بدجت السعودية</b> - 0.5 ريال/سهم (أحقية 13 أغسطس)\n'
                f'✅ <b>1050 بي اس اف</b> - صرف أرباح 11 أغسطس\n'
                f'✅ <b>4004 دله الصحية</b> - أحقية قريبة\n'
                f'✅ <b>4344 سدكو كابيتال ريت</b> - توزيع ربع سنوي\n'
                f'━━━━━━━━━━━━━━━\n'
                f'⚠️ <i>لتستحق الأرباح اشترِ قبل يوم الأحقية</i>\n'
                f'⏰ {now.strftime("%H:%M")} | {now.strftime("%Y/%m/%d")}'
            )
        send_telegram_message(msg)
        print(f'✅ Dividends alert sent at {now.strftime("%H:%M")}')
    except Exception as e:
        print(f'Dividends alert error: {e}')


def start_scheduler():
    if not SCHEDULER_AVAILABLE:
        print('APScheduler not available, skipping scheduler')
        return
    try:
        scheduler = BackgroundScheduler(timezone='Asia/Riyadh')
        # ملخص صباحي الساعة 9:00 صباحاً (الأحد-الخميس)
        scheduler.add_job(send_morning_briefing, 'cron', hour=9, minute=0, day_of_week='sun,mon,tue,wed,thu')
        # ملخص إغلاق الساعة 3:30 مساءً (الأحد-الخميس)
        scheduler.add_job(send_closing_summary, 'cron', hour=15, minute=30, day_of_week='sun,mon,tue,wed,thu')
        # ✅ مراقبة الأخبار كل 5 دقائق (أيام العمل 8ص-11م)
        scheduler.add_job(check_and_send_news, 'interval', minutes=5)
        # ✅ Keep-Alive: ping نفسه كل 10 دقائق لمنع Render من النوم
        scheduler.add_job(keep_alive_ping, 'interval', minutes=10)
        # ✅ توزيعات الأرباح: كل أحد الساعة 10:00 صباحاً
        scheduler.add_job(send_dividends_alert, 'cron', hour=10, minute=0, day_of_week='sun')
        scheduler.start()
        print('✅ Scheduler started: 9:00 AM & 3:30 PM daily + News every 5min + Keep-Alive every 10min + Dividends every Sunday 10AM')
    except Exception as e:
        print(f'Scheduler error: {e}')


@app.route('/news', methods=['GET'])
def send_news_now():
    """endpoint لإرسال آخر الأخبار يدوياً"""
    try:
        from datetime import datetime
        now = datetime.now()
        # جلب الأخبار
        articles = fetch_argaam_news()
        earnings = fetch_earnings_news()
        fed      = fetch_fed_news()

        msg = ''
        if earnings:
            msg += '📊 <b>نتائج مالية جديدة ✨</b>\n━━━━━━━━━━━━━━━\n'
            for i, a in enumerate(earnings[:5], 1):
                msg += f'  {i}. {a[:130]}\n'
            msg += '━━━━━━━━━━━━━━━\n'
        if articles:
            msg += '📢 <b>أخبار السوق السعودي</b>\n━━━━━━━━━━━━━━━\n'
            for i, a in enumerate(articles[:5], 1):
                msg += f'  {i}. {a[:120]}\n'
            msg += '━━━━━━━━━━━━━━━\n'
        if fed:
            msg += '🇺🇸 <b>أخبار الفيدرالي</b>\n━━━━━━━━━━━━━━━\n'
            for i, a in enumerate(fed[:3], 1):
                msg += f'  {i}. {a[:120]}\n'
            msg += '━━━━━━━━━━━━━━━\n'

        if not msg:
            msg = '📰 <b>لا توجد أخبار جديدة حالياً</b>\n'

        msg += f'⏰ <i>{now.strftime("%H:%M")} | {now.strftime("%Y/%m/%d")}</i>'
        send_telegram_message(msg)
        return jsonify({"status": "success", "message": "News sent!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/closing', methods=['GET'])
def send_closing_now():
    """مسار احتياطي لإرسال ملخص إغلاق تاسي يدوياً عند الحاجة"""
    try:
        send_closing_summary()
        return jsonify({"status": "success", "message": "Closing summary sent!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════
# نظام التوصيات النشطة - محفوظة في ملف JSON
# ══════════════════════════════════════════════════════════
import json
SIGNALS_FILE = '/tmp/active_signals.json'
MAX_ACTIVE_SIGNALS = 50  # نحفظ آخر 50 توصية

def load_active_signals():
    """تحميل التوصيات من الملف"""
    try:
        if os.path.exists(SIGNALS_FILE):
            with open(SIGNALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []

def save_active_signals(signals):
    """حفظ التوصيات في الملف"""
    try:
        with open(SIGNALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(signals, f, ensure_ascii=False, indent=2)
    except:
        pass

# تحميل التوصيات عند بدء التشغيل
active_signals = load_active_signals()

def add_active_signal(ticker, stock_name, price, sl, tp1, tp2, tp3, timeframe):
    """إضافة توصية جديدة للقائمة وحفظها"""
    global active_signals
    signal = {
        'ticker': ticker,
        'name': stock_name,
        'price': price,
        'sl': sl,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'time': timeframe,
        'date': datetime.now().strftime('%Y/%m/%d %H:%M')
    }
    active_signals.insert(0, signal)
    if len(active_signals) > MAX_ACTIVE_SIGNALS:
        active_signals.pop()
    save_active_signals(active_signals)

def format_active_signals_message():
    """تنسيق رسالة التوصيات النشطة"""
    if not active_signals:
        return None
    msg = '📋 <b>آخر التوصيات النشطة</b>\n━━━━━━━━━━━━━━━\n'
    for i, s in enumerate(active_signals, 1):
        msg += f"{i}. 🟢 <b>{s['name']} ({s['ticker']})</b>\n"
        msg += f"   💰 الدخول: <b>{format_num(s['price'])}</b> | 🛑 الوقف: <b>{format_num(s['sl'])}</b>\n"
        msg += f"   🎯 TP1: {format_num(s['tp1'])} | TP2: {format_num(s['tp2'])} | TP3: {format_num(s['tp3'])}\n"
        msg += f"   📅 {s['date']}\n\n"
    msg += '━━━━━━━━━━━━━━━\n'
    msg += '⚠️ <i>هذه التوصيات للأغراض التعليمية فقط</i>'
    return msg

@app.route('/telegram_update', methods=['POST'])
def telegram_update():
    """استقبال تحديثات تيليجرام لاستقبال الأعضاء الجدد"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'ok': True}), 200
        message = data.get('message', {})
        if not message:
            return jsonify({'ok': True}), 200
        new_members = message.get('new_chat_members', [])
        if new_members:
            signals_msg = format_active_signals_message()
            if signals_msg:
                welcome = ''
                for m in new_members:
                    name = m.get('first_name', 'عضو جديد')
                    welcome += f'👋 أهلاً <b>{name}</b> في مجموعة صائد الأسهم السعودية!\n'
                welcome += '\nإليك آخر التوصيات النشطة:\n\n'
                welcome += signals_msg
                send_telegram_message(welcome)
        return jsonify({'ok': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/active_signals', methods=['GET'])
def get_active_signals():
    """إرسال التوصيات النشطة للمجموعة"""
    msg = format_active_signals_message()
    if msg:
        send_telegram_message(msg)
        return jsonify({'status': 'success', 'count': len(active_signals)}), 200
    return jsonify({'status': 'no_signals', 'message': 'لا توجد توصيات نشطة حالياً'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    start_scheduler()
    app.run(host='0.0.0.0', port=port)
else:
    # تشغيل الجدولة عند بدء Gunicorn/Render
    start_scheduler()
