"""Unit tests for the production check on the reverse-proxy settings."""

import pytest

from app.core.proxy_settings import production_proxy_settings_error


@pytest.mark.parametrize("environment", ["development", "test"])
def test_outside_production_anything_goes(environment):
    assert production_proxy_settings_error(environment, "false", "") is None
    assert production_proxy_settings_error(environment, "true", "*") is None


@pytest.mark.parametrize(
    "forwarded_allow_ips",
    ["172.18.0.1", "172.18.0.0/16", "127.0.0.1, 172.18.0.1", "10.0.0.5,fd00::1"],
)
def test_production_accepts_a_proxy_address(forwarded_allow_ips):
    assert production_proxy_settings_error("production", "true", forwarded_allow_ips) is None


@pytest.mark.parametrize("use_proxy_headers", ["TRUE", "1", "yes"])
def test_production_accepts_any_spelling_of_true(use_proxy_headers):
    assert production_proxy_settings_error("production", use_proxy_headers, "172.18.0.1") is None


@pytest.mark.parametrize(
    ("use_proxy_headers", "forwarded_allow_ips", "named"),
    [
        ("false", "172.18.0.1", "USE_PROXY_HEADERS"),
        ("true", "", "FORWARDED_ALLOW_IPS"),
        ("true", " , ", "FORWARDED_ALLOW_IPS"),
        ("true", "*", "'*'"),
        ("true", "172.18.0.1,*", "'*'"),
        ("true", "proxy.internal", "'proxy.internal'"),
        ("true", "127.0.0.1", "loopback"),
        ("true", "127.0.0.1,::1", "loopback"),
    ],
)
def test_production_refuses_settings_that_share_one_limit(use_proxy_headers, forwarded_allow_ips, named):
    error = production_proxy_settings_error("production", use_proxy_headers, forwarded_allow_ips)

    assert error is not None
    assert named in error
