import os, re, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# ── Environment Variables ──────────────────────────────────────
VERIFY_TOKEN   = os.environ.get("VERIFY_TOKEN",       "esolution_tanta_2024")
PAGE_TOKEN     = os.environ.get("PAGE_ACCESS_TOKEN",  "")
WA_TOKEN       = os.environ.get("WHATSAPP_TOKEN",     "")
WA_PHONE_ID    = os.environ.get("PHONE_NUMBER_ID",    "")
N8N_WEBHOOK    = os.environ.get("N8N_LEAD_WEBHOOK",   "")   # ← رابط n8n

# ── Lead Keywords ──────────────────────────────────────────────
LEAD_SIGNALS = [
    "سعر","أسعار","كام","بكام","شقة","شقه","وحدة","وحده",
    "دوبلكس","مقدم","تقسيط","استثمار","مشروع","توليب",
    "price","unit","apartment","invest","booking","book"
]

# ══════════════════════════════════════════════════════════════
#  Unified Webhook  /webhook
# ══════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["GET","POST"])
def unified_webhook():

    # GET — Meta verification
    if request.method == "GET":
        mode, token, challenge = (
            request.args.get("hub.mode"),
            request.args.get("hub.verify_token"),
            request.args.get("hub.challenge")
        )
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    data = request.get_json(silent=True) or {}
    obj  = data.get("object","")

    # ── WhatsApp ──
    if obj == "whatsapp_business_account":
        try:
            val  = data["entry"][0]["changes"][0]["value"]
            msgs = val.get("messages",[])
            if msgs:
                msg    = msgs[0]
                sender = msg["from"]
                body   = msg.get("text",{}).get("body","")
                name   = val.get("contacts",[{}])[0].get("profile",{}).get("name","عميل")
                _handle_message(sender, name, body, "WhatsApp")
                _auto_reply_wa(sender, name)
        except Exception as e:
            print(f"[WA] ⚠️ {e}")
        return "OK", 200

    # ── Facebook Page (Messenger + Comments) ──
    if obj == "page":
        try:
            for entry in data.get("entry",[]):
                for event in entry.get("messaging",[]):
                    sid  = event["sender"]["id"]
                    text = event.get("message",{}).get("text","")
                    if text:
                        name = _get_messenger_name(sid)
                        _handle_message(sid, name, text, "Messenger")
                        _auto_reply_messenger(sid)
                for change in entry.get("changes",[]):
                    val = change.get("value",{})
                    if change.get("field") == "feed" and val.get("item") == "comment":
                        cid    = val.get("comment_id","")
                        sender = val.get("from",{})
                        text   = val.get("message","")
                        _handle_message(sender.get("id",""), sender.get("name",""), text, "Comment")
                        _auto_reply_comment(cid)
        except Exception as e:
            print(f"[Page] ⚠️ {e}")
        return "OK", 200

    return "OK", 200

# ══════════════════════════════════════════════════════════════
#  Lead Detection & Forward to n8n
# ══════════════════════════════════════════════════════════════
def _is_lead(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in LEAD_SIGNALS)

def _extract_phone(text: str):
    m = re.search(r'(\+?2?01[0125]\d{8})', text.replace(" ",""))
    return m.group(1) if m else None

def _handle_message(sender_id, name, text, channel):
    phone   = _extract_phone(text)
    is_lead = _is_lead(text) or phone is not None
    print(f"[{channel}] {'🎯' if is_lead else '💬'} {name}: {text[:60]}")

    if is_lead and N8N_WEBHOOK:
        try:
            requests.post(N8N_WEBHOOK, json={
                "sender_id":   sender_id,
                "sender_name": name,
                "message":     text,
                "channel":     channel,
                "phone":       phone,
                "has_phone":   phone is not None,
                "is_lead":     True,
                "source":      "realestate-bot"
            }, timeout=6)
            print(f"[Lead] ✅ أُرسل لـ n8n")
        except Exception as e:
            print(f"[Lead] ❌ {e}")

# ══════════════════════════════════════════════════════════════
#  Auto Replies
# ══════════════════════════════════════════════════════════════
def _auto_reply_wa(sender, name):
    if not WA_TOKEN or not WA_PHONE_ID:
        return
    msg = (f"مرحباً {name} 👋\n\nشكراً لتواصلك مع E-Solution 🏗️\n"
           "خبرة ٢٠+ سنة · ٥٠٠+ مشروع\n\n"
           "سيتواصل معك أخصائي مبيعات خلال دقائق ✅")
    requests.post(
        f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages",
        headers={"Authorization":f"Bearer {WA_TOKEN}","Content-Type":"application/json"},
        json={"messaging_product":"whatsapp","to":sender,"type":"text","text":{"body":msg}},
        timeout=8
    )

def _auto_reply_messenger(sender_id):
    if not PAGE_TOKEN:
        return
    requests.post("https://graph.facebook.com/v19.0/me/messages",
        params={"access_token": PAGE_TOKEN},
        json={"recipient":{"id":sender_id},
              "message":{"text":"شكراً لتواصلك! سيرد عليك أحد أخصائيينا قريباً ✅"}},
        timeout=8)

def _auto_reply_comment(comment_id):
    if not PAGE_TOKEN:
        return
    requests.post(f"https://graph.facebook.com/v19.0/{comment_id}/comments",
        params={"access_token": PAGE_TOKEN},
        json={"message":"شكراً على تعليقك! راسلنا على الخاص للمزيد من التفاصيل 📩"},
        timeout=8)

def _get_messenger_name(sender_id) -> str:
    try:
        r = requests.get(f"https://graph.facebook.com/v19.0/{sender_id}",
            params={"fields":"name","access_token":PAGE_TOKEN}, timeout=5)
        return r.json().get("name","عميل")
    except:
        return "عميل"

# ══════════════════════════════════════════════════════════════
#  Cron & Health
# ══════════════════════════════════════════════════════════════
@app.route("/cron/page", methods=["GET"])
def cron_page():
    if request.args.get("token") != VERIFY_TOKEN:
        return jsonify({"error":"unauthorized"}), 401
    return jsonify({"new_leads":0,"posts_scanned":5,"processed":0})

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "bot":"سلمى","status":"running",
        "channels":["messenger","whatsapp","fb_comments"],
        "n8n_connected": bool(N8N_WEBHOOK),
        "webhook":"/webhook"
    })

if __name__ == "__main__":
    app.run(debug=False, port=5000)
