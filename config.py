import os
from dotenv import load_dotenv

load_dotenv()

# ===== إعدادات فيسبوك =====
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "tanta_real_estate_2026")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")

# ===== إعدادات واتساب (360dialog أو Cloud API) =====
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")
WHATSAPP_API_URL = "https://waba.360dialog.io/v1"
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

# ===== موظفي المبيعات — توزيع بالتناوب (Round-Robin) =====
# ⚠️ أضف أرقام الواتساب الحقيقية هنا (بالصيغة الدولية: 201XXXXXXXXX)
AGENTS = [
    {"name": "مسئول المبيعات ١", "whatsapp": os.getenv("AGENT1_WHATSAPP", "201XXXXXXXXX")},
    {"name": "مسئول المبيعات ٢", "whatsapp": os.getenv("AGENT2_WHATSAPP", "201XXXXXXXXX")},
    {"name": "مسئول المبيعات ٣", "whatsapp": os.getenv("AGENT3_WHATSAPP", "201XXXXXXXXX")},
]

# ===== إعدادات البوت =====
BOT_NAME = "سلمى"
COMPANY_NAME = "E-Solution"
CITY = "طنطا"

# ===== مسار حفظ بيانات العملاء =====
LEADS_FILE = os.path.join(os.getenv("TMPDIR", "/tmp"), "leads.json")

# ===== إعدادات الخادم =====
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
