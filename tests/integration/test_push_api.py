import os
import uuid
import re
import requests
from .test_auth_utils import auth_utils

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
V1 = f"{API_BASE_URL}/api/v1"


def _unique_endpoint() -> str:
    # Generate a pseudo endpoint URL to act as a unique key
    return f"https://example.pushservice/sub/{uuid.uuid4()}"


def test_public_key_returns_configured_value():
    resp = requests.get(f"{V1}/push/public-key")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "publicKey" in data
    public_key = data["publicKey"]
    assert isinstance(public_key, str) and len(public_key) > 20
    # Basic URL-safe base64 check (A-Z a-z 0-9 - _)
    assert re.fullmatch(r"[A-Za-z0-9_-]+", public_key) is not None


def test_subscribe_then_resubscribe_updates_same_record():
    endpoint = _unique_endpoint()

    # Initial subscribe
    resp1 = requests.post(
        f"{V1}/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "k1", "auth": "a1"},
            "user_agent": "pytest",
        },
    )
    assert resp1.status_code == 201, resp1.text
    data1 = resp1.json()
    assert data1["endpoint"] == endpoint
    assert data1["is_active"] is True
    assert "id" in data1

    # Resubscribe with new keys; should upsert same row (id stable)
    resp2 = requests.post(
        f"{V1}/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "k2", "auth": "a2"},
            "user_agent": "pytest-2",
        },
    )
    assert resp2.status_code == 201, resp2.text
    data2 = resp2.json()
    assert data2["endpoint"] == endpoint
    assert data2["is_active"] is True
    assert data2["id"] == data1["id"], "Upsert must preserve the same subscription record"


def test_unsubscribe_deactivates():
    endpoint = _unique_endpoint()

    # Ensure subscribed first
    resp1 = requests.post(
        f"{V1}/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "k3", "auth": "a3"},
            "user_agent": "pytest",
        },
    )
    assert resp1.status_code == 201, resp1.text

    # Unsubscribe (deactivate)
    resp2 = requests.delete(f"{V1}/push/subscribe", params={"endpoint": endpoint})
    assert resp2.status_code == 200, resp2.text
    assert resp2.json().get("status") in ("deactivated", "not_found")

    # Re-subscribe activates again (sanity)
    resp3 = requests.post(
        f"{V1}/push/subscribe",
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "k4", "auth": "a4"},
            "user_agent": "pytest-3",
        },
    )
    assert resp3.status_code == 201, resp3.text


def test_admin_topics_aggregate_and_logout_behavior():
    # Login as admin
    assert auth_utils.login() is True
    headers = auth_utils.get_auth_headers()

    # Initially, expect empty list of admin topics
    r0 = requests.get(f"{V1}/push/admin/topics", headers=headers)
    assert r0.status_code == 200, r0.text
    assert isinstance(r0.json(), list)
    initial_topics = {t["name"] for t in r0.json()}

    # Create a browser subscription for this admin
    endpoint = _unique_endpoint()
    r1 = requests.post(
        f"{V1}/push/admin/subscribe",
        headers=headers,
        json={
            "endpoint": endpoint,
            "keys": {"p256dh": "k-sub", "auth": "a-sub"},
            "user_agent": "pytest-admin-topics",
        },
    )
    assert r1.status_code == 201, r1.text
    sub_id = r1.json()["id"]

    # Get available topics
    r_topics = requests.get(f"{V1}/push/topics", headers=headers)
    assert r_topics.status_code == 200, r_topics.text
    all_topics = r_topics.json()
    assert len(all_topics) >= 2

    # Pick a couple of topic IDs to subscribe (e.g., admin_login, list_published)
    topic_ids = [t["id"] for t in all_topics if t["name"] in ("admin_login", "list_published")]
    assert len(topic_ids) >= 1

    # Subscribe this subscription to those topics
    r_sub = requests.post(
        f"{V1}/push/topics/subscribe",
        headers=headers,
        json={"subscription_id": sub_id, "topic_ids": topic_ids},
    )
    assert r_sub.status_code == 200, r_sub.text

    # Now the admin topics endpoint should include those topic names
    r2 = requests.get(f"{V1}/push/admin/topics", headers=headers)
    assert r2.status_code == 200, r2.text
    names = {t["name"] for t in r2.json()}
    for tname in ("admin_login", "list_published"):
        if any(x["name"] == tname for x in all_topics):
            assert tname in names

    # Deactivate the subscription to simulate logout
    r3 = requests.delete(f"{V1}/push/subscribe", params={"endpoint": endpoint}, headers=headers)
    assert r3.status_code == 200, r3.text

    # Admin topics should now drop these topics (no active subs remain)
    r4 = requests.get(f"{V1}/push/admin/topics", headers=headers)
    assert r4.status_code == 200, r4.text
    names_after = {t["name"] for t in r4.json()}
    for tname in ("admin_login", "list_published"):
        if any(x["name"] == tname for x in all_topics):
            assert tname not in names_after
