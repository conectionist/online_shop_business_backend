import os
import uuid
import re
import requests

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
