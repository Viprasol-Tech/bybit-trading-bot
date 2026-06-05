from __future__ import annotations

import json
from urllib.parse import urlencode

from bybit_trading_bot.auth import sign
from bybit_trading_bot.client import (
    MAINNET_BASE_URL,
    TESTNET_BASE_URL,
    BybitClient,
)

TS = 1700000000000


def _client() -> BybitClient:
    return BybitClient("key", "secret", base_url=TESTNET_BASE_URL, recv_window=5000)


def test_prepare_get_signs_query_string() -> None:
    client = _client()
    req = client.prepare_get(
        "/v5/market/tickers",
        {"category": "spot", "symbol": "BTCUSDT"},
        timestamp=TS,
    )
    query = urlencode(sorted({"category": "spot", "symbol": "BTCUSDT"}.items()))
    assert req.method == "GET"
    assert req.url == f"{TESTNET_BASE_URL}/v5/market/tickers?{query}"
    assert req.body is None
    assert req.headers["X-BAPI-SIGN"] == sign("secret", TS, "key", 5000, query)


def test_prepare_get_without_params_has_no_query() -> None:
    client = _client()
    req = client.prepare_get("/v5/account/wallet-balance", timestamp=TS)
    assert req.url == f"{TESTNET_BASE_URL}/v5/account/wallet-balance"
    assert req.headers["X-BAPI-SIGN"] == sign("secret", TS, "key", 5000, "")


def test_prepare_post_signs_json_body() -> None:
    client = _client()
    body = {"symbol": "BTCUSDT", "side": "Buy", "qty": "0.001"}
    req = client.prepare_post("/v5/order/create", body, timestamp=TS)
    payload = json.dumps(body, separators=(",", ":"), sort_keys=True)
    assert req.method == "POST"
    assert req.body == payload
    assert req.headers["Content-Type"] == "application/json"
    assert req.headers["X-BAPI-SIGN"] == sign("secret", TS, "key", 5000, payload)


def test_prepare_post_empty_body_is_empty_object() -> None:
    client = _client()
    req = client.prepare_post("/v5/order/cancel-all", timestamp=TS)
    assert req.body == "{}"
    assert req.headers["X-BAPI-SIGN"] == sign("secret", TS, "key", 5000, "{}")


def test_default_base_url_is_mainnet() -> None:
    client = BybitClient("k", "s")
    assert client.base_url == MAINNET_BASE_URL
