# backend/utils/notify.py

"""
Simple placeholder for notifications (email / slack / etc.).
"""


def notify_user(user_id: str, message: str):
    # TODO: integrate real email / push logic
    print(f"[NOTIFY] user={user_id}: {message}")
