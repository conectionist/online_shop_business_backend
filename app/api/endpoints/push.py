from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.config import settings
from app.schemas.push_notifications import PushSubscriptionIn, PushSubscriptionOut, SendNotificationRequest
from app.services.push_notifications import (
    save_or_update_subscription,
    deactivate_subscription,
    send_to_subscription,
    send_to_admin_subscriptions,
    send_to_all_admins,
    PushSendError,
)
from app.services.auth import get_current_admin, Admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/public-key", response_model=dict)
def get_public_key():
    if not settings.VAPID_PUBLIC_KEY:
        return {"publicKey": ""}
    return {"publicKey": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", response_model=PushSubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe_customer(
    subscription: PushSubscriptionIn,
    db: Session = Depends(get_db),
):
    """Subscribe to push notifications (customer - no authentication required)."""
    try:
        # Customer subscription - no user association
        sub = save_or_update_subscription(db, subscription, user_id=None)
        return PushSubscriptionOut(id=sub.id, endpoint=sub.endpoint, is_active=sub.is_active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Subscribe failed: {str(e)}")


@router.post("/admin/subscribe", response_model=PushSubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe_admin(
    subscription: PushSubscriptionIn,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Subscribe to push notifications (admin - authentication required)."""
    try:
        # Associate subscription with current admin
        sub = save_or_update_subscription(db, subscription, user_id=current_admin.id)
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
    current_admin: Admin = Depends(get_current_admin),
):
    """Admin-only: send a test notification to the most recent active subscription."""
    from sqlalchemy import select, desc
    from app.models.web_push_subscription import WebPushSubscription
    from app.core.database import SessionLocal

    sub = db.execute(
        select(WebPushSubscription).where(WebPushSubscription.is_active == True).order_by(desc(WebPushSubscription.id)).limit(1)
    ).scalar_one_or_none()

    if not sub:
        raise HTTPException(status_code=404, detail="No active subscriptions")

    payload = {
        "title": req.title,
        "body": req.body,
        "data": req.data or {},
        "icon": req.icon,
        "tag": req.event_id or req.tag,
    }

    sub_id = sub.id

    def _send():
        from sqlalchemy import select as _select
        try:
            session = SessionLocal()
            fresh = session.execute(_select(WebPushSubscription).where(WebPushSubscription.id == sub_id)).scalar_one_or_none()
            if not fresh:
                return
            try:
                send_to_subscription(fresh, payload, event_id=req.event_id, db=session)
            except PushSendError as ex:
                if ex.status_code in (404, 410):
                    fresh.is_active = False
                    session.add(fresh)
                    session.commit()
        finally:
            try:
                session.close()
            except Exception:
                pass

    background.add_task(_send)
    return {"status": "queued"}


@router.post("/admin/notify", response_model=dict, responses={
    200: {
        "description": "Notification sent to all admins",
        "content": {
            "application/json": {
                "example": {"status": "queued"}
            }
        }
    },
    401: {"description": "Unauthorized - admin authentication required"},
    500: {"description": "Internal server error"}
})
def notify_all_admins(
    req: SendNotificationRequest,
    background: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Send notification to all admin subscriptions."""
    payload = {
        "title": req.title,
        "body": req.body,
        "data": req.data or {},
        "icon": req.icon,
        "tag": req.event_id or req.tag,
    }
    
    def _send():
        try:
            result = send_to_all_admins(db, payload, event_id=req.event_id)
            logger.info("Admin broadcast completed: %s", result)
        except Exception as e:
            logger.error("Admin broadcast failed: %s", str(e))
    
    background.add_task(_send)
    return {"status": "queued"}


@router.post("/admin/notify/{admin_id}", response_model=dict, responses={
    200: {
        "description": "Notification sent to specific admin",
        "content": {
            "application/json": {
                "example": {"status": "queued"}
            }
        }
    },
    401: {"description": "Unauthorized - admin authentication required"},
    404: {"description": "Admin not found"},
    422: {"description": "Validation error - invalid admin ID"},
    500: {"description": "Internal server error"}
})
def notify_specific_admin(
    admin_id: int,
    req: SendNotificationRequest,
    background: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Send notification to a specific admin's subscriptions."""
    # Verify admin exists
    from app.models.admin import Admin as AdminModel
    admin = db.query(AdminModel).filter(AdminModel.id == admin_id).first()
    if not admin:
        raise HTTPException(status_code=404, detail=f"Admin with ID {admin_id} not found")
    
    payload = {
        "title": req.title,
        "body": req.body,
        "data": req.data or {},
        "icon": req.icon,
        "tag": req.event_id or req.tag,
    }
    
    def _send():
        try:
            result = send_to_admin_subscriptions(db, admin_id, payload, event_id=req.event_id)
            logger.info("Admin notification to admin_id=%s completed: %s", admin_id, result)
        except Exception as e:
            logger.error("Admin notification to admin_id=%s failed: %s", admin_id, str(e))
    
    background.add_task(_send)
    return {"status": "queued"}
