from pydantic import BaseModel, Field, conlist
from typing import Optional, Dict, Any, List


class PushSubscriptionKeys(BaseModel):
    p256dh: str = Field(..., min_length=1)
    auth: str = Field(..., min_length=1)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(..., min_length=1, max_length=512)
    keys: PushSubscriptionKeys
    user_agent: Optional[str] = Field(default=None, max_length=512)


class PushSubscriptionOut(BaseModel):
    id: int
    endpoint: str
    is_active: bool

    class Config:
        from_attributes = True


class SendNotificationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=128)
    body: str = Field(..., min_length=1, max_length=1024)
    data: Optional[Dict[str, Any]] = None
    icon: Optional[str] = None
    tag: Optional[str] = None
    event_id: Optional[str] = Field(default=None, max_length=128)
    ttl_seconds: Optional[int] = Field(
        default=None,
        ge=1,
        le=86400,
        description="Time-to-live in seconds for the push message (1..86400)"
    )


class TopicOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SubscriptionTopicsRequest(BaseModel):
    subscription_id: int = Field(..., gt=0)
    topic_ids: conlist(int, min_length=1)
