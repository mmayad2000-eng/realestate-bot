#!/bin/bash
# ===== سكريبت التشغيل السريع =====
echo "🚀 تثبيت المتطلبات..."
pip install -r requirements.txt

echo ""
echo "✅ تم! الخطوات التالية:"
echo ""
echo "1. انسخ ملف الإعدادات:"
echo "   cp .env.example .env"
echo ""
echo "2. افتح ملف .env وأضف:"
echo "   - FB_PAGE_ACCESS_TOKEN"
echo "   - WHATSAPP_API_KEY"
echo "   - أرقام الموظفين في config.py"
echo ""
echo "3. شغّل الخادم:"
echo "   python app.py"
echo ""
echo "4. للنشر على الإنترنت (Heroku/Render):"
echo "   git init && git add . && git commit -m 'first commit'"
echo "   heroku create && git push heroku main"
