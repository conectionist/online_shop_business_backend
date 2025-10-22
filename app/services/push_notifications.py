from typing import Optional, Dict, Any, Iterable, List

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from pywebpush import webpush, WebPushException
import logging
import time
import random

from app.core.config import settings
from app.models.web_push_subscription import WebPushSubscription
from app.models.notification_log import NotificationLog
from app.models.notification_topic import NotificationTopic
from app.models.subscription_topic import SubscriptionTopic
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
    max_retries: int = 3,
    base_backoff_seconds: float = 0.5,
    event_id: Optional[str] = None,
    db: Optional[Session] = None,
) -> bool:
    """Send a push. Returns True if delivered (or skipped due to dedupe), False if transient failure after retries.

    - If event_id provided and db given: dedupe by (subscription_id, event_id)
    - On success with event_id: insert NotificationLog
    """
    if event_id and db is not None:
        # Dedupe check
        existing_log = db.execute(
            select(NotificationLog).where(
                and_(NotificationLog.subscription_id == subscription.id, NotificationLog.event_key == event_id)
            )
        ).scalar_one_or_none()
        if existing_log is not None:
            logger.info("Deduped event_id=%s for subscription id=%s", event_id, subscription.id)
            return True

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
                ttl=payload.get("ttl_seconds") if isinstance(payload, dict) else None,
            )
            logger.info("Push sent endpoint=%s event_id=%s", subscription.endpoint, event_id)
            if event_id and db is not None:
                # Log delivery for dedupe
                db.add(NotificationLog(subscription_id=subscription.id, event_key=event_id))
                db.commit()
            return True
        except WebPushException as ex:
            status_code = getattr(ex.response, "status_code", None)
            logger.warning(
                "Push failed endpoint=%s status=%s attempt=%s error=%s",
                subscription.endpoint,
                status_code,
                attempt + 1,
                str(ex),
            )
            if status_code in (404, 410):
                raise PushSendError(message=str(ex), status_code=status_code) from ex
            attempt += 1
            if attempt > max_retries:
                return False
            # exponential backoff with jitter
            delay = min(30.0, base_backoff_seconds * (2 ** (attempt - 1)))
            jitter = random.uniform(0, delay / 2)
            time.sleep(delay + jitter)


def broadcast_to_active_subscriptions(
    db: Session,
    payload: Dict[str, Any],
    batch_size: int = 500,
    event_id: Optional[str] = None,
) -> Dict[str, int]:
    offset = 0
    sent = 0
    deactivated = 0
    skipped = 0

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
                delivered_or_skipped = send_to_subscription(sub, payload, event_id=event_id, db=db)
                if delivered_or_skipped:
                    sent += 1
                else:
                    logger.error("Push transiently failed after retries endpoint=%s", sub.endpoint)
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

    logger.info("Broadcast complete sent_or_skipped=%s deactivated=%s", sent, deactivated)
    return {"sent_or_skipped": sent, "deactivated": deactivated}


def prune_inactive_subscriptions(db: Session, older_than_days: int = 30, batch_size: int = 1000) -> int:
    """Hard-delete inactive subscriptions older than the retention window.

    Returns number of rows deleted. Related notification logs are removed via FK cascade.
    """
    deletion_query = text(
        """
        DELETE FROM web_push_subscription
        WHERE is_active = 0
          AND updated_at < (CURRENT_TIMESTAMP - INTERVAL :days DAY)
        LIMIT :limit
        """
    )
    total_deleted = 0
    while True:
        result = db.execute(deletion_query, {"days": older_than_days, "limit": batch_size})
        db.commit()
        deleted = result.rowcount if hasattr(result, "rowcount") else 0
        total_deleted += max(0, deleted or 0)
        logger.info("Prune pass deleted=%s (total=%s)", deleted, total_deleted)
        if not deleted or deleted <= 0:
            break
    return total_deleted


class PushSendError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


def send_to_admin_subscriptions(
    db: Session,
    admin_id: int,
    payload: Dict[str, Any],
    event_id: Optional[str] = None,
) -> Dict[str, int]:
    """Send notification to all subscriptions of a specific admin.
    
    Args:
        db: Database session
        admin_id: Admin user ID
        payload: Notification payload
        event_id: Optional event ID for deduplication
        
    Returns:
        Dict with 'sent' count
    """
    subscriptions = db.query(WebPushSubscription).filter(
        WebPushSubscription.user_id == admin_id,
        WebPushSubscription.is_active == True  # noqa: E712
    ).all()
    
    sent = 0
    deactivated = 0
    
    for sub in subscriptions:
        try:
            delivered_or_skipped = send_to_subscription(sub, payload, event_id=event_id, db=db)
            if delivered_or_skipped:
                sent += 1
            else:
                logger.error("Push transiently failed after retries endpoint=%s", sub.endpoint)
        except PushSendError as err:
            if err.status_code in (404, 410):
                sub.is_active = False
                db.add(sub)
                deactivated += 1
            else:
                logger.error(
                    "Push permanently failed endpoint=%s status=%s", sub.endpoint, err.status_code
                )
    
    if deactivated > 0:
        db.commit()
    
    logger.info("Admin notification sent to admin_id=%s sent=%s deactivated=%s", admin_id, sent, deactivated)
    return {"sent": sent, "deactivated": deactivated}


