"""
مراقبة تعليقات صفحة الفيسبوك — يشتغل من endpoint أو cron
E-Solution | طنطا
"""
import requests
import logging
import json
import os

import config
from bot.conversation import TRIGGER_KEYWORDS, MSG_COMMENT_REPLY
from bot import messenger, leads as lead_store

logger = logging.getLogger(__name__)

# ملف لتخزين آخر تعليق تمت معالجته
_PROCESSED_FILE = "/tmp/processed_comments.json"


def _load_processed():
    try:
        with open(_PROCESSED_FILE) as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_processed(ids: set):
    try:
        with open(_PROCESSED_FILE, "w") as f:
            json.dump(list(ids), f)
    except Exception:
        pass


def get_page_posts(limit=10):
    """اجلب آخر بوستات الصفحة"""
    url = "https://graph.facebook.com/v19.0/me/feed"
    params = {
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
        "fields": "id,message,created_time",
        "limit": limit,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "error" in data:
            logger.error(f"[PageMonitor] FB API error: {data['error']}")
            return []
        return data.get("data", [])
    except Exception as e:
        logger.error(f"[PageMonitor] Error fetching posts: {e}")
        return []


def get_post_comments(post_id, limit=25):
    """اجلب تعليقات بوست معين"""
    url = f"https://graph.facebook.com/v19.0/{post_id}/comments"
    params = {
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
        "fields": "id,message,from,created_time",
        "limit": limit,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        if "error" in data:
            logger.error(f"[PageMonitor] FB API error for {post_id}: {data['error']}")
            return []
        return data.get("data", [])
    except Exception as e:
        logger.error(f"[PageMonitor] Error fetching comments for {post_id}: {e}")
        return []


def reply_to_comment(comment_id, message):
    """رد على تعليق"""
    url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
    params = {"access_token": config.FB_PAGE_ACCESS_TOKEN}
    payload = {"message": message}
    try:
        r = requests.post(url, params=params, json=payload, timeout=10)
        if r.status_code == 200:
            logger.info(f"[PageMonitor] Replied to comment {comment_id}")
            return True
        logger.warning(f"[PageMonitor] Reply failed ({r.status_code}): {r.text[:100]}")
    except Exception as e:
        logger.error(f"[PageMonitor] Error replying to {comment_id}: {e}")
    return False


def scan_page_comments():
    """
    الدالة الرئيسية — تفحص كل تعليقات الصفحة وترد على العملاء المهتمين
    بتُستدعى من /cron/page كل ساعة
    """
    if not config.FB_PAGE_ACCESS_TOKEN:
        return {"error": "FB_PAGE_ACCESS_TOKEN غير مضبوط", "new_leads": 0}

    processed = _load_processed()
    new_leads = 0
    fb_errors = []

    posts = get_page_posts(limit=5)
    logger.info(f"[PageMonitor] Scanning {len(posts)} posts...")

    if not posts:
        return {
            "processed": len(processed),
            "new_leads": 0,
            "note": "لا يوجد بوستات أو خطأ في الاتصال بالفيسبوك"
        }

    for post in posts:
        post_id = post["id"]
        comments = get_post_comments(post_id, limit=50)

        for comment in comments:
            comment_id   = comment.get("id", "")
            comment_text = comment.get("message", "").strip()
            commenter    = comment.get("from", {})
            commenter_id = commenter.get("id", "")
            commenter_name = commenter.get("name", "")

            # تجاهل التعليقات المعالجة مسبقاً
            if comment_id in processed:
                continue

            processed.add(comment_id)

            # هل فيه كلمة مفتاحية؟
            text_lower = comment_text.lower()
            if not any(kw in text_lower for kw in TRIGGER_KEYWORDS):
                continue

            logger.info(f"[PageMonitor] Keyword match: {commenter_name} ({commenter_id}): {comment_text[:50]}")

            # رد على التعليق
            reply_to_comment(comment_id, MSG_COMMENT_REPLY)

            # ابدأ محادثة ماسنجر معه
            if commenter_id:
                from bot.handler import handle_message
                handle_message(
                    commenter_id,
                    comment_text,
                    channel="fb_comment",
                    send_fn=messenger.send_message
                )
                new_leads += 1

    _save_processed(processed)
    logger.info(f"[PageMonitor] Done. New leads from comments: {new_leads}")
    return {
        "processed": len(processed),
        "new_leads": new_leads,
        "posts_scanned": len(posts)
    }


def subscribe_page_to_webhooks():
    """
    اشترك في أحداث الصفحة (يُنفَّذ مرة واحدة)
    GET /setup/subscribe لتفعيله

    ملاحظة: "feed" يتطلب pages_manage_metadata.
    الكومنتات تُعالج بـ polling كل ساعة عبر /cron/page
    """
    url = "https://graph.facebook.com/v19.0/me/subscribed_apps"
    results = {}

    # المحاولة ١: messages + messaging_postbacks (لا تحتاج pages_manage_metadata)
    params1 = {
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
        "subscribed_fields": "messages,messaging_postbacks,messaging_optins",
    }
    try:
        r1 = requests.post(url, params=params1, timeout=10)
        results["messages"] = r1.json()
        logger.info(f"[PageMonitor] Subscribe (messages): {results['messages']}")
    except Exception as e:
        results["messages"] = {"error": str(e)}

    # المحاولة ٢: feed (قد تحتاج pages_manage_metadata)
    params2 = {
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
        "subscribed_fields": "feed",
    }
    try:
        r2 = requests.post(url, params=params2, timeout=10)
        results["feed"] = r2.json()
        logger.info(f"[PageMonitor] Subscribe (feed): {results['feed']}")
    except Exception as e:
        results["feed"] = {"error": str(e)}

    results["polling_active"] = True
    results["note"] = "الكومنتات تُراقَب كل ساعة عبر /cron/page حتى لو feed subscription فشلت"
    return results
