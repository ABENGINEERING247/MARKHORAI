"""Run as a persistent background worker on an always-on host: python worker.py"""
import os, time, logging
from datetime import datetime, timezone
from markhor.db import session, Task, User
from markhor.notifications import notify_task

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
POLL_SECONDS = int(os.getenv("MARKHOR_POLL_SECONDS", "20"))

def run_once():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = session()
    try:
        due = db.query(Task).filter(Task.status == "scheduled", Task.due_at <= now).limit(100).all()
        for task in due:
            user = db.query(User).filter(User.id == task.user_id).first()
            if not user:
                task.status = "failed"
                continue
            ok = notify_task(task, user.username)
            task.status = "notified" if ok else "due"
            if ok: task.notified_at = now
            logging.info("task_id=%s user_id=%s delivery=%s", task.id, task.user_id, "sent" if ok else "not-configured-or-failed")
        db.commit()
    except Exception:
        db.rollback(); logging.exception("Worker cycle failed")
    finally: db.close()

if __name__ == "__main__":
    logging.info("MARKHOR notification worker started")
    while True:
        run_once(); time.sleep(POLL_SECONDS)
