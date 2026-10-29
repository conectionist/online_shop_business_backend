"""Unit tests for the rate limiter's client key."""

import logging

import pytest
from starlette.requests import Request

from app.core import rate_limit


def _request(peer: str, *forwarded_for_lines: str) -> Request:
    headers = [(b"x-forwarded-for", line.encode()) for line in forwarded_for_lines]
    return Request({"type": "http", "client": (peer, 50000), "headers": headers})


@pytest.fixture(autouse=True)
def _fresh_warning_state(monkeypatch):
    monkeypatch.setattr(rate_limit, "_last_untrusted_proxy_warning", None)


def _warnings(caplog):
    return [record for record in caplog.records if "FORWARDED_ALLOW_IPS" in record.getMessage()]


def test_key_is_the_peer_address():
    assert rate_limit._client_ip_key(_request("198.51.100.7")) == "198.51.100.7"


def test_a_forwarded_for_header_does_not_change_the_key():
    # What a client sends itself; Uvicorn did not use it, so the peer is still the client.
    key_a = rate_limit._client_ip_key(_request("198.51.100.7", "203.0.113.1"))
    key_b = rate_limit._client_ip_key(_request("198.51.100.7", "203.0.113.2"))

    assert key_a == key_b == "198.51.100.7"


def test_no_warning_when_uvicorn_used_the_forwarded_address(caplog):
    # A trusted proxy: Uvicorn already replaced the peer with the forwarded client.
    with caplog.at_level(logging.WARNING, logger=rate_limit.__name__):
        rate_limit._client_ip_key(_request("203.0.113.9", "203.0.113.9, 10.0.0.2"))

    assert _warnings(caplog) == []


def test_no_warning_when_a_proxy_adds_its_own_header_line(caplog):
    # The client's line first, then the trusted proxy's, which Uvicorn reads.
    with caplog.at_level(logging.WARNING, logger=rate_limit.__name__):
        rate_limit._client_ip_key(_request("203.0.113.9", "198.51.100.1", "203.0.113.9"))

    assert _warnings(caplog) == []


def test_no_warning_for_an_empty_header(caplog):
    with caplog.at_level(logging.WARNING, logger=rate_limit.__name__):
        rate_limit._client_ip_key(_request("198.51.100.7", " , "))

    assert _warnings(caplog) == []


def test_warns_about_a_proxy_uvicorn_does_not_trust_at_most_hourly(caplog, monkeypatch):
    clock = iter([1000.0, 1000.0 + 60, 1000.0 + 60 * 60 + 1])
    monkeypatch.setattr(rate_limit, "monotonic", lambda: next(clock))

    with caplog.at_level(logging.WARNING, logger=rate_limit.__name__):
        rate_limit._client_ip_key(_request("172.18.0.1", "203.0.113.9"))
        rate_limit._client_ip_key(_request("172.18.0.1", "203.0.113.10"))
        rate_limit._client_ip_key(_request("172.18.0.1", "203.0.113.11"))

    assert len(_warnings(caplog)) == 2
