"""Optional push notification delivery through ntfy; browser alerts are handled in the UI."""
import os
import requests

def send_ntfy(topic: str, title: str, message: str, server: str = "https://ntfy.sh") -> bool:
    if not topic: return False
    if any(ch.isspace() for ch in topic) or len(topic) > 128: return False
    try:
        r = requests.post(f"{server.rstrip('/')}/{topic}", data=message.encode("utf-8"), headers={"Title": title[:200], "Priority":"default"}, timeout=12)
        return r.status_code < 300
    except requests.RequestException:
        return False

def notify_task(task, username):
    topic = os.getenv("NTFY_TOPIC", "").strip()
    return send_ntfy(topic, f"MARKHOR reminder: {task.title}", f"For {username}. Due: {task.due_at}. {task.details}")
