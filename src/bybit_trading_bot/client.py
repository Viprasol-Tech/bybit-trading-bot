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
from enum import Enum
from urllib.parse import urlencode

from bybit_trading_bot.auth import DEFAULT_RECV_WINDOW, auth_headers
from bybit_trading_bot.enums import Category, Interval, OrderType, Side, TimeInForce

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

    # -- High-level v5 endpoint builders ---------------------------------

    def get_kline(
        self,
        symbol: str,
        interval: Interval | str,
        *,
        category: Category | str = Category.SPOT,
        limit: int = 200,
        start: int | None = None,
        end: int | None = None,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Build a signed ``GET /v5/market/kline`` request.

        Args:
            symbol: Trading symbol, e.g. ``"BTCUSDT"``.
            interval: Candlestick interval (:class:`~.enums.Interval` or raw).
            category: Product category.
            limit: Number of candles (Bybit caps at 1000); must be 1..1000.
            start: Optional inclusive start time in milliseconds.
            end: Optional inclusive end time in milliseconds.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest`.

        Raises:
            ValueError: If ``limit`` is outside ``1..1000``.
        """
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        params: dict[str, object] = {
            "category": _value(category),
            "symbol": symbol,
            "interval": _value(interval),
            "limit": limit,
        }
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        return self.prepare_get("/v5/market/kline", params, timestamp=timestamp)

    def get_tickers(
        self,
        *,
        category: Category | str = Category.SPOT,
        symbol: str | None = None,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Build a signed ``GET /v5/market/tickers`` request.

        Args:
            category: Product category.
            symbol: Optional symbol filter; omitted means all symbols.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest`.
        """
        params: dict[str, object] = {"category": _value(category)}
        if symbol is not None:
            params["symbol"] = symbol
        return self.prepare_get("/v5/market/tickers", params, timestamp=timestamp)

    def get_positions(
        self,
        *,
        category: Category | str = Category.LINEAR,
        symbol: str | None = None,
        settle_coin: str | None = None,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Build a signed ``GET /v5/position/list`` request.

        Args:
            category: Product category (positions exist for derivatives).
            symbol: Optional symbol filter.
            settle_coin: Optional settle coin filter, e.g. ``"USDT"``.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest`.
        """
        params: dict[str, object] = {"category": _value(category)}
        if symbol is not None:
            params["symbol"] = symbol
        if settle_coin is not None:
            params["settleCoin"] = settle_coin
        return self.prepare_get("/v5/position/list", params, timestamp=timestamp)

    def get_wallet_balance(
        self,
        *,
        account_type: str = "UNIFIED",
        coin: str | None = None,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Build a signed ``GET /v5/account/wallet-balance`` request.

        Args:
            account_type: Account type, e.g. ``"UNIFIED"`` or ``"CONTRACT"``.
            coin: Optional coin filter, e.g. ``"USDT"``.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest`.
        """
        params: dict[str, object] = {"accountType": account_type}
        if coin is not None:
            params["coin"] = coin
        return self.prepare_get("/v5/account/wallet-balance", params, timestamp=timestamp)

    def place_order(
        self,
        symbol: str,
        side: Side | str,
        order_type: OrderType | str,
        qty: str | float,
        *,
        category: Category | str = Category.SPOT,
        price: str | float | None = None,
        time_in_force: TimeInForce | str | None = None,
        order_link_id: str | None = None,
        reduce_only: bool | None = None,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Build a signed ``POST /v5/order/create`` request.

        Args:
            symbol: Trading symbol, e.g. ``"BTCUSDT"``.
            side: Order side (:class:`~.enums.Side` or raw).
            order_type: Order type (:class:`~.enums.OrderType` or raw).
            qty: Order quantity (Bybit takes strings; numbers are stringified).
            category: Product category.
            price: Limit price; required for limit orders, ignored otherwise.
            time_in_force: Time-in-force policy.
            order_link_id: Optional client order id for idempotency.
            reduce_only: Optional reduce-only flag for derivatives.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest`.

        Raises:
            ValueError: If a limit order is missing a ``price``.
        """
        ot = _value(order_type)
        if ot == OrderType.LIMIT.value and price is None:
            raise ValueError("limit orders require a price")
        body: dict[str, object] = {
            "category": _value(category),
            "symbol": symbol,
            "side": _value(side),
            "orderType": ot,
            "qty": str(qty),
        }
        if price is not None:
            body["price"] = str(price)
        if time_in_force is not None:
            body["timeInForce"] = _value(time_in_force)
        if order_link_id is not None:
            body["orderLinkId"] = order_link_id
        if reduce_only is not None:
            body["reduceOnly"] = reduce_only
        return self.prepare_post("/v5/order/create", body, timestamp=timestamp)

    def cancel_order(
        self,
        symbol: str,
        *,
        category: Category | str = Category.SPOT,
        order_id: str | None = None,
        order_link_id: str | None = None,
        timestamp: int | None = None,
    ) -> PreparedRequest:
        """Build a signed ``POST /v5/order/cancel`` request.

        Exactly one of ``order_id`` or ``order_link_id`` must be supplied.

        Args:
            symbol: Trading symbol.
            category: Product category.
            order_id: Bybit-assigned order id.
            order_link_id: Client-assigned order id.
            timestamp: Override millisecond timestamp (mainly for testing).

        Returns:
            A signed :class:`PreparedRequest`.

        Raises:
            ValueError: If neither or both id forms are provided.
        """
        if (order_id is None) == (order_link_id is None):
            raise ValueError("provide exactly one of order_id or order_link_id")
        body: dict[str, object] = {"category": _value(category), "symbol": symbol}
        if order_id is not None:
            body["orderId"] = order_id
        if order_link_id is not None:
            body["orderLinkId"] = order_link_id
        return self.prepare_post("/v5/order/cancel", body, timestamp=timestamp)


def _value(member: object) -> str:
    """Return the wire string for an enum member or a raw string.

    Args:
        member: An :class:`~enum.Enum` instance or a plain string.

    Returns:
        The enum's ``value`` when given an enum, else the string itself.
    """
    if isinstance(member, Enum):
        return str(member.value)
    return str(member)
