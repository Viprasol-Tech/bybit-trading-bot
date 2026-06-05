from __future__ import annotations

import hashlib
import hmac

from bybit_trading_bot.auth import auth_headers, prehash_string, sign


def test_prehash_string_order() -> None:
    assert prehash_string(1700000000000, "KEY", 5000, "payload") == "1700000000000KEY5000payload"


def test_sign_reproduces_known_hmac() -> None:
    api_secret = "topsecret"
    timestamp = 1700000000000
    api_key = "myapikey"
    recv_window = 5000
    payload = '{"symbol":"BTCUSDT"}'

    message = f"{timestamp}{api_key}{recv_window}{payload}"
    expected = hmac.new(
        api_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    got = sign(api_secret, timestamp, api_key, recv_window, payload)
    assert got == expected
    # A hex SHA256 digest is always 64 lowercase hex chars.
    assert len(got) == 64
    assert got == got.lower()


def test_sign_is_stable_for_fixed_inputs() -> None:
    # Locks the exact digest for a fixed input vector (regression guard).
    digest = sign("secret", 1700000000000, "key", 5000, "")
    expected = hmac.new(
        b"secret",
        b"1700000000000key5000",
        hashlib.sha256,
    ).hexdigest()
    assert digest == expected


def test_auth_headers_has_four_xbapi_keys() -> None:
    headers = auth_headers(
        "myapikey",
        "topsecret",
        '{"symbol":"BTCUSDT"}',
        timestamp=1700000000000,
        recv_window=5000,
    )
    assert set(headers) == {
        "X-BAPI-API-KEY",
        "X-BAPI-TIMESTAMP",
        "X-BAPI-RECV-WINDOW",
        "X-BAPI-SIGN",
    }
    assert headers["X-BAPI-API-KEY"] == "myapikey"
    assert headers["X-BAPI-TIMESTAMP"] == "1700000000000"
    assert headers["X-BAPI-RECV-WINDOW"] == "5000"
    assert headers["X-BAPI-SIGN"] == sign(
        "topsecret", 1700000000000, "myapikey", 5000, '{"symbol":"BTCUSDT"}'
    )


def test_auth_headers_signature_changes_with_payload() -> None:
    a = auth_headers("k", "s", "a", timestamp=1, recv_window=5000)
    b = auth_headers("k", "s", "b", timestamp=1, recv_window=5000)
    assert a["X-BAPI-SIGN"] != b["X-BAPI-SIGN"]
