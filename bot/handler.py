"""
معالج المحادثة الرئيسي — نفس المنطق لكل القنوات
"""
import config
from bot.conversation import (
    STAGE_START, STAGE_TYPE, STAGE_BUDGET, STAGE_AREA,
    STAGE_SIZE, STAGE_OFFER, STAGE_DONE,
    MSG_WELCOME, MSG_TYPE, MSG_BUDGET, MSG_AREA, MSG_SIZE,
    MSG_OFFER, MSG_NOT_NOW, MSG_UNKNOWN,
    detect_intent, parse_type_answer, TRIGGER_KEYWORDS,
)
from bot import leads as lead_store


def _fmt(msg):
    """استبدل متغيرات الرسالة بالإعدادات"""
    return msg.format(
        bot_name=config.BOT_NAME,
        company=config.COMPANY_NAME,
        city=config.CITY,
    )


def handle_message(user_id, text, channel="messenger", send_fn=None):
    """
    المعالج الرئيسي — يُستدعى من webhook كل قناة
    send_fn(user_id, text) — دالة الإرسال الخاصة بالقناة
    Returns: True إذا تمت المعالجة
    """
    session = lead_store.get_session(user_id)
    stage = session["stage"]
    intent = detect_intent(text)

    # ===== مرحلة البداية =====
    if stage == STAGE_START:
        # أي كلمة تشغيل أو رد إيجابي
        if intent in ("trigger", "positive") or any(kw in text.lower() for kw in TRIGGER_KEYWORDS):
            lead_store.update_session(user_id, stage=STAGE_TYPE, data_update={"channel": channel})
            send_fn(user_id, _fmt(MSG_WELCOME))
            send_fn(user_id, MSG_TYPE)
        elif intent == "not_now":
            send_fn(user_id, MSG_NOT_NOW)
        else:
            send_fn(user_id, _fmt(MSG_WELCOME))
            send_fn(user_id, MSG_TYPE)
            lead_store.update_session(user_id, stage=STAGE_TYPE)

    # ===== نوع الشقة =====
    elif stage == STAGE_TYPE:
        apt_type = parse_type_answer(text)
        lead_store.update_session(user_id, stage=STAGE_BUDGET, data_update={"type": apt_type})
        send_fn(user_id, MSG_BUDGET)

    # ===== الميزانية =====
    elif stage == STAGE_BUDGET:
        lead_store.update_session(user_id, stage=STAGE_AREA, data_update={"budget": text})
        send_fn(user_id, MSG_AREA)

    # ===== المنطقة =====
    elif stage == STAGE_AREA:
        lead_store.update_session(user_id, stage=STAGE_SIZE, data_update={"area": text})
        send_fn(user_id, MSG_SIZE)

    # ===== الحجم والدور =====
    elif stage == STAGE_SIZE:
        lead_store.update_session(user_id, stage=STAGE_OFFER, data_update={"size": text})
        # احفظ العميل واختار موظف
        lead = lead_store.save_lead(user_id, channel=channel)
        # ابعت رسالة إنجاز للعميل
        send_fn(user_id, _fmt(MSG_OFFER))
        # أشعر الموظف المخصص
        _notify_assigned_agent(lead)
        lead_store.update_session(user_id, stage=STAGE_DONE)

    # ===== منتهي — لو بعت رسالة تانية =====
    elif stage in (STAGE_OFFER, STAGE_DONE):
        if any(kw in text.lower() for kw in TRIGGER_KEYWORDS):
            # عميل جديد يبدأ من أول
            lead_store.update_session(user_id, stage=STAGE_TYPE)
            send_fn(user_id, _fmt(MSG_WELCOME))
            send_fn(user_id, MSG_TYPE)
        else:
            send_fn(user_id, "شكراً! لو عندك أي استفسار تاني أو عاوز تبدأ طلب جديد، ابعت لي \"شقة\" وهساعدك 😊")

    return True


def _notify_assigned_agent(lead):
    """ابعت إشعار للموظف المعين"""
    agent = lead.get("assigned_agent")
    if not agent:
        return
    try:
        from bot.whatsapp import notify_agent
        notify_agent(agent, lead)
        print(f"[Handler] Notified agent {agent['name']} for lead {lead['id']}")
    except Exception as e:
        print(f"[Handler] Could not notify agent: {e}")
