from typing import Optional, Dict, Any, Iterable, List

from sqlalchemy.orm import Session
from sqlalchemy import select
from pywebpush import webpush, WebPushException
import logging
import time

from app.core.config import settings
from app.models.web_push_subscription import WebPushSubscription
from app.schemas.push_notifications import PushSubscriptionIn

logger = logging.getLogger(__name__)


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
        logger.info("Updated subscription endpoint=%s id=%s active=%s", existing.endpoint, existing.id, existing.is_active)
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
    logger.info("Created subscription endpoint=%s id=%s", new_sub.endpoint, new_sub.id)
    return new_sub


def deactivate_subscription(db: Session, endpoint: str) -> bool:
    sub: Optional[WebPushSubscription] = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    if not sub:
        logger.warning("Deactivate requested for missing endpoint=%s", endpoint)
        return False
    sub.is_active = False
    db.add(sub)
    db.commit()
    logger.info("Deactivated subscription endpoint=%s id=%s", endpoint, sub.id)
    return True


def delete_subscription(db: Session, endpoint: str) -> bool:
    sub: Optional[WebPushSubscription] = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.endpoint == endpoint)
    ).scalar_one_or_none()
    if not sub:
        logger.warning("Delete requested for missing endpoint=%s", endpoint)
        return False
    db.delete(sub)
    db.commit()
    logger.info("Deleted subscription endpoint=%s id=%s", endpoint, sub.id)
    return True


def send_to_subscription(
    subscription: WebPushSubscription,
    payload: Dict[str, Any],
    max_retries: int = 2,
    backoff_seconds: float = 0.5,
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

    attempt = 0
    while True:
        try:
            webpush(
                subscription_info=subscription_info,
                data=json_dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": settings.VAPID_SUBJECT},
            )
            logger.info("Push sent endpoint=%s", subscription.endpoint)
            return
        except WebPushException as ex:
            status_code = getattr(ex.response, "status_code", None)
            logger.warning(
                "Push failed endpoint=%s status=%s attempt=%s error=%s",
                subscription.endpoint,
                status_code,
                attempt + 1,
                str(ex),
            )
            # Do not retry on permanently invalid subscriptions
            if status_code in (404, 410):
                raise PushSendError(message=str(ex), status_code=status_code) from ex
            attempt += 1
            if attempt > max_retries:
                raise PushSendError(message=str(ex), status_code=status_code) from ex
            time.sleep(backoff_seconds * attempt)


def broadcast_to_active_subscriptions(
    db: Session,
    payload: Dict[str, Any],
    batch_size: int = 500,
) -> Dict[str, int]:
    offset = 0
    sent = 0
    deactivated = 0

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
                if err.status_code in (404, 410):
                    sub.is_active = False
                    db.add(sub)
                    deactivated += 1
                else:
                    logger.error(
                        "Push permanently failed endpoint=%s status=%s", sub.endpoint, err.status_code
                    )
        db.commit()
        offset += len(batch)

    logger.info("Broadcast complete sent=%s deactivated=%s", sent, deactivated)
    return {"sent": sent, "deactivated": deactivated}


class PushSendError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def json_dumps(data: Dict[str, Any]) -> str:
    # Minimal wrapper to avoid adding extra deps here
    import json

    return json.dumps(data, separators=(",", ":"))
