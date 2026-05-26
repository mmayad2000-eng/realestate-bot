"""
إدارة بيانات العملاء
"""
import json
import os
from datetime import datetime
import config

# حالات المحادثة في الذاكرة (per user)
_sessions = {}

# عداد الموظف الحالي للتناوب
_agent_index = 0


def get_session(user_id):
    """جيب أو أنشئ session للمستخدم"""
    if user_id not in _sessions:
        _sessions[user_id] = {
            "stage": "start",
            "data": {},
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "channel": "unknown",
        }
    return _sessions[user_id]


def update_session(user_id, stage=None, data_update=None):
    """حدّث الـ session"""
    session = get_session(user_id)
    if stage:
        session["stage"] = stage
    if data_update:
        session["data"].update(data_update)
    session["last_updated"] = datetime.now().isoformat()
    return session


def save_lead(user_id, channel="unknown"):
    """احفظ بيانات العميل في الملف"""
    global _agent_index
    session = get_session(user_id)
    
    # اختار الموظف المسؤول بالتناوب
    agents = config.AGENTS
    assigned_agent = agents[_agent_index % len(agents)] if agents else None
    _agent_index += 1

    lead = {
        "id": user_id,
        "channel": channel,
        "assigned_agent": assigned_agent,
        "timestamp": datetime.now().isoformat(),
        "status": "new",
        **session["data"]
    }

    # حمّل الملف الحالي
    leads = _load_leads()
    # حدّث أو أضف
    existing = next((i for i, l in enumerate(leads) if l["id"] == user_id), None)
    if existing is not None:
        leads[existing] = lead
    else:
        leads.append(lead)

    _save_leads(leads)
    return lead


def _load_leads():
    if not os.path.exists(config.LEADS_FILE):
        return []
    with open(config.LEADS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_leads(leads):
    with open(config.LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)


def get_all_leads():
    return _load_leads()


def mark_lead_contacted(user_id):
    leads = _load_leads()
    for lead in leads:
        if lead["id"] == user_id:
            lead["status"] = "contacted"
    _save_leads(leads)


def reset_session(user_id):
    """إعادة تعيين session العميل للبداية"""
    if user_id in _sessions:
        _sessions[user_id] = {
            "stage": "start",
            "data": {},
            "created_at": _sessions[user_id].get("created_at", ""),
            "last_updated": datetime.now().isoformat(),
            "channel": "unknown",
        }
