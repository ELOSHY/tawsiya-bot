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
    # ── البنوك ──
    "1010": "بنك الرياض",
    "1020": "بنك الجزيرة",
    "1030": "مصرف الراجحي",
    "1050": "البنك السعودي البريطاني",
    "1060": "البنك السعودي الفرنسي",
    "1080": "البنك العربي الوطني",
    "1120": "البنك الأهلي السعودي",
    "1140": "بنك البلاد",
    "1150": "مصرف الإنماء",
    "1180": "البنك الأهلي التجاري",
    "1182": "أملاك للتمويل",
    # ── الصناعة والتعدين ──
    "1201": "تكوين",
    "1202": "مبكو",
    "1210": "الصناعات الكيميائية الأساسية",
    "1211": "معادن",
    "1212": "مجموعة أسترا الصناعية",
    "1213": "نسيج",
    "1214": "شاكر",
    "1301": "مصانع الأسلاك المتحدة",
    "1302": "بوان",
    "1303": "الصناعات الكهربائية",
    "1304": "حديد اليمامة",
    "1320": "أنابيب السعودية للصلب",
    "1321": "الأنابيب المتكاملة للصناعة",
    "1322": "المسانة الكبرى للتعدين",
    # ── الاتصالات والتقنية ──
    "1810": "مجموعة سيرا القابضة",
    "1820": "مجموعة بان القابضة",
    "1830": "ليجام للرياضة",
    "1833": "الموارد للقوى البشرية",
    # ── البتروكيماويات والطاقة ──
    "2001": "الميثانول كيميكالز",
    "2010": "سابك",
    "2020": "سابك للمغذيات الزراعية",
    "2030": "مصافي السعودية",
    "2040": "السعودية للسيراميك",
    "2050": "مجموعة سافولا",
    "2060": "التصنيع الوطنية",
    "2070": "سبيميكو",
    "2080": "الغاز والتصنيع الوطنية",
    "2082": "أكوا باور",
    "2083": "شركة المياه والكهرباء للجبيل وينبع",
    "2090": "الجبس الوطنية",
    "2100": "وفرة للصناعة والتطوير",
    "2110": "الكابلات السعودية",
    "2120": "الصناعات السعودية المتقدمة",
    "2130": "الشركة السعودية للتطوير الصناعي",
    "2140": "عيان للاستثمار",
    "2150": "الشركة الوطنية لصناعة الزجاج",
    "2160": "الأمانت السعودية",
    "2170": "ألجين",
    "2180": "شركة التعبئة والتغليف",
    "2200": "أنابيب العربية",
    "2222": "أرامكو السعودية",
    "2223": "سابك للبتروكيماويات",
    "2270": "سدافكو",
    "2280": "يانساب",
    "2290": "سبكيم",
    "2300": "سيبكو",
    "2310": "المتقدمة",
    "2320": "كيان السعودية",
    "2330": "أرتكس",
    "2340": "وفرة",
    "2350": "كيان السعودية",
    "2360": "الخليج للبتروكيماويات",
    "2370": "مسك",
    "2380": "بترو رابغ",
    "2381": "الحفر العربية",
    "2382": "أديس",
    # ── الأسمنت ──
    "3002": "أسمنت نجران",
    "3003": "أسمنت المدينة",
    "3004": "أسمنت المنطقة الشمالية",
    "3005": "أسمنت أم القرى",
    "3007": "زهرة الواحة للتجارة",
    "3008": "الكثيري القابضة",
    "3010": "أسمنت العربية",
    "3020": "أسمنت اليمامة",
    "3030": "أسمنت السعودية",
    "3040": "أسمنت القصيم",
    "3050": "أسمنت الجنوب",
    "3060": "أسمنت ينبع",
    "3080": "أسمنت المنطقة الشرقية",
    "3090": "أسمنت تبوك",
    "3091": "أسمنت الجوف",
    "3092": "أسمنت الرياض",
    # ── الرعاية الصحية ──
    "4001": "أسواق عبدالله العثيم",
    "4002": "مواساة",
    "4003": "إكسترا",
    "4004": "دله الصحية",
    "4005": "رعاية",
    "4006": "أسواق المزرعة",
    "4007": "الحمادي القابضة",
    "4008": "ساكو",
    "4009": "المستشفى السعودي الألماني",
    "4011": "لازوردي",
    "4012": "ثوب الأصيل",
    "4013": "مجموعة سليمان الحبيب الطبية",
    "4014": "دار المعدات الطبية والعلمية",
    "4015": "جمجوم فارما",
    "4016": "أفالون فارما",
    "4017": "فقيه للرعاية الصحية",
    "4018": "الموسى الصحية",
    "4019": "الشركة الطبية المتخصصة",
    "4020": "الأكارية",
    "4021": "مركز كندا الطبي",
    # ── النقل والخدمات اللوجستية ──
    "4030": "بحري",
    "4031": "الخدمات الأرضية السعودية",
    "4040": "سابتكو",
    # ── التجزئة والخدمات ──
    "4050": "ساسكو",
    "4051": "بازيم",
    "4061": "أنعام القابضة",
    "4070": "التعليم والتدريب",
    "4071": "العربية للتعليم",
    "4072": "مجموعة MBC",
    "4080": "سناد القابضة",
    "4081": "نايفات للتمويل",
    "4082": "مرنا",
    "4083": "تسهيل",
    "4084": "ديراية للاستثمار",
    "4090": "طيبة",
    "4100": "شركة مكة للإنشاء والتعمير",
    "4110": "باتك للاستثمارات واللوجستيات",
    "4130": "درب السعودية",
    "4140": "سيكو القابضة",
    "4141": "العمران",
    "4142": "كابلات الرياض",
    "4143": "طلكو",
    "4144": "راووم",
    "4145": "الغاز والتصنيع الأهلية",
    "4146": "الغاز",
    "4147": "الغاز والتصنيع المركزية",
    "4148": "الوسائل الصناعية",
    "4150": "أردكو",
    "4160": "ثمار",
    "4161": "بن داود",
    "4162": "المنجم",
    "4163": "الدواء",
    "4164": "نهدي",
    "4165": "المجد للعود",
    "4170": "تيكو",
    "4180": "مجموعة فتيحي",
    "4190": "جرير",
    "4191": "أبو موتي",
    "4192": "معارض السيف",
    "4193": "نايس ون",
    "4194": "بيلد ستيشن",
    "4200": "الدريس",
    "4210": "مجموعة روشن",
    "4220": "إعمار المدينة الاقتصادية",
    "4230": "البحر الأحمر الدولية",
    "4240": "سينومي للتجزئة",
    "4250": "جبل عمر",
    "4260": "بدجت السعودية",
    "4261": "ذيب",
    "4262": "لومي",
    "4263": "سال",
    "4264": "فلاي ناس",
    "4265": "شيري",
    "4270": "الخطوط السعودية للخدمات الأرضية",
    "4280": "المملكة القابضة",
    "4290": "الخليج للتدريب والتعليم",
    "4291": "الشركة الوطنية للتعلم الإلكتروني",
    "4292": "عطاء",
    "4300": "دار الأركان",
    "4310": "الكيميائية السعودية",
    "4320": "الأندلس العقارية",
    "4321": "سينومي سنترز",
    "4322": "ريتال",
    "4323": "سمو",
    "4324": "بنان",
    "4325": "مسار",
    "4326": "المجيدية",
    "4327": "الرمز",
    # ── صناديق الاستثمار العقاري (ريت) ──
    "4330": "صندوق الرياض ريت",
    "4331": "صندوق الجزيرة ريت",
    "4332": "صندوق جدوى ريت الحرمين",
    "4333": "صندوق تعليم ريت",
    "4334": "صندوق المآثر ريت",
    "4335": "صندوق مشاركة ريت",
    "4336": "صندوق ملكية ريت",
    "4337": "صندوق العزيزية ريت",
    "4338": "صندوق الأهلي ريت 1",
    "4339": "صندوق ديراية ريت",
    "4340": "صندوق الراجحي ريت",
    "4342": "صندوق جدوى ريت السعودية",
    "4344": "صندوق سيدكو ريت",
    "4345": "صندوق الإنماء ريت للتجزئة",
    "4346": "صندوق ميفك ريت",
    "4347": "صندوق بنيان ريت",
    "4348": "صندوق الخبير ريت",
    "4349": "صندوق الإنماء ريت للضيافة",
    "4350": "صندوق الاستثمار ريت",
    "4700": "الخبير للدخل",
    "4702": "الخبير للدخل 2030",
    "4703": "سيدكو متعدد الأصول",
    # ── الطاقة ──
    "5110": "الطاقة السعودية",
    # ── الغذاء والزراعة ──
    "6001": "HB",
    "6002": "هرفي فودز",
    "6004": "كاتريون",
    "6010": "نادك",
    "6012": "ريدان",
    "6013": "DWF",
    "6014": "الأمار",
    "6015": "أمريكانا",
    "6016": "برجر إيزر",
    "6017": "جاهز",
    "6018": "الأندية الرياضية",
    "6019": "المسار الشامل",
    "6020": "جاكو",
    "6040": "تادكو",
    "6050": "سفيكو",
    "6060": "الشرقية للتنمية",
    "6070": "الجوف",
    "6090": "جازدكو",
    # ── الاتصالات ──
    "7010": "الاتصالات السعودية",
    "7020": "موبايلي",
    "7030": "زين السعودية",
    "7040": "قو للاتصالات",
    "7200": "مباشر للإنترنت",
    "7201": "البحر العربي",
    "7202": "سلوشنز",
    "7203": "علم",
    "7204": "2P",
    "7205": "DBS",
    "7211": "أزم",
    # ── التأمين ──
    "8010": "التعاونية",
    "8012": "تكافل الجزيرة",
    "8020": "ملاذ للتأمين",
    "8030": "ميدغلف",
    "8040": "متكاملة",
    "8050": "سلامة",
    "8060": "ولاء",
    "8070": "الدرع العربي",
    "8100": "سايكو",
    "8120": "الخليجية الأهلية",
    "8150": "أسيج",
    "8160": "التأمين الإسلامي",
    "8170": "الاتحاد للتأمين",
    "8180": "الصقر للتأمين",
    "8190": "الاتحاد التجاري",
    "8200": "إعادة التأمين السعودية",
    "8210": "بوبا العربية",
    "8230": "الراجحي للتكافل",
    "8240": "تشب",
    "8250": "جيج",
    "8260": "الخليج العام",
    "8280": "ليفا",
    "8300": "وطنية",
    "8310": "أمانة للتأمين",
    "8311": "عناية",
    "8313": "راسن",
    # ── صناديق ريت إضافية ──
    "9300": "صندوق الواحة ريت",
    # ── السوق الموازي (نمو) ──
    "9510": "NBM",
    "9513": "حديد وطني",
    "9514": "النقول",
    "9515": "فيش فاش",
    "9516": "NGDC",
    "9517": "موبي الصناعية",
    "9521": "إنمار",
    "9522": "الحاسوب",
    "9523": "مجموعة الخمس",
    "9524": "أيكتك",
    "9527": "AME",
    "9530": "الطبية",
    "9532": "حلوى",
    "9533": "SPC",
    "9535": "لدن",
    "9536": "فاديكو",
    "9537": "أمواج الدولية",
    "9538": "نسيج تك",
    "9539": "أقاسيم",
    "9540": "تدوير",
    "9541": "أكاديمية التعلم",
    "9542": "كير",
    "9543": "نتووركرز",
    "9544": "فيوتشر كير",
    "9545": "الدولية",
    "9546": "نبأ الصحة",
    "9547": "رواسي",
    "9548": "أبيكو",
    "9549": "البابطين للأغذية",
    "9550": "شور",
    "9551": "برج المعرفة",
    "9552": "سعودي توب",
    "9553": "مولان",
    "9555": "لين الخير",
    "9557": "إدارة",
    "9558": "القلم",
    "9559": "بلدي",
    "9560": "واجا",
    "9561": "نولدج نت",
    "9562": "بوابة الغذاء",
    "9563": "بينا",
    "9564": "هورايزون للأغذية",
    "9565": "ميار",
    "9566": "لايم الصناعات",
    "9567": "غذاء السلطان",
    "9568": "مايار",
    "9569": "المنيف",
    "9570": "تام للتطوير",
    "9571": "منولا",
    "9572": "الرازي",
    "9574": "برو ميدكس",
    "9575": "تصميم الرخام",
    "9576": "بيبر هوم",
    "9577": "دار المركبة",
    "9578": "أطلس للمصاعد",
    "9579": "ريماث",
    "9580": "الرشيد الصناعية",
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
    "9593": "بان خليج",
    "9594": "الأدوات",
    "9595": "WSM",
    "9596": "قوارة",
    "9597": "ليف",
    "9598": "المحافظة للتعليم",
    "9599": "طاقات",
    "9600": "قومل",
    "9601": "الرشيد",
    "9602": "يقين",
    "9603": "هورايزون التعليمية",
    "9604": "ميرال",
    "9605": "نفط الشرق",
    "9606": "ثروة",
    "9607": "ASG",
    "9608": "الأشغال الميسرة",
    "9609": "ناس للبترول",
    "9610": "الأفنيو الأول",
    "9611": "UFG",
    "9612": "سما للمياه",
    "9613": "شلفا",
    "9614": "نقاء",
    "9615": "مفيد",
    "9616": "جنى",
    "9617": "أرابيكا ستار",
    "9618": "الفاخرة",
    "9619": "متعدد الأعمال",
    "9620": "بلسم الطبية",
    "9621": "DRC",
    "9622": "SMC",
    "9623": "مصنع البطال",
    "9624": "الشهيلي للمعادن",
    "9625": "إتمام",
    "9626": "سمايل كير",
    "9627": "TMC",
    "9628": "لمسات",
    "9630": "راشيو",
    "9631": "HKC",
    "9632": "رؤية المستقبل",
    "9633": "معدات الخدمات",
    "9634": "أدير",
    "9635": "دخون",
    "9636": "الكزامة",
    "9637": "حلول أكسيليريتد",
    "9639": "أنمات",
    "9640": "أساس مكين",
    "9641": "هوية",
    "9642": "تايم",
    "9644": "ناف",
    "9645": "عالم الإشارات",
    "9647": "وجد لايف",
    "9648": "حمد بن سعيدان العقارية",
    "9649": "جمجوم فاشن",
    "9650": "ساحة المجد",
    "9651": "التويجري",
    "9653": "KDL",
    "9655": "MSGA",
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

            price     = safe_float(data.get('price'))
            stop_loss = safe_float(data.get('sl') or data.get('stop_loss') or data.get('plot_0'))
            target_1  = safe_float(data.get('tp1') or data.get('target_1') or data.get('plot_1'))
            target_2  = safe_float(data.get('tp2') or data.get('target_2') or data.get('plot_2'))
            target_3  = safe_float(data.get('tp3') or data.get('target_3') or data.get('plot_3'))

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

        # إرسال الأخبار الجديدة
        if new_items:
            tasi_items     = [t for cat, t in new_items if cat == 'tasi']
            earnings_items = [t for cat, t in new_items if cat == 'earnings']
            fed_items      = [t for cat, t in new_items if cat == 'fed']

            msg = ''
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