def send_to_all_admins(
    db: Session,
    payload: Dict[str, Any],
    event_id: Optional[str] = None,
) -> Dict[str, int]:
    """Send notification to all admin subscriptions.
    
    Args:
        db: Database session
        payload: Notification payload
        event_id: Optional event ID for deduplication
        
    Returns:
        Dict with 'sent' and 'deactivated' counts
    """
    subscriptions = db.query(WebPushSubscription).filter(
        WebPushSubscription.user_id.isnot(None),  # Only admin subscriptions
        WebPushSubscription.is_active == True  # noqa: E712
    ).all()
    
    sent = 0
    deactivated = 0
    
    for sub in subscriptions:
        try:
            delivered_or_skipped = send_to_subscription(sub, payload, event_id=event_id, db=db)
            if delivered_or_skipped:
                sent += 1
            else:
                logger.error("Push transiently failed after retries endpoint=%s", sub.endpoint)
        except PushSendError as err:
            if err.status_code in (404, 410):
                sub.is_active = False
                db.add(sub)
                deactivated += 1
            else:
                logger.error(
                    "Push permanently failed endpoint=%s status=%s", sub.endpoint, err.status_code
                )
    
    if deactivated > 0:
        db.commit()
    
    logger.info("Admin broadcast sent=%s deactivated=%s", sent, deactivated)
    return {"sent": sent, "deactivated": deactivated}


def json_dumps(data: Dict[str, Any]) -> str:
    # Minimal wrapper to avoid adding extra deps here
    import json

    return json.dumps(data, separators=(",", ":"))


# ---- Topic subscription and routing services ----

def list_notification_topics(db: Session) -> List[NotificationTopic]:
    """Return all available notification topics."""
    return db.query(NotificationTopic).order_by(NotificationTopic.id.asc()).all()


def subscribe_subscription_to_topics(
    db: Session,
    subscription_id: int,
    topic_ids: List[int],
) -> int:
    """Subscribe a WebPush subscription to the given topic IDs.

    Returns number of new mappings created (idempotent - existing pairs are ignored).
    """
    if not topic_ids:
        return 0

    created = 0
    for topic_id in topic_ids:
        # Check if mapping exists
        existing = (
            db.query(SubscriptionTopic)
            .filter(
                SubscriptionTopic.subscription_id == subscription_id,
                SubscriptionTopic.topic_id == topic_id,
            )
            .first()
        )
        if existing is None:
            db.add(SubscriptionTopic(subscription_id=subscription_id, topic_id=topic_id))
            created += 1
    if created:
        db.commit()
    return created


def unsubscribe_subscription_from_topics(
    db: Session,
    subscription_id: int,
    topic_ids: List[int],
) -> int:
    """Unsubscribe a subscription from given topic IDs.

    Returns number of mappings removed.
    """
    if not topic_ids:
        return 0

    deleted = (
        db.query(SubscriptionTopic)
        .filter(
            SubscriptionTopic.subscription_id == subscription_id,
            SubscriptionTopic.topic_id.in_(topic_ids),
        )
        .delete(synchronize_session=False)
    )
    if deleted:
        db.commit()
    return int(deleted or 0)


def send_to_subscriptions_by_topic(
    db: Session,
    topic_name: str,
    payload: Dict[str, Any],
    event_id: Optional[str] = None,
) -> Dict[str, int]:
    """Send a notification to all active subscriptions that subscribed to the topic."""
    topic: Optional[NotificationTopic] = (
        db.query(NotificationTopic).filter(NotificationTopic.name == topic_name).first()
    )
    if not topic:
        logger.warning("Topic '%s' not found", topic_name)
        return {"sent": 0, "deactivated": 0}

    # Get subscription IDs subscribed to the topic
    sub_topic_rows: List[SubscriptionTopic] = (
        db.query(SubscriptionTopic).filter(SubscriptionTopic.topic_id == topic.id).all()
    )
    if not sub_topic_rows:
        return {"sent": 0, "deactivated": 0}

    subscription_ids = [row.subscription_id for row in sub_topic_rows]
    subscriptions: List[WebPushSubscription] = (
        db.query(WebPushSubscription)
        .filter(
            WebPushSubscription.id.in_(subscription_ids),
            WebPushSubscription.is_active == True,  # noqa: E712
        )
        .all()
    )

    sent = 0
    deactivated = 0
    for sub in subscriptions:
        try:
            delivered_or_skipped = send_to_subscription(sub, payload, event_id=event_id, db=db)
            if delivered_or_skipped:
                sent += 1
            else:
                logger.error("Push transiently failed after retries endpoint=%s", sub.endpoint)
        except PushSendError as err:
            if err.status_code in (404, 410):
                sub.is_active = False
                db.add(sub)
                deactivated += 1
            else:
                logger.error(
                    "Push permanently failed endpoint=%s status=%s", sub.endpoint, err.status_code
                )

    if deactivated > 0:
        db.commit()

    logger.info(
        "Topic send complete topic=%s sent=%s deactivated=%s", topic_name, sent, deactivated
    )
    return {"sent": sent, "deactivated": deactivated}
