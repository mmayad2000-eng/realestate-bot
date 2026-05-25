"""
Facebook Messenger API
"""
import requests
import config


def send_message(recipient_id, text):
    """ابعت رسالة نصية على ماسنجر"""
    url = f"https://graph.facebook.com/v19.0/me/messages"
    headers = {"Content-Type": "application/json"}
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
        "messaging_type": "RESPONSE",
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Messenger] Error sending to {recipient_id}: {e}")
        return False


def send_quick_replies(recipient_id, text, options):
    """ابعت رسالة مع أزرار اختيار سريع"""
    quick_replies = [
        {"content_type": "text", "title": opt, "payload": opt.upper().replace(" ", "_")}
        for opt in options
    ]
    url = f"https://graph.facebook.com/v19.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text, "quick_replies": quick_replies},
        "messaging_type": "RESPONSE",
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Messenger] Quick reply error: {e}")
        return False


def reply_to_comment(comment_id, message):
    """رد على تعليق فيسبوك"""
    url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
    payload = {
        "message": message,
        "access_token": config.FB_PAGE_ACCESS_TOKEN,
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"[Messenger] Comment reply error: {e}")
        return False


def send_dm_to_commenter(user_id, text):
    """ابعت رسالة خاصة لصاحب التعليق"""
    return send_message(user_id, text)
