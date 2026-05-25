# بوت العقارات — طنطا 🏠
## فيسبوك ماسنجر + واتساب + تعليقات فيسبوك

---

## الخطوات خطوة بخطوة

### الخطوة ١ — تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### الخطوة ٢ — إعداد ملف البيئة
```bash
cp .env.example .env
```
افتح `.env` وأضف:
- `FB_PAGE_ACCESS_TOKEN` من Meta Developer Console
- `FB_APP_SECRET` من Meta Developer Console
- `WHATSAPP_API_KEY` من 360dialog

### الخطوة ٣ — أضف أرقام الموظفين
افتح `config.py` وعدّل قائمة `AGENTS`:
```python
AGENTS = [
    {"name": "أحمد",  "whatsapp": "201001234567"},
    {"name": "سارة",  "whatsapp": "201001234568"},
]
```

### الخطوة ٤ — شغّل الخادم محلياً
```bash
python app.py
```

### الخطوة ٥ — انشر على الإنترنت (Render — مجاناً)
1. افتح render.com وأنشئ حساب
2. New Web Service > ارفع الكود من GitHub
3. أضف Environment Variables من `.env`
4. الرابط اللي هتاخده هو رابط الـ Webhook

---

## ربط فيسبوك

1. افتح developers.facebook.com
2. أنشئ App جديد > Business
3. أضف "Messenger" و "Webhooks"
4. في Webhooks حدد:
   - Callback URL: `https://رابطك.com/webhook/facebook`
   - Verify Token: `tanta_real_estate_2026`
   - اشترك في: `messages`, `messaging_postbacks`, `feed`
5. انسخ الـ Page Access Token وحطه في `.env`

---

## ربط واتساب (360dialog)

1. سجّل على app.360dialog.com
2. أنشئ Channel جديد
3. في Webhooks حدد:
   - URL: `https://رابطك.com/webhook/whatsapp`
4. انسخ الـ API Key وحطه في `.env`

---

## لوحة عرض العملاء

افتح المتصفح على: `https://رابطك.com/leads`

---

## هيكل الملفات

```
realestate-bot/
├── app.py              ← الخادم الرئيسي
├── config.py           ← الإعدادات والموظفين
├── requirements.txt    ← المتطلبات
├── .env.example        ← نموذج متغيرات البيئة
├── leads.json          ← بيانات العملاء (تلقائي)
├── Procfile            ← للنشر على Heroku/Render
└── bot/
    ├── conversation.py ← الرسائل وكلمات التشغيل
    ├── handler.py      ← منطق المحادثة
    ├── messenger.py    ← Facebook API
    ├── whatsapp.py     ← WhatsApp API
    └── leads.py        ← حفظ بيانات العملاء
```
