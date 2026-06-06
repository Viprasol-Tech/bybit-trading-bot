"""Typed configuration for Bybit Trading Bot.

:class:`Settings` is a small, validated configuration model built on Pydantic.
It captures the API credentials, network selection, and request tuning the bot
needs, and can hydrate itself from environment variables (``BYBIT_*``) so that
secrets never have to be hard-coded.

Part of Bybit Trading Bot by Viprasol Tech Private Limited (https://viprasol.com).
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, field_validator

from bybit_trading_bot.client import MAINNET_BASE_URL, TESTNET_BASE_URL

#: Environment-variable prefix used by :meth:`Settings.from_env`.
ENV_PREFIX = "BYBIT_"


class Settings(BaseModel):
    """Validated runtime configuration for the bot.

    Attributes:
        api_key: The public Bybit API key. May be empty for demo/paper flows.
        api_secret: The Bybit API secret. May be empty for demo/paper flows.
        testnet: When ``True``, target the Bybit testnet instead of mainnet.
        recv_window: Receive-window in milliseconds applied to every request.
        default_category: Default product category (``spot``/``linear``/...).
    """

    model_config = {"frozen": True}

    api_key: str = ""
    api_secret: str = ""
    testnet: bool = False
    recv_window: int = Field(default=5_000, ge=1, le=60_000)
    default_category: str = "spot"

    @field_validator("default_category")
    @classmethod
    def _check_category(cls, value: str) -> str:
        """Validate that the category is one Bybit v5 recognises."""
        allowed = {"spot", "linear", "inverse", "option"}
        if value not in allowed:
            raise ValueError(f"default_category must be one of {sorted(allowed)}")
        return value

    @property
    def base_url(self) -> str:
        """Return the REST base URL implied by :attr:`testnet`."""
        return TESTNET_BASE_URL if self.testnet else MAINNET_BASE_URL

    @property
    def has_credentials(self) -> bool:
        """Return ``True`` when both an API key and secret are present."""
        return bool(self.api_key) and bool(self.api_secret)

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        """Build :class:`Settings` from ``BYBIT_*`` environment variables.

        Recognised keys: ``BYBIT_API_KEY``, ``BYBIT_API_SECRET``,
        ``BYBIT_TESTNET`` (truthy: ``1/true/yes/on``), ``BYBIT_RECV_WINDOW``,
        and ``BYBIT_DEFAULT_CATEGORY``. Missing keys fall back to defaults.

        Args:
            environ: Mapping to read from; defaults to :data:`os.environ`.

        Returns:
            A validated :class:`Settings` instance.
        """
        env = os.environ if environ is None else environ
        recv_raw = env.get(f"{ENV_PREFIX}RECV_WINDOW")
        return cls(
            api_key=env.get(f"{ENV_PREFIX}API_KEY", ""),
            api_secret=env.get(f"{ENV_PREFIX}API_SECRET", ""),
            testnet=_truthy(env.get(f"{ENV_PREFIX}TESTNET")),
            recv_window=int(recv_raw) if recv_raw else 5_000,
            default_category=env.get(f"{ENV_PREFIX}DEFAULT_CATEGORY", "spot"),
        )


def _truthy(value: str | None) -> bool:
    """Interpret a string environment value as a boolean.

    Args:
        value: The raw string (or ``None``).

    Returns:
        ``True`` for ``1``, ``true``, ``yes`` or ``on`` (case-insensitive).
    """
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}
