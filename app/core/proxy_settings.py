"""The reverse-proxy settings production needs for per-client rate limits.

Uvicorn reads USE_PROXY_HEADERS (through docker-entrypoint.sh) and FORWARDED_ALLOW_IPS,
but the order and login rate limits depend on them, so the app checks them too.
"""
import ipaddress
from typing import Optional

_FINDING_THE_ADDRESS = (
    "Set it to the address your reverse proxy connects from, as the API container sees it: "
    "the proxy container's IP, or, if the proxy runs on the host, the Docker network's "
    "gateway (docker network inspect <network> shows it). If you list the gateway, keep "
    "port 8000 reachable only through the proxy."
)


def production_proxy_settings_error(
    environment: str, use_proxy_headers: str, forwarded_allow_ips: str
) -> Optional[str]:
    """Why these settings would make every customer share one rate limit, or None.

    Production sits behind a TLS proxy, since its public URLs must be https. Unless Uvicorn
    trusts that proxy, every request has the proxy's IP.
    """
    if environment != "production":
        return None

    if use_proxy_headers.strip().lower() not in ("true", "1", "yes"):
        return (
            "Production requires USE_PROXY_HEADERS=true: without it every request has the "
            "reverse proxy's IP, and all customers share one order and login rate limit."
        )

    entries = [entry.strip() for entry in forwarded_allow_ips.split(",") if entry.strip()]
    if not entries:
        return "Production requires FORWARDED_ALLOW_IPS. " + _FINDING_THE_ADDRESS

    if "*" in entries:
        return (
            "FORWARDED_ALLOW_IPS must not be '*' in production: Uvicorn would then take the "
            "client's own X-Forwarded-For entry, so clients could choose their rate-limit key. "
            + _FINDING_THE_ADDRESS
        )

    networks = []
    for entry in entries:
        try:
            networks.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            return (
                f"FORWARDED_ALLOW_IPS has {entry!r}, which is not an IP address or network. "
                + _FINDING_THE_ADDRESS
            )

    # The default; inside the container the proxy never connects over loopback.
    if all(network.is_loopback for network in networks):
        return (
            f"FORWARDED_ALLOW_IPS={forwarded_allow_ips.strip()} only trusts loopback, which "
            "the reverse proxy never connects from. " + _FINDING_THE_ADDRESS
        )

    return None
