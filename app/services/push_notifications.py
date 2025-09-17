from typing import Optional, Dict, Any, Iterable, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from pywebpush import webpush, WebPushException

from app.core.config import settings
from app.models.web_push_subscription import WebPushSubscription
from app.schemas.push_notifications import PushSubscriptionIn


def save_or_update_subscription(
    db: Session,
    subscription_in: PushSubscriptionIn,
    user_id: Optional[int] = None,
) -> WebPushSubscription:
    existing: Optional[WebPushSubscription] = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.endpoint == subscription_in.endpoint)
    ).scalar_one_or_none()

    if existing:
        existing.p256dh_key = subscription_in.keys.p256dh
        existing.auth_key = subscription_in.keys.auth
        existing.user_agent = subscription_in.user_agent
        existing.is_active = True
        if user_id is not None:
            existing.user_id = user_id
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    new_sub = WebPushSubscription(
        endpoint=subscription_in.endpoint,
        p256dh_key=subscription_in.keys.p256dh,
        auth_key=subscription_in.keys.auth,
        user_agent=subscription_in.user_agent,
        is_active=True,
        user_id=user_id,
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


def deactivate_subscription(db: Session, endpoint: str) -> bool:
    sub: Optional[WebPushSubscription] = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    if not sub:
        return False
    sub.is_active = False
    db.add(sub)
    db.commit()
    return True


def delete_subscription(db: Session, endpoint: str) -> bool:
    sub: Optional[WebPushSubscription] = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    if not sub:
        return False
    db.delete(sub)
    db.commit()
    return True


def send_to_subscription(
    subscription: WebPushSubscription,
    payload: Dict[str, Any],
) -> None:
    if not (settings.VAPID_PRIVATE_KEY and settings.VAPID_SUBJECT):
        raise RuntimeError("VAPID keys/subject not configured")

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh_key,
            "auth": subscription.auth_key,
        },
    }

    try:
        webpush(
            subscription_info=subscription_info,
            data=json_dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
        )
    except WebPushException as ex:
        # 404/410 indicate invalid/expired subscription — caller should deactivate
        status_code = getattr(ex.response, "status_code", None)
        message = str(ex)
        raise PushSendError(message=message, status_code=status_code) from ex


def broadcast_to_active_subscriptions(
    db: Session,
    payload: Dict[str, Any],
    batch_size: int = 500,
) -> Dict[str, int]:
    offset = 0
    sent = 0
    deactivated = 0
    from sqlalchemy import and_

    while True:
        batch: List[WebPushSubscription] = (
            db.query(WebPushSubscription)
            .filter(WebPushSubscription.is_active == True)  # noqa: E712
            .order_by(WebPushSubscription.id.asc())
            .offset(offset)
            .limit(batch_size)
            .all()
        )
        if not batch:
            break

        for sub in batch:
            try:
                send_to_subscription(sub, payload)
                sent += 1
            except PushSendError as err:
                # Deactivate on 404/410; keep others for later retry
                if err.status_code in (404, 410):
                    sub.is_active = False
                    db.add(sub)
                    deactivated += 1
        db.commit()
        offset += len(batch)

    return {"sent": sent, "deactivated": deactivated}


class PushSendError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def json_dumps(data: Dict[str, Any]) -> str:
    # Minimal wrapper to avoid adding extra deps here
    import json

    return json.dumps(data, separators=(",", ":"))
