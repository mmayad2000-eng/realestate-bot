"""
WhatsApp Business API via 360dialog
"""
import requests
import config


def send_message(to_number, text):
    """ابعت رسالة واتساب"""
    url = f"{config.WHATSAPP_API_URL}/messages"
    headers = {
        "D360-API-KEY": config.WHATSAPP_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {"body": text},
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[WhatsApp] Error sending to {to_number}: {e}")
        return False


def notify_agent(agent, lead_data):
    """
    ابعت إشعار للموظف المعيّن ببيانات العميل الكاملة
    مع رابط واتساب مباشر للتواصل فوراً
    """
    phone = lead_data.get('phone', '')
    # رابط واتساب مباشر
    wa_link = f"https://wa.me/{phone.replace('0', '20', 1)}" if phone else ""

    msg = (
        f"🔔 *عميل جديد — يحتاج متابعة فورية!*\n\n"
        f"📱 *رقم العميل:* {phone}\n"
        f"{'🔗 واتساب مباشر: ' + wa_link if wa_link else ''}\n\n"
        f"📋 *تفاصيل الطلب:*\n"
        f"  • النوع: {lead_data.get('type', '—')}\n"
        f"  • الميزانية: {lead_data.get('budget', '—')}\n"
        f"  • المنطقة: {lead_data.get('area', '—')}\n"
        f"  • المساحة: {lead_data.get('size', '—')}\n"
        f"  • المصدر: {lead_data.get('channel', '—')}\n\n"
        f"⏰ {lead_data.get('timestamp', '')[:16]}\n\n"
        f"⚡ *رجاءً التواصل خلال أقل من ساعة!*"
    )

    agent_wa = agent.get("whatsapp", "")
    if not agent_wa or agent_wa.startswith("201XXXXX"):
        print(f"[WhatsApp] Agent {agent.get('name')} has no real number set")
        return False

    return send_message(agent_wa, msg)


def parse_incoming_webhook(data):
    """تحليل webhook الوارد من 360dialog أو Cloud API"""
    messages = []
    try:
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    messages.append({
                        "from": msg.get("from"),
                        "body": msg.get("text", {}).get("body", ""),
                        "message_id": msg.get("id"),
                        "type": msg.get("type", "text"),
                    })
    except Exception as e:
        print(f"[WhatsApp] Parse error: {e}")
    return messages
