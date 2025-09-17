from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.push_notifications import PushSubscriptionIn, PushSubscriptionOut, SendNotificationRequest
from app.services.push_notifications import (
    save_or_update_subscription,
    deactivate_subscription,
    send_to_subscription,
    PushSendError,
)
from app.services.auth import get_current_admin

router = APIRouter()


@router.get("/public-key", response_model=dict)
def get_public_key():
    if not settings.VAPID_PUBLIC_KEY:
        return {"publicKey": ""}
    return {"publicKey": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=PushSubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe(
    subscription: PushSubscriptionIn,
    db: Session = Depends(get_db),
):
    try:
        sub = save_or_update_subscription(db, subscription, user_id=None)
        return PushSubscriptionOut(id=sub.id, endpoint=sub.endpoint, is_active=sub.is_active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscribe failed: {str(e)}")


@router.delete("/subscribe", response_model=dict)
def unsubscribe(
    endpoint: str,
    db: Session = Depends(get_db),
):
    try:
        ok = deactivate_subscription(db, endpoint)
        if not ok:
            return {"status": "not_found"}
        return {"status": "deactivated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unsubscribe failed: {str(e)}")


@router.post("/test", response_model=dict)
def send_test_notification(
    req: SendNotificationRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_admin),
):
    """Admin-only: send a test notification to the most recent active subscription."""
    from sqlalchemy import select, desc
    from app.models.web_push_subscription import WebPushSubscription

    sub = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.is_active == True).order_by(desc(WebPushSubscription.id)).limit(1)
    ).scalar_one_or_none()

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscriptions")

    payload = {"title": req.title, "body": req.body, "data": req.data or {}, "icon": req.icon, "tag": req.tag}

    def _send():
        try:
            send_to_subscription(sub, payload)
        except PushSendError as ex:
            if ex.status_code in (404, 410):
                sub.is_active = False
                db.add(sub)
                db.commit()

    background.add_task(_send)
    return {"status": "queued"}
