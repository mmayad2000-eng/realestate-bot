"""
الخادم الرئيسي — Flask Webhook
يستقبل من: Facebook Messenger + WhatsApp (360dialog) + Facebook Comments
"""
import hashlib
import hmac
import json
import logging

from flask import Flask, request, jsonify, abort

import config
from bot.handler import handle_message
from bot.conversation import MSG_COMMENT_REPLY, TRIGGER_KEYWORDS
from bot import messenger, whatsapp

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)


# ============================================================
# ١. Facebook Messenger Webhook
# ============================================================

@app.route("/webhook/facebook", methods=["GET"])
def fb_verify():
    """التحقق من الـ Webhook عند الربط الأول"""
    mode  = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == config.FB_VERIFY_TOKEN:
        logger.info("Facebook webhook verified ✓")
        return challenge, 200
    abort(403)


@app.route("/webhook/facebook", methods=["POST"])
def fb_webhook():
    """استقبال رسائل ماسنجر والتعليقات"""
    # التحقق من التوقيع
    sig = request.headers.get("X-Hub-Signature-256", "")
    if config.FB_APP_SECRET:
        expected = "sha256=" + hmac.new(
            config.FB_APP_SECRET.encode(),
            request.data,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            logger.warning("Invalid signature from Facebook")
            abort(403)

    data = request.get_json(silent=True) or {}
    object_type = data.get("object")

    if object_type == "page":
        for entry in data.get("entry", []):
            # ===== رسائل ماسنجر =====
            for msg_event in entry.get("messaging", []):
                sender_id = msg_event.get("sender", {}).get("id")
                if not sender_id:
                    continue
                # تجاهل الأحداث التي ليست رسائل نصية
                msg = msg_event.get("message", {})
                text = msg.get("text", "").strip()
                if not text:
                    continue
                logger.info(f"[Messenger] {sender_id}: {text[:60]}")
                handle_message(sender_id, text, channel="messenger",
                               send_fn=messenger.send_message)

            # ===== تعليقات الصفحة =====
            for change in entry.get("changes", []):
                value = change.get("value", {})
                if change.get("field") != "feed":
                    continue
                item = value.get("item")
                verb = value.get("verb")
                if item == "comment" and verb == "add":
                    comment_id    = value.get("comment_id")
                    commenter_id  = value.get("sender_id") or value.get("from", {}).get("id")
                    comment_text  = value.get("message", "")
                    
                    if any(kw in comment_text.lower() for kw in TRIGGER_KEYWORDS):
                        logger.info(f"[Comment] Keyword detected from {commenter_id}")
                        # رد على التعليق
                        messenger.reply_to_comment(comment_id, MSG_COMMENT_REPLY)
                        # ابعت رسالة خاصة
                        if commenter_id:
                            handle_message(commenter_id, comment_text,
                                           channel="fb_comment",
                                           send_fn=messenger.send_message)

    return jsonify({"status": "ok"}), 200


# ============================================================
# ٢. WhatsApp Webhook (360dialog)
# ============================================================

@app.route("/webhook/whatsapp", methods=["GET"])
def wa_verify():
    """التحقق من الـ Webhook"""
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == config.FB_VERIFY_TOKEN:
        return challenge, 200
    # 360dialog يستخدم نمط مختلف أحياناً
    return "OK", 200


@app.route("/webhook/whatsapp", methods=["POST"])
def wa_webhook():
    """استقبال رسائل واتساب"""
    data = request.get_json(silent=True) or {}
    messages = whatsapp.parse_incoming_webhook(data)

    for msg in messages:
        user_id = msg["from"]
        text    = msg["body"].strip()
        if not text or msg["type"] != "text":
            continue
        logger.info(f"[WhatsApp] {user_id}: {text[:60]}")
        handle_message(user_id, text, channel="whatsapp",
                       send_fn=whatsapp.send_message)

    return jsonify({"status": "ok"}), 200


# ============================================================
# ٣. لوحة تحكم العملاء (بسيطة)
# ============================================================

@app.route("/leads", methods=["GET"])
def view_leads():
    """اعرض كل العملاء"""
    from bot.leads import get_all_leads
    leads = get_all_leads()
    # ترتيب من الأحدث للأقدم
    leads.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    html = """<html dir="rtl">
<head><meta charset="utf-8">
<title>عملاء البوت</title>
<style>
  body { font-family: Arial; padding: 20px; background: #f5f5f5; }
  h1 { color: #1F4E79; }
  table { border-collapse: collapse; width: 100%; background: white; }
  th { background: #1F4E79; color: white; padding: 10px; }
  td { border: 1px solid #ddd; padding: 8px; }
  tr:nth-child(even) { background: #f0f6ff; }
  .new { color: #c55a11; font-weight: bold; }
  .contacted { color: #1d6b2f; }
</style>
</head>
<body>
<h1>عملاء البوت</h1>
<p>إجمالي: """ + str(len(leads)) + """ عميل</p>
<table>
<tr>
  <th>#</th><th>القناة</th><th>النوع</th><th>الميزانية</th>
  <th>المنطقة</th><th>المساحة</th><th>الموظف</th><th>الحالة</th><th>الوقت</th>
</tr>"""
    
    for i, lead in enumerate(leads, 1):
        agent = lead.get("assigned_agent", {})
        agent_name = agent.get("name", "—") if isinstance(agent, dict) else "—"
        status_class = "new" if lead.get("status") == "new" else "contacted"
        html += f"""<tr>
  <td>{i}</td>
  <td>{lead.get('channel','—')}</td>
  <td>{lead.get('type','—')}</td>
  <td>{lead.get('budget','—')}</td>
  <td>{lead.get('area','—')}</td>
  <td>{lead.get('size','—')}</td>
  <td>{agent_name}</td>
  <td class="{status_class}">{lead.get('status','—')}</td>
  <td>{lead.get('timestamp','—')[:16]}</td>
</tr>"""
    
    html += "</table></body></html>"
    return html


# ============================================================
# ٤. Health Check
# ============================================================

@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "bot": config.BOT_NAME,
        "city": config.CITY,
        "channels": ["messenger", "whatsapp", "fb_comments"],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)


