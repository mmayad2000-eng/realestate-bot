import os
from dotenv import load_dotenv

load_dotenv()

# ===== إعدادات فيسبوك =====
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN", "")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "tanta_real_estate_2026")
FB_APP_SECRET = os.getenv("FB_APP_SECRET", "")

# ===== إعدادات واتساب (360dialog) =====
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")
WHATSAPP_API_URL = "https://waba.360dialog.io/v1"
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")

# ===== الموظفين الحقيقيين (رقم واتساب بالصيغة الدولية) =====
# أضف أرقام الموظفين هنا — البوت هيوزع عليهم بالتناوب
AGENTS = [
    {"name": "أحمد", "whatsapp": "201XXXXXXXXX"},
    {"name": "سارة",  "whatsapp": "201XXXXXXXXX"},
    {"name": "محمود", "whatsapp": "201XXXXXXXXX"},
]

# ===== إعدادات البوت =====
BOT_NAME = "سلمى"
COMPANY_NAME = "شركتنا للعقارات"
CITY = "طنطا"

# ===== مسار حفظ بيانات العملاء =====
LEADS_FILE = os.path.join(os.getenv("TMPDIR", "/tmp"), "leads.json")

# ===== إعدادات الخادم =====
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
