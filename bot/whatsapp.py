"""
WhatsApp Business API via 360dialog
"""
import requests
import config


def send_message(to_number, text):
    """
    ابعت رسالة واتساب
    to_number: رقم المستقبل بالصيغة الدولية (مثلاً: 201001234567)
    """
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
    ابعت إشعار للموظف الحقيقي ببيانات العميل
    """
    msg = f"""🔔 *عميل جديد محتاج متابعة!*

👤 *الاسم:* {lead_data.get('name', 'غير معروف')}
📱 *الرقم:* {lead_data.get('phone', 'غير معروف')}
📍 *المصدر:* {lead_data.get('channel', 'غير معروف')}

📋 *تفاصيل الطلب:*
• النوع: {lead_data.get('type', '—')}
• الميزانية: {lead_data.get('budget', '—')}
• المنطقة: {lead_data.get('area', '—')}
• المساحة: {lead_data.get('size', '—')}

⏰ الوقت: {lead_data.get('timestamp', '—')}

⚡ *رجاءً التواصل معه خلال ساعة!*"""

    return send_message(agent["whatsapp"], msg)


def parse_incoming_webhook(data):
    """
    تحليل webhook الوارد من 360dialog
    Returns: list of {from, body, message_id}
    """
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
