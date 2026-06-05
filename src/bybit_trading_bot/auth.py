"""Bybit v5 request signing (HMAC-SHA256).

Bybit's v5 API authenticates each request by signing the concatenation of
``timestamp + api_key + recv_window + payload`` with the account's API secret
using HMAC-SHA256, encoded as a lowercase hex digest. The signature and its
inputs travel in the ``X-BAPI-*`` request headers.

For ``GET`` requests the payload is the URL-encoded query string; for ``POST``
requests it is the raw JSON body. See ``client`` for how the payload is built.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import hashlib
import hmac
import time

#: Default ``recv_window`` (milliseconds) Bybit allows between client timestamp
#: and server receipt before the request is rejected as stale.
DEFAULT_RECV_WINDOW = 5_000


def now_ms() -> int:
    """Return the current UNIX time in integer milliseconds.

    Bybit expects ``X-BAPI-TIMESTAMP`` as a millisecond epoch.

    Returns:
        The current time in milliseconds since the UNIX epoch.
    """
    return int(time.time() * 1000)


def prehash_string(
    timestamp: int | str,
    api_key: str,
    recv_window: int | str,
    payload: str,
) -> str:
    """Build the exact string Bybit signs for a v5 request.

    The order is fixed: ``timestamp + api_key + recv_window + payload``,
    concatenated with no separators.

    Args:
        timestamp: Millisecond epoch sent as ``X-BAPI-TIMESTAMP``.
        api_key: The public API key.
        recv_window: Receive-window in milliseconds.
        payload: Query string (GET) or JSON body (POST); ``""`` if none.

    Returns:
        The concatenated pre-hash string.
    """
    return f"{timestamp}{api_key}{recv_window}{payload}"


def sign(
    api_secret: str,
    timestamp: int | str,
    api_key: str,
    recv_window: int | str,
    payload: str,
) -> str:
    """Sign a Bybit v5 request and return the lowercase hex signature.

    Args:
        api_secret: The API secret used as the HMAC key.
        timestamp: Millisecond epoch sent as ``X-BAPI-TIMESTAMP``.
        api_key: The public API key.
        recv_window: Receive-window in milliseconds.
        payload: Query string (GET) or JSON body (POST); ``""`` if none.

    Returns:
        The HMAC-SHA256 signature as a lowercase hex string.
    """
    message = prehash_string(timestamp, api_key, recv_window, payload)
    return hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def auth_headers(
    api_key: str,
    api_secret: str,
    payload: str,
    *,
    timestamp: int | None = None,
    recv_window: int = DEFAULT_RECV_WINDOW,
) -> dict[str, str]:
    """Build the signed ``X-BAPI-*`` header set for a Bybit v5 request.

    Args:
        api_key: The public API key.
        api_secret: The API secret used to sign the request.
        payload: Query string (GET) or JSON body (POST); ``""`` if none.
        timestamp: Millisecond epoch; defaults to ``now_ms()`` when ``None``.
        recv_window: Receive-window in milliseconds.

    Returns:
        A dict with exactly four keys: ``X-BAPI-API-KEY``,
        ``X-BAPI-TIMESTAMP``, ``X-BAPI-RECV-WINDOW`` and ``X-BAPI-SIGN``.
    """
    ts = now_ms() if timestamp is None else timestamp
    signature = sign(api_secret, ts, api_key, recv_window, payload)
    return {
        "X-BAPI-API-KEY": api_key,
        "X-BAPI-TIMESTAMP": str(ts),
        "X-BAPI-RECV-WINDOW": str(recv_window),
        "X-BAPI-SIGN": signature,
    }
