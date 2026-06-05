"""Signed-request preparation for the Bybit v5 REST API.

``BybitClient`` builds fully-signed request descriptions (method, URL, headers,
body) without performing any network I/O. This keeps the signing logic testable
and lets you inspect exactly what would be sent before wiring in an HTTP
transport such as ``httpx`` or ``requests``.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlencode

from bybit_trading_bot.auth import DEFAULT_RECV_WINDOW, auth_headers

#: Bybit production REST base URL.
MAINNET_BASE_URL = "https://api.bybit.com"
#: Bybit testnet REST base URL.
TESTNET_BASE_URL = "https://api-testnet.bybit.com"


@dataclass(slots=True, frozen=True)
class PreparedRequest:
    """A fully-signed request ready to hand to an HTTP transport.

    Attributes:
        method: HTTP verb, ``"GET"`` or ``"POST"``.
        url: Absolute URL including any query string.
        headers: Request headers, including the signed ``X-BAPI-*`` set.
        body: JSON body for ``POST`` requests, or ``None`` for ``GET``.
    """

    method: str
    url: str
    headers: dict[str, str]
    body: str | None


class BybitClient:
    """Prepare signed Bybit v5 requests without sending them.

    Args:
        api_key: The public API key.
        api_secret: The API secret used to sign requests.
        base_url: REST base URL; defaults to mainnet.
        recv_window: Receive-window in milliseconds applied to every request.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        base_url: str = MAINNET_BASE_URL,
        recv_window: int = DEFAULT_RECV_WINDOW,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.recv_window = recv_window

    def prepare_get(
        self,
        path: str,
        params: Mapping[str, object] | None = None,
        *,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Prepare a signed ``GET`` request.

        The query string is URL-encoded and used both in the URL and as the
        signing payload, exactly as Bybit requires.

        Args:
            path: API path, e.g. ``"/v5/market/tickers"``.
            params: Query parameters; ``None`` or empty means no query string.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest` with ``body=None``.
        """
        query = urlencode(sorted((params or {}).items()))
        headers = auth_headers(
            self.api_key,
            self.api_secret,
            query,
            timestamp=timestamp,
            recv_window=self.recv_window,
        )
        url = f"{self.base_url}{path}"
        if query:
            url = f"{url}?{query}"
        return PreparedRequest(method="GET", url=url, headers=headers, body=None)

    def prepare_post(
        self,
        path: str,
        body: Mapping[str, object] | None = None,
        *,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Prepare a signed ``POST`` request.

        The body is serialized to compact JSON and used as the signing payload.

        Args:
            path: API path, e.g. ``"/v5/order/create"``.
            body: Request body; ``None`` is serialized as ``{}``.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest` with a JSON ``body``.
        """
        payload = json.dumps(body or {}, separators=(",", ":"), sort_keys=True)
        headers = auth_headers(
            self.api_key,
            self.api_secret,
            payload,
            timestamp=timestamp,
            recv_window=self.recv_window,
        )
        headers["Content-Type"] = "application/json"
        url = f"{self.base_url}{path}"
        return PreparedRequest(method="POST", url=url, headers=headers, body=payload)
