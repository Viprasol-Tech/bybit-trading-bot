from __future__ import annotations

import json

import pytest

from bybit_trading_bot.client import TESTNET_BASE_URL, BybitClient
from bybit_trading_bot.enums import Category, Interval, OrderType, Side, TimeInForce

TS = 1700000000000


def _client() -> BybitClient:
    return BybitClient("key", "secret", base_url=TESTNET_BASE_URL, recv_window=5000)


def _body(req) -> dict:  # type: ignore[no-untyped-def]
    assert req.body is not None
    return json.loads(req.body)


def test_get_kline_builds_query() -> None:
    req = _client().get_kline("BTCUSDT", Interval.H1, limit=100, timestamp=TS)
    assert req.method == "GET"
    assert "/v5/market/kline" in req.url
    assert "interval=60" in req.url
    assert "limit=100" in req.url
    assert "symbol=BTCUSDT" in req.url
    assert "category=spot" in req.url


def test_get_kline_accepts_raw_interval_string() -> None:
    req = _client().get_kline("BTCUSDT", "15", timestamp=TS)
    assert "interval=15" in req.url


def test_get_kline_with_time_range() -> None:
    req = _client().get_kline("BTCUSDT", Interval.D1, start=1, end=2, timestamp=TS)
    assert "start=1" in req.url
    assert "end=2" in req.url


@pytest.mark.parametrize("limit", [0, 1001])
def test_get_kline_rejects_bad_limit(limit: int) -> None:
    with pytest.raises(ValueError):
        _client().get_kline("BTCUSDT", Interval.H1, limit=limit, timestamp=TS)


def test_get_tickers_all_symbols() -> None:
    req = _client().get_tickers(category=Category.LINEAR, timestamp=TS)
    assert "/v5/market/tickers" in req.url
    assert "category=linear" in req.url
    assert "symbol=" not in req.url


def test_get_tickers_single_symbol() -> None:
    req = _client().get_tickers(symbol="ETHUSDT", timestamp=TS)
    assert "symbol=ETHUSDT" in req.url


def test_get_positions_filters() -> None:
    req = _client().get_positions(symbol="BTCUSDT", settle_coin="USDT", timestamp=TS)
    assert "/v5/position/list" in req.url
    assert "category=linear" in req.url
    assert "symbol=BTCUSDT" in req.url
    assert "settleCoin=USDT" in req.url


def test_get_wallet_balance() -> None:
    req = _client().get_wallet_balance(coin="USDT", timestamp=TS)
    assert "/v5/account/wallet-balance" in req.url
    assert "accountType=UNIFIED" in req.url
    assert "coin=USDT" in req.url


def test_place_market_order_body() -> None:
    req = _client().place_order("BTCUSDT", Side.BUY, OrderType.MARKET, "0.001", timestamp=TS)
    body = _body(req)
    assert body["category"] == "spot"
    assert body["symbol"] == "BTCUSDT"
    assert body["side"] == "Buy"
    assert body["orderType"] == "Market"
    assert body["qty"] == "0.001"
    assert "price" not in body


def test_place_limit_order_includes_price_and_tif() -> None:
    req = _client().place_order(
        "BTCUSDT",
        Side.SELL,
        OrderType.LIMIT,
        0.5,
        price=31_000,
        time_in_force=TimeInForce.POST_ONLY,
        order_link_id="abc-1",
        reduce_only=True,
        timestamp=TS,
    )
    body = _body(req)
    assert body["side"] == "Sell"
    assert body["orderType"] == "Limit"
    assert body["price"] == "31000"
    assert body["qty"] == "0.5"
    assert body["timeInForce"] == "PostOnly"
    assert body["orderLinkId"] == "abc-1"
    assert body["reduceOnly"] is True


def test_place_limit_order_requires_price() -> None:
    with pytest.raises(ValueError):
        _client().place_order("BTCUSDT", Side.BUY, OrderType.LIMIT, "1", timestamp=TS)


def test_place_order_accepts_raw_strings() -> None:
    req = _client().place_order("BTCUSDT", "Buy", "Market", "1", timestamp=TS)
    assert _body(req)["side"] == "Buy"


def test_cancel_order_by_order_id() -> None:
    req = _client().cancel_order("BTCUSDT", order_id="oid-9", timestamp=TS)
    body = _body(req)
    assert "/v5/order/cancel" in req.url
    assert body["orderId"] == "oid-9"
    assert "orderLinkId" not in body


def test_cancel_order_by_link_id() -> None:
    req = _client().cancel_order("BTCUSDT", order_link_id="link-9", timestamp=TS)
    assert _body(req)["orderLinkId"] == "link-9"


def test_cancel_order_requires_exactly_one_id() -> None:
    with pytest.raises(ValueError):
        _client().cancel_order("BTCUSDT", timestamp=TS)
    with pytest.raises(ValueError):
        _client().cancel_order("BTCUSDT", order_id="a", order_link_id="b", timestamp=TS)


def test_endpoints_are_signed() -> None:
    req = _client().get_wallet_balance(timestamp=TS)
    assert len(req.headers["X-BAPI-SIGN"]) == 64