# ============================================================
# ٥. مراقبة تعليقات الصفحة (Cron Job)
# ============================================================

@app.route("/cron/page", methods=["GET", "POST"])
def cron_scan_page():
    """يُستدعى كل ساعة لفحص تعليقات جديدة على الصفحة"""
    from bot.page_monitor import scan_page_comments
    result = scan_page_comments()
    logger.info(f"[Cron] Page scan result: {result}")
    return jsonify(result), 200


@app.route("/setup/subscribe", methods=["GET"])
def setup_subscribe():
    """اشترك في أحداث الصفحة — نفّذه مرة واحدة فقط"""
    from bot.page_monitor import subscribe_page_to_webhooks
    result = subscribe_page_to_webhooks()
    return jsonify(result), 200


# ============================================================
# ٦. عملاء الجروبات
# ============================================================

@app.route("/leads/groups", methods=["GET"])
def view_group_leads():
    """اعرض عملاء الجروبات"""
    from bot.group_leads import get_all_group_leads, format_group_leads_html
    leads = get_all_group_leads()
    leads.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return format_group_leads_html(leads)


@app.route("/leads/groups/add", methods=["POST"])
def add_group_lead():
    """
    أضف عميل من جروب يدوياً أو من سكريبت خارجي
    JSON: { name, phone, post_text, source }
    """
    data = request.get_json(silent=True) or {}
    from bot.group_leads import process_post
    result = process_post(
        post_text=data.get("post_text", ""),
        author_name=data.get("name", "غير معروف"),
        source_group=data.get("source", "جروب"),
    )
    return jsonify(result), 200


# ============================================================
# ٧. صفحة سياسة الخصوصية (مطلوبة لـ Facebook App)
# ============================================================

@app.route("/privacy", methods=["GET"])
def privacy_policy():
    """سياسة الخصوصية — مطلوبة لإعداد تطبيق الفيسبوك"""
    html = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>سياسة الخصوصية — E-Solution</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto;
           padding: 0 20px; line-height: 1.8; color: #333; background: #f9f9f9; }
    h1 { color: #1F4E79; border-bottom: 2px solid #1F4E79; padding-bottom: 10px; }
    h2 { color: #2E75B6; margin-top: 30px; }
    .logo { font-size: 24px; font-weight: bold; color: #1F4E79; }
    .date { color: #888; font-size: 14px; }
    footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #ddd;
             color: #888; font-size: 13px; }
  </style>
</head>
<body>
  <div class="logo">E-Solution للتطوير العقاري</div>
  <h1>سياسة الخصوصية</h1>
  <p class="date">آخر تحديث: مايو 2026</p>

  <h2>١. مقدمة</h2>
  <p>
    نحن في <strong>E-Solution للتطوير العقاري</strong> نحترم خصوصيتك ونلتزم بحماية بياناتك الشخصية.
    تشرح هذه السياسة كيفية جمع بياناتك واستخدامها عند تفاعلك مع البوت الآلي "سلمى" على فيسبوك ماسنجر.
  </p>

  <h2>٢. البيانات التي نجمعها</h2>
  <p>عند تفاعلك مع البوت، قد نجمع:</p>
  <ul>
    <li>اسمك كما يظهر على حسابك في فيسبوك</li>
    <li>رقم هاتفك (اختياري — فقط إذا قدّمته طوعاً)</li>
    <li>متطلباتك العقارية (النوع، الميزانية، المنطقة، المساحة)</li>
    <li>تاريخ ووقت التفاعل</li>
  </ul>

  <h2>٣. كيف نستخدم بياناتك</h2>
  <ul>
    <li>التواصل معك بخصوص العروض العقارية المناسبة</li>
    <li>توجيه طلبك لأحد مسؤولي المبيعات المختصين</li>
    <li>تحسين خدماتنا وتجربة التواصل</li>
  </ul>

  <h2>٤. مشاركة البيانات</h2>
  <p>
    لا نبيع بياناتك ولا نشاركها مع أطراف خارجية بغرض تجاري.
    يتم مشاركة بياناتك فقط مع فريق المبيعات الداخلي في E-Solution لأغراض المتابعة.
  </p>

  <h2>٥. الاحتفاظ بالبيانات</h2>
  <p>
    نحتفظ ببياناتك لمدة لا تتجاوز 12 شهراً من آخر تفاعل، ثم يتم حذفها تلقائياً.
  </p>

  <h2>٦. حقوقك</h2>
  <p>يحق لك في أي وقت:</p>
  <ul>
    <li>طلب الاطلاع على بياناتك المحفوظة</li>
    <li>طلب تصحيح أو حذف بياناتك</li>
    <li>إيقاف تلقّي الرسائل بإرسال كلمة "إيقاف"</li>
  </ul>

  <h2>٧. التواصل معنا</h2>
  <p>
    للاستفسار عن سياسة الخصوصية أو ممارسة حقوقك، تواصل معنا عبر:<br>
    <strong>E-Solution للتطوير العقاري — طنطا، مصر</strong>
  </p>

  <footer>
    © 2026 E-Solution للتطوير العقاري. جميع الحقوق محفوظة.
  </footer>
</body>
</html>"""
    return html, 200, {"Content-Type": "text/html; charset=utf-8"}
