"""
معالج المحادثة الرئيسي — نسخة محسّنة
يدعم: رقم التليفون | مشاريع ترشيح | طلب التواصل المباشر
"""
import config
from bot.conversation import (
    STAGE_START, STAGE_TYPE, STAGE_BUDGET, STAGE_AREA,
    STAGE_SIZE, STAGE_PHONE, STAGE_OFFER, STAGE_DONE,
    MSG_WELCOME, MSG_TYPE, MSG_BUDGET, MSG_AREA, MSG_SIZE,
    MSG_PHONE, MSG_PHONE_INVALID, MSG_OFFER, MSG_NOT_NOW,
    MSG_UNKNOWN, MSG_ABOUT,
    detect_intent, parse_type_answer, validate_phone,
    match_projects, format_projects,
    TRIGGER_KEYWORDS,
)
from bot import leads as lead_store

# كلمات طلب التواصل المباشر
CONTACT_KEYWORDS = [
    "رقم", "تليفون", "موبايل", "واتساب", "whatsapp",
    "تواصل", "اتصل", "مبيعات", "مسئول", "مسؤول",
    "بعت رقمك", "ابعت رقم", "كلمني", "اتصل بيا",
    "رقم التواصل", "رقم الشركة", "رقم المبيعات",
]


def _fmt(msg, **extra):
    """استبدل متغيرات الرسالة بالإعدادات"""
    return msg.format(
        bot_name=config.BOT_NAME,
        company=config.COMPANY_NAME,
        city=config.CITY,
        **extra,
    )


def _wants_contact(text):
    """هل العميل بيطلب رقم تواصل مباشر؟"""
    t = text.lower()
    return any(kw in t for kw in CONTACT_KEYWORDS)


def _send_contact_info(user_id, send_fn):
    """ابعت رقم التواصل للعميل"""
    # اختار أول موظف متاح
    if config.AGENTS:
        agent = config.AGENTS[0]
        wa = agent.get("whatsapp", "")
        name = agent.get("name", "فريق المبيعات")
        if wa and not wa.startswith("201XXXXX"):
            msg = (
                f"بكل سرور! 😊\n\n"
                f"تقدر تتواصل مع *{name}* مباشرة:\n"
                f"📱 واتساب: *{wa}*\n\n"
                f"أو كمل معايا وهبعتلك عرض مخصص! 🏠"
            )
        else:
            msg = (
                f"تمام! زميلنا المختص هيتواصل معاك في أقرب وقت 📞\n\n"
                f"أو كمل معايا الأسئلة البسيطة دي وهبعتلك عرض مخصص يناسبك! 🏠"
            )
    else:
        msg = "زميلنا المختص هيتواصل معاك قريباً 📞"
    send_fn(user_id, msg)


def handle_message(user_id, text, channel="messenger", send_fn=None):
    """
    المعالج الرئيسي — يُستدعى من webhook كل قناة
    """
    session = lead_store.get_session(user_id)
    stage = session["stage"]
    intent = detect_intent(text)

    # ===== لو بيطلب رقم تواصل في أي مرحلة =====
    if _wants_contact(text) and stage not in (STAGE_PHONE, STAGE_OFFER, STAGE_DONE):
        _send_contact_info(user_id, send_fn)
        # استمر في المحادثة بعدها
        if stage == STAGE_START:
            lead_store.update_session(user_id, stage=STAGE_TYPE, data_update={"channel": channel})
            send_fn(user_id, MSG_TYPE)
        return True

    # ===== لو بيسأل عن المشاريع =====
    if intent == "about" and stage == STAGE_START:
        send_fn(user_id, MSG_ABOUT)
        send_fn(user_id, "عاوز تعرف أكتر أو تبدأ طلبك؟ ابعت *\"شقة\"* وهساعدك! 🏠")
        return True

    # ===== مرحلة البداية =====
    if stage == STAGE_START:
        if intent in ("trigger", "positive") or any(kw in text.lower() for kw in TRIGGER_KEYWORDS):
            lead_store.update_session(user_id, stage=STAGE_TYPE, data_update={"channel": channel})
            send_fn(user_id, _fmt(MSG_WELCOME))
            send_fn(user_id, MSG_TYPE)
        elif intent == "not_now":
            send_fn(user_id, MSG_NOT_NOW)
        else:
            # أي رسالة تبدأ المحادثة
            lead_store.update_session(user_id, stage=STAGE_TYPE, data_update={"channel": channel})
            send_fn(user_id, _fmt(MSG_WELCOME))
            send_fn(user_id, MSG_TYPE)

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
        lead_store.update_session(user_id, stage=STAGE_PHONE, data_update={"size": text})
        send_fn(user_id, MSG_PHONE)

    # ===== رقم التليفون (مرحلة جديدة) =====
    elif stage == STAGE_PHONE:
        phone = validate_phone(text)
        if not phone:
            send_fn(user_id, MSG_PHONE_INVALID)
            return True

        lead_store.update_session(user_id, stage=STAGE_OFFER, data_update={"phone": phone})

        # احفظ العميل واختار مشاريع مناسبة
        lead = lead_store.save_lead(user_id, channel=channel)

        # رشح مشاريع مناسبة
        projects = match_projects(
            apt_type=lead.get("type", ""),
            budget_text=lead.get("budget", ""),
            size_text=lead.get("size", ""),
        )
        projects_text = format_projects(projects)

        # ابعت العرض مع المشاريع
        send_fn(user_id, _fmt(MSG_OFFER, projects_text=projects_text, phone=phone))

        # أشعر الموظف المخصص
        _notify_assigned_agent(lead)
        lead_store.update_session(user_id, stage=STAGE_DONE)

    # ===== منتهي — رسالة متابعة =====
    elif stage in (STAGE_OFFER, STAGE_DONE):
        if any(kw in text.lower() for kw in TRIGGER_KEYWORDS):
            # بدء طلب جديد
            lead_store.reset_session(user_id)
            lead_store.update_session(user_id, stage=STAGE_TYPE, data_update={"channel": channel})
            send_fn(user_id, _fmt(MSG_WELCOME))
            send_fn(user_id, MSG_TYPE)
        elif _wants_contact(text):
            _send_contact_info(user_id, send_fn)
        else:
            send_fn(
                user_id,
                "شكراً! 😊 لو عندك سؤال تاني أو عاوز تبدأ طلب جديد، ابعتلي *\"شقة\"* وهساعدك 🏠"
            )

    return True


def _notify_assigned_agent(lead):
    """ابعت إشعار للموظف المعين"""
    agent = lead.get("assigned_agent")
    if not agent:
        return
    try:
        from bot.whatsapp import notify_agent
        notify_agent(agent, lead)
    except Exception as e:
        print(f"[Handler] Could not notify agent: {e}")
