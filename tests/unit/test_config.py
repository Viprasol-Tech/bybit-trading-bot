from __future__ import annotations

import pytest
from pydantic import ValidationError

from bybit_trading_bot.client import MAINNET_BASE_URL, TESTNET_BASE_URL
from bybit_trading_bot.config import Settings


def test_defaults_target_mainnet() -> None:
    settings = Settings()
    assert settings.base_url == MAINNET_BASE_URL
    assert settings.recv_window == 5_000
    assert settings.default_category == "spot"
    assert settings.has_credentials is False


def test_testnet_flag_switches_base_url() -> None:
    assert Settings(testnet=True).base_url == TESTNET_BASE_URL


def test_has_credentials_requires_both() -> None:
    assert Settings(api_key="k").has_credentials is False
    assert Settings(api_secret="s").has_credentials is False
    assert Settings(api_key="k", api_secret="s").has_credentials is True


def test_invalid_category_rejected() -> None:
    with pytest.raises(ValueError):
        Settings(default_category="futures")


@pytest.mark.parametrize("recv", [0, 60_001])
def test_recv_window_bounds_enforced(recv: int) -> None:
    with pytest.raises(ValueError):
        Settings(recv_window=recv)


def test_settings_is_frozen() -> None:
    settings = Settings()
    with pytest.raises(ValidationError):
        settings.api_key = "mutated"  # type: ignore[misc]


def test_from_env_reads_all_keys() -> None:
    env = {
        "BYBIT_API_KEY": "abc",
        "BYBIT_API_SECRET": "xyz",
        "BYBIT_TESTNET": "true",
        "BYBIT_RECV_WINDOW": "8000",
        "BYBIT_DEFAULT_CATEGORY": "linear",
    }
    settings = Settings.from_env(env)
    assert settings.api_key == "abc"
    assert settings.api_secret == "xyz"
    assert settings.testnet is True
    assert settings.base_url == TESTNET_BASE_URL
    assert settings.recv_window == 8_000
    assert settings.default_category == "linear"
    assert settings.has_credentials is True


def test_from_env_defaults_when_empty() -> None:
    settings = Settings.from_env({})
    assert settings.api_key == ""
    assert settings.testnet is False
    assert settings.recv_window == 5_000


@pytest.mark.parametrize(
    "value,expected",
    [("1", True), ("YES", True), ("on", True), ("0", False), ("no", False), ("", False)],
)
def test_from_env_truthy_parsing(value: str, expected: bool) -> None:
    assert Settings.from_env({"BYBIT_TESTNET": value}).testnet is expected
