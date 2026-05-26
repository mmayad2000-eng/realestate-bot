"""
جامع عملاء الجروبات — يحلل بوستات مجموعات الفيسبوك
E-Solution | طنطا

الاستخدام:
- يُستدعى يدوياً أو من سكريبت خارجي
- يحفظ العملاء في ملف CSV وفي نظام lead_store
"""
import re
import csv
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# مسار ملف العملاء من الجروبات
GROUPS_LEADS_FILE = "/tmp/group_leads.csv"

# الجروبات المستهدفة في طنطا
TARGET_GROUPS = [
    "https://www.facebook.com/groups/tantagharbiya",
    "https://www.facebook.com/groups/عقارات.طنطا",
    "https://www.facebook.com/groups/tanta.realestate",
    "https://www.facebook.com/groups/shaqaq.tanta",
    "https://www.facebook.com/groups/gharbiarealestate",
]

# كلمات دالة على البحث عن شقة
SEARCH_KEYWORDS = [
    "محتاج شقة", "عايز شقة", "عاوز شقة", "بدور على شقة",
    "شقة للإيجار", "شقة للايجار", "شقة للبيع", "شقة للتمليك",
    "شقة في طنطا", "شقق طنطا", "محتاج شقه", "عايز شقه",
    "باحث عن شقة", "شقة مفروشة", "ايجار", "للايجار",
    "فين أجيب شقة", "محتاج سكن", "ايجار سنوي",
]

# تعبير منتظم للتليفونات المصرية
PHONE_REGEX = re.compile(
    r'(?:(?:\+?2)?0)?'           # prefix
    r'(1[0125]\d{8})',           # 11-digit Egyptian mobile
)


def extract_phones(text: str) -> list:
    """استخلص أرقام التليفون من نص"""
    phones = []
    for match in PHONE_REGEX.finditer(text):
        num = "0" + match.group(1)  # مثل 01012345678
        if num not in phones:
            phones.append(num)
    return phones


def is_relevant_post(text: str) -> bool:
    """هل البوست عن البحث عن شقة؟"""
    t = text.lower()
    return any(kw in t for kw in SEARCH_KEYWORDS)


def save_group_lead(name: str, phone: str, post_text: str, source: str):
    """احفظ عميل من جروب"""
    lead = {
        "name": name,
        "phone": phone,
        "source": source,
        "post_preview": post_text[:100],
        "timestamp": datetime.now().isoformat(),
        "status": "new",
    }

    # احفظ في CSV
    file_exists = os.path.exists(GROUPS_LEADS_FILE)
    with open(GROUPS_LEADS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=lead.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(lead)

    logger.info(f"[GroupLeads] Saved lead: {name} | {phone} | {source}")
    return lead


def get_all_group_leads() -> list:
    """اجلب كل عملاء الجروبات"""
    if not os.path.exists(GROUPS_LEADS_FILE):
        return []
    leads = []
    with open(GROUPS_LEADS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        leads = list(reader)
    return leads


def process_post(post_text: str, author_name: str, source_group: str) -> dict:
    """
    عالج بوست من جروب:
    1. هل هو طلب شقة؟
    2. هل فيه رقم تليفون؟
    3. احفظ العميل
    """
    result = {"relevant": False, "phones": [], "saved": False}

    if not is_relevant_post(post_text):
        return result

    result["relevant"] = True
    phones = extract_phones(post_text)
    result["phones"] = phones

    if phones:
        for phone in phones:
            save_group_lead(
                name=author_name,
                phone=phone,
                post_text=post_text,
                source=source_group,
            )
        result["saved"] = True

    return result


def format_group_leads_html(leads: list) -> str:
    """HTML جميل لعرض عملاء الجروبات"""
    html = """<html dir="rtl">
<head><meta charset="utf-8"><title>عملاء الجروبات</title>
<style>
  body { font-family: Arial; padding: 20px; background: #f0fff0; }
  h1 { color: #1a5c1a; }
  table { border-collapse: collapse; width: 100%; background: white; }
  th { background: #1a5c1a; color: white; padding: 10px; }
  td { border: 1px solid #ccc; padding: 8px; }
  tr:nth-child(even) { background: #f0fff0; }
  .phone { font-weight: bold; color: #1a5c1a; font-size: 1.1em; }
  .wa-link { display: inline-block; background: #25d366; color: white;
             padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 0.9em; }
</style></head>
<body>
<h1>🏘 عملاء الجروبات</h1>
<p>إجمالي: """ + str(len(leads)) + """ عميل</p>
<table>
<tr><th>#</th><th>الاسم</th><th>التليفون</th><th>المصدر</th><th>البوست</th><th>الوقت</th><th>تواصل</th></tr>"""

    for i, lead in enumerate(leads, 1):
        phone = lead.get("phone", "")
        wa_num = phone.replace("0", "20", 1) if phone.startswith("0") else phone
        wa_link = f"https://wa.me/{wa_num}" if wa_num else "#"
        html += f"""<tr>
  <td>{i}</td>
  <td>{lead.get('name','—')}</td>
  <td class="phone">{phone}</td>
  <td>{lead.get('source','—')[:30]}</td>
  <td>{lead.get('post_preview','—')[:60]}...</td>
  <td>{lead.get('timestamp','—')[:16]}</td>
  <td><a class="wa-link" href="{wa_link}" target="_blank">📱 واتساب</a></td>
</tr>"""

    html += "</table></body></html>"
    return html