def send_closing_summary():
    """إرسال ملخص إغلاق السوق"""
    try:
        now = datetime.now()
        # لا ترسل في عطلة نهاية الأسبوع
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
            f"🔔 <b>ملخص إغلاق السوق السعودي</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📅 <b>التاريخ:</b> {now.strftime('%Y/%m/%d')}\n"
            f"⏰ <b>وقت الإغلاق:</b> 3:30 مساءً\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📰 <b>أبرز أخبار اليوم:</b>\n"
            f"{news_text}"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 <b>تابع إشاراتنا غداً إن شاء الله</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ <i>هذه المعلومات للأغراض التعليمية فقط</i>"
        )
        send_telegram_message(message)
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


def start_scheduler():
    if not SCHEDULER_AVAILABLE:
        print('APScheduler not available, skipping scheduler')
        return
    try:
        scheduler = BackgroundScheduler(timezone='Asia/Riyadh')
        # ملخص صباحي الساعة 9:00 صباحاً (الأحد-الخميس)
        scheduler.add_job(send_morning_briefing, 'cron', hour=9, minute=0, day_of_week='sun-thu')
        # ملخص إغلاق الساعة 3:30 مساءً (الأحد-الخميس)
        scheduler.add_job(send_closing_summary, 'cron', hour=15, minute=30, day_of_week='sun-thu')
        # ✅ مراقبة الأخبار كل 5 دقائق (أيام العمل 8ص-11م)
        scheduler.add_job(check_and_send_news, 'interval', minutes=5)
        # ✅ Keep-Alive: ping نفسه كل 10 دقائق لمنع Render من النوم
        scheduler.add_job(keep_alive_ping, 'interval', minutes=10)
        scheduler.start()
        print('✅ Scheduler started: 9:00 AM & 3:30 PM daily + News every 5min + Keep-Alive every 10min')
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    start_scheduler()
    app.run(host='0.0.0.0', port=port)
else:
    # تشغيل الجدولة عند بدء Gunicorn/Render
    start_scheduler()
